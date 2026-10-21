"""
Deleting a competition, in three parts:
    CompetitionDeletionCollector finds what belongs to a competition and what can be deleted with it,
    CompetitionDeletionPreview turns that into the details shown in the delete dialog,
    CompetitionDeleter deletes the records and queues the deletion of their files.
"""
import os

from django.db import transaction
from django.db.models import Q

from competitions.models import Phase, Submission, SubmissionDetails
from competitions.tasks import delete_storage_files
from datasets.models import Data
from forums.models import Thread, Post
from leaderboards.models import Leaderboard, SubmissionScore
from profiles.models import CustomGroup
from tasks.models import Task, Solution

TASK_DATASET_FIELDS = ['ingestion_program', 'scoring_program', 'input_data', 'reference_data']
PHASE_DATASET_FIELDS = ['public_data', 'starting_kit']
SUBMISSION_FILE_FIELDS = ['prediction_result', 'scoring_result', 'detailed_result']


def _ids(records):
    """
    Returns the ids of `records` as a list, each id once.

    Why: a Django query (queryset) is not run when it is written, but every time it is used. If we kept the
    query "submissions of this competition" and used it after deleting the competition, it would find
    nothing. So we run it right away and keep the ids, which we can still use after the delete.
    Some queries return the same record more than once (e.g. a task used in two phases of the
    competition shows up once per phase), so duplicates are removed.

    Arguments:
        records: the query to get the ids from (e.g. the tasks of the competition)

    Example: the competition has 2 phases that both use task 4, and a phase that uses task 7
        -> _ids(records=Task.objects.filter(phases__competition=competition)) -> [4, 7]
    """
    return list(records.values_list('id', flat=True).distinct())


def _referenced_ids(records, fields):
    """
    Returns the ids of the datasets that `records` use in `fields`, each id once.

    Why: tasks, phases and solutions point to their datasets through fields:
        a task through 4 fields (ingestion program, scoring program, input data, reference data),
        a phase through 2 (public data, starting kit),
        a solution through 1 (data).
    To delete those datasets we first need their ids. This collects them from all the given fields of all
    the given records at once. Empty fields are skipped, and a dataset used several times is returned once.

    Arguments:
        records: the tasks, phases or solutions to read the datasets of
        fields: the dataset fields to read (e.g. TASK_DATASET_FIELDS)

    Example: task T1 uses dataset 10 as ingestion program and 11 as scoring program,
    task T2 uses dataset 10 as ingestion program and has no scoring program
        -> _referenced_ids(records=[T1, T2], fields=['ingestion_program', 'scoring_program']) -> [10, 11]
    """
    ids = set()
    for field in fields:
        # Reads only the dataset id stored on each record (the `<field>_id` column), not the dataset itself
        ids.update(records.values_list(f'{field}_id', flat=True))
    # Empty fields give None
    ids.discard(None)
    return sorted(ids)


def _unused_ids(data_ids, kept_records, fields):
    """
    Returns the datasets from `data_ids` that none of `kept_records` use, i.e. the ones safe to delete.

    Why: a dataset (e.g. a scoring program) can be shared by several tasks. When we delete some tasks,
    we would like to delete their datasets too, but a task we keep may still use one of them, and it
    would lose it. So the datasets still used by a kept task are removed from the list.

    Arguments:
        data_ids: the datasets we would like to delete
        kept_records: the records that are not deleted (e.g. the tasks we keep)
        fields: the dataset fields of those records (e.g. TASK_DATASET_FIELDS)

    Example: we would like to delete datasets 10 and 11, and a task we keep uses 11 as its scoring program
        -> _unused_ids(data_ids=[10, 11], kept_records=kept_tasks, fields=TASK_DATASET_FIELDS) -> [10]
    """
    # Only look at the kept records that use one of `data_ids` in any of the fields
    uses_one_of_data_ids = Q()
    for field in fields:
        uses_one_of_data_ids |= Q(**{f'{field}__in': data_ids})
    # Datasets from `data_ids` that those kept records use
    used_data_ids = set(_referenced_ids(records=kept_records.filter(uses_one_of_data_ids), fields=fields))
    return [data_id for data_id in data_ids if data_id not in used_data_ids]


def _total_size(sizes):
    """
    Returns the total of the file sizes in bytes, shown in the delete dialog.

    Why: the size of a file is stored in the database when the file is saved, but it is not always known:
    it is empty (None) when it was never computed, and -1 when the file could not be read
    (see Data.save and SubmissionDetails.save). Those sizes are skipped, so the total only adds real sizes.

    Arguments:
        sizes: the stored file sizes, as read from the database

    Example: _total_size(sizes=[100, None, -1, 50]) -> 150.0
    """
    return sum(float(size) for size in sizes if size and size > 0)


class CompetitionDeletionCollector:
    """
    Finds everything that belongs to a competition and can be deleted with it, as lists of ids.

    Always deleted with the competition (collected here):
        submission_ids        submissions of all phases, parents and children
        score_ids             leaderboard scores of those submissions
        submission_data_ids   submission zips, including zips uploaded through the submit form
                              whose submission was never created
        leaderboard_ids       leaderboards of the phases (their columns are deleted with them)
        group_ids             participant groups (their memberships are deleted with them)
        bundle_data_ids       the competition bundle the competition was created from
        dump_data_ids         competition dump zips
    Deletable, deleted only when chosen (collected here):
        deletable_task_ids            tasks not used by another competition
        deletable_solution_ids        solutions whose tasks are all in deletable_task_ids
        deletable_solution_data_ids   zips of those solutions
        deletable_task_data_ids       datasets of those tasks (ingestion program, scoring program, input data,
                                      reference data) that no kept task uses
        deletable_phase_data_ids      phase datasets (public data, starting kits) not used by
                                      another competition's phase
    Also collected, to list everything in the preview:
        all_task_ids          all tasks of the competition, including the ones used by another competition
        all_phase_data_ids    all phase datasets of the competition

    Not collected, the database deletes them with the competition:
        phases and their task links, pages, participants, whitelist emails, forum with its threads and posts,
        submission details (logs), the bundle upload status and the dump records.
    Files (logo, submission results and logs, dataset zips) are listed by CompetitionDeleter.files().
    """

    def __init__(self, competition):
        self.competition = competition
        self._collect_submissions()
        self._collect_competition_data()
        self._collect_tasks()
        self._collect_phase_datasets()

    def _collect_submissions(self):
        """Collects the submissions of all phases (parents and children), their scores and their zips"""
        submissions = Submission.objects.filter(phase__competition=self.competition)
        self.submission_ids = _ids(submissions)
        self.score_ids = _ids(SubmissionScore.objects.filter(submissions__in=submissions))
        # Zips of the submissions, plus zips uploaded through the competition's submit form whose
        # submission was never created (the database deletes those with the competition)
        self.submission_data_ids = _ids(
            Data.objects.filter(Q(submission__in=submissions) | Q(competition=self.competition))
        )

    def _collect_competition_data(self):
        """Collects the leaderboards, participant groups, bundle and dumps of the competition"""
        competition = self.competition
        # Leaderboards of the phases; their columns are deleted with them
        self.leaderboard_ids = _ids(Leaderboard.objects.filter(phases__competition=competition))
        self.group_ids = _ids(competition.participant_groups.all())
        # Bundle the competition was created from, through its upload status (CompetitionCreationTaskStatus)
        self.bundle_data_ids = _ids(Data.objects.filter(competition_bundles__resulting_competition=competition))
        self.dump_data_ids = _ids(Data.objects.filter(competition_dump_file__competition=competition))

    def _collect_tasks(self):
        """
        Collects all tasks of the competition, and the deletable ones: the tasks not used by another
        competition, with their solutions and datasets
        """
        competition_tasks = Task.objects.filter(phases__competition=self.competition)
        other_competitions_phases = Phase.objects.exclude(competition=self.competition)

        self.all_task_ids = _ids(competition_tasks)
        self.deletable_task_ids = _ids(competition_tasks.exclude(phases__in=other_competitions_phases))
        # Every task in the database that is not deleted
        kept_tasks = Task.objects.exclude(id__in=self.deletable_task_ids)

        # A solution can be linked to several tasks: it is deletable only when all of its tasks are
        self.deletable_solution_ids = _ids(
            Solution.objects.filter(tasks__in=self.deletable_task_ids).exclude(tasks__in=kept_tasks)
        )
        self.deletable_solution_data_ids = _referenced_ids(
            records=Solution.objects.filter(id__in=self.deletable_solution_ids), fields=['data'],
        )

        # A dataset can be used by several tasks: it is deletable only when no kept task uses it
        task_data_ids = _referenced_ids(
            records=Task.objects.filter(id__in=self.deletable_task_ids), fields=TASK_DATASET_FIELDS,
        )
        self.deletable_task_data_ids = _unused_ids(
            data_ids=task_data_ids, kept_records=kept_tasks, fields=TASK_DATASET_FIELDS,
        )

    def _collect_phase_datasets(self):
        """
        Collects all phase datasets (public data and starting kits) of the competition, and the deletable ones:
        the datasets not used by a phase of another competition
        """
        competition_phases = Phase.objects.filter(competition=self.competition)
        other_competitions_phases = Phase.objects.exclude(competition=self.competition)
        self.all_phase_data_ids = _referenced_ids(records=competition_phases, fields=PHASE_DATASET_FIELDS)
        self.deletable_phase_data_ids = _unused_ids(
            data_ids=self.all_phase_data_ids, kept_records=other_competitions_phases, fields=PHASE_DATASET_FIELDS,
        )


class CompetitionDeletionPreview:
    """
    Builds the details shown in the delete dialog: what is always deleted, and every task and phase dataset
    with `can_delete` telling whether its checkbox would delete it
    """

    def __init__(self, collector):
        self.collector = collector

    def to_dict(self):
        """Returns the preview as a dict, sent as JSON to the delete dialog"""
        competition = self.collector.competition
        return {
            'auto_delete': {
                'submissions': self._submissions(),
                'leaderboards': [
                    {'title': leaderboard.title, 'columns': list(leaderboard.columns.values_list('title', flat=True))}
                    for leaderboard in Leaderboard.objects.filter(id__in=self.collector.leaderboard_ids)
                ],
                'phases': list(competition.phases.order_by('index').values_list('name', flat=True)),
                'pages': list(competition.pages.order_by('index').values_list('title', flat=True)),
                'logo': [os.path.basename(f.name) for f in (competition.logo, competition.logo_icon) if f],
                'bundle': self._datasets(self.collector.bundle_data_ids),
                'dumps': self._datasets(self.collector.dump_data_ids),
                'participants_count': competition.participants.count(),
                'participant_groups': [
                    {'name': group.name, 'members_count': group.user_set.count()}
                    for group in CustomGroup.objects.filter(id__in=self.collector.group_ids).order_by('name')
                ],
                'forum_threads_count': Thread.objects.filter(forum__competition=competition).count(),
                'forum_posts_count': Post.objects.filter(thread__forum__competition=competition).count(),
            },
            'tasks': self._tasks(),
            'phase_datasets': [
                {**self._dataset(data), 'can_delete': data.id in self.collector.deletable_phase_data_ids}
                for data in Data.objects.filter(id__in=self.collector.all_phase_data_ids).order_by('type')
            ],
        }

    def _submissions(self):
        """Returns the submission counts, and the number and total size of their files"""
        submissions = Submission.objects.filter(id__in=self.collector.submission_ids)
        details = SubmissionDetails.objects.filter(submission__in=self.collector.submission_ids)
        zips = Data.objects.filter(id__in=self.collector.submission_data_ids)
        # Names of all submission files (results, logs, zips), to count the files; empty names are not counted
        file_names = (
            [name for field in SUBMISSION_FILE_FIELDS for name in submissions.values_list(field, flat=True)] +
            list(details.values_list('data_file', flat=True)) +
            list(zips.values_list('data_file', flat=True))
        )
        # Their sizes, as stored in the database when each file was saved, to show the total size
        file_sizes = (
            [size for field in SUBMISSION_FILE_FIELDS for size in submissions.values_list(f'{field}_file_size', flat=True)] +
            list(details.values_list('file_size', flat=True)) +
            list(zips.values_list('file_size', flat=True))
        )
        return {
            # Child submissions are the runs created for each task of a multi-task phase
            'parent_count': submissions.filter(parent__isnull=True).count(),
            'child_count': submissions.filter(parent__isnull=False).count(),
            'file_count': len([name for name in file_names if name]),
            'total_size': _total_size(file_sizes),
        }

    def _tasks(self):
        """Returns every task of the competition with its datasets and solutions, and whether each can be deleted"""
        tasks = []
        for task in Task.objects.filter(id__in=self.collector.all_task_ids).order_by('name'):
            task_data_ids = _referenced_ids(records=Task.objects.filter(id=task.id), fields=TASK_DATASET_FIELDS)
            tasks.append({
                'name': task.name,
                'can_delete': task.id in self.collector.deletable_task_ids,
                'datasets': [
                    {**self._dataset(data), 'can_delete': data.id in self.collector.deletable_task_data_ids}
                    for data in Data.objects.filter(id__in=task_data_ids).order_by('type')
                ],
                'solutions': [
                    {
                        'name': solution.name,
                        'can_delete': solution.id in self.collector.deletable_solution_ids,
                        'dataset': self._dataset(solution.data) if solution.data else None,
                    }
                    for solution in task.solutions.select_related('data').order_by('name')
                ],
            })
        return tasks

    def _datasets(self, data_ids):
        """Returns the name, type, file name and size of each dataset in `data_ids`"""
        return [self._dataset(data) for data in Data.objects.filter(id__in=data_ids)]

    @staticmethod
    def _dataset(data):
        """Returns the name, type, file name and size of a dataset"""
        return {
            'name': data.name,
            'type': data.get_type_display(),
            'file_name': os.path.basename(data.data_file.name) if data.data_file else None,
            'file_size': _total_size([data.file_size]),
        }


class CompetitionDeleter:
    """
    Deletes a competition with what the collector found, records and files.

    Always deleted:
        submissions (parents and children) with their scores, prediction, scoring and detailed results,
        logs and submission zips, leaderboards with their columns, the competition bundle, dumps, the logo,
        phases, pages, participants, participant groups and forum
    Deleted when `delete_tasks` is True:
        the deletable tasks, with their solutions and datasets
    Deleted when `delete_phase_datasets` is True:
        the deletable phase datasets (public data and starting kits)

    Records are deleted in one transaction; their files are then deleted from storage by a celery task.
    """

    def __init__(self, collector, delete_tasks=False, delete_phase_datasets=False):
        self.collector = collector
        self.competition = collector.competition
        # What to delete from the deletable tasks and phase datasets, depending on the options
        self.task_ids = collector.deletable_task_ids if delete_tasks else []
        self.solution_ids = collector.deletable_solution_ids if delete_tasks else []
        self.solution_data_ids = collector.deletable_solution_data_ids if delete_tasks else []
        self.task_data_ids = collector.deletable_task_data_ids if delete_tasks else []
        self.phase_data_ids = collector.deletable_phase_data_ids if delete_phase_datasets else []

    @property
    def data_ids(self):
        """Ids of all datasets to delete"""
        return sorted(set(
            self.collector.submission_data_ids + self.collector.bundle_data_ids + self.collector.dump_data_ids +
            self.solution_data_ids + self.task_data_ids + self.phase_data_ids
        ))

    def files(self):
        """
        Returns the files to delete from storage, grouped by type: {type: [[model label, field name, file name]]}.
        The model and field are used to find the storage the file is in. Types without files are left out.
        """
        submissions = Submission.objects.filter(id__in=self.collector.submission_ids)
        details = SubmissionDetails.objects.filter(submission__in=self.collector.submission_ids)
        files = {
            'logo files': (
                self._file_entries('competitions.Competition', 'logo', [self.competition.logo.name]) +
                self._file_entries('competitions.Competition', 'logo_icon', [self.competition.logo_icon.name])
            ),
            'submission zips': self._data_file_entries(self.collector.submission_data_ids),
            'submission result files': [
                entry for field in SUBMISSION_FILE_FIELDS
                for entry in self._file_entries('competitions.Submission', field, submissions.values_list(field, flat=True))
            ],
            'submission log files': self._file_entries(
                'competitions.SubmissionDetails', 'data_file', details.values_list('data_file', flat=True)
            ),
            'competition bundles': self._data_file_entries(self.collector.bundle_data_ids),
            'competition dumps': self._data_file_entries(self.collector.dump_data_ids),
            'task datasets': self._data_file_entries(self.task_data_ids),
            'solution datasets': self._data_file_entries(self.solution_data_ids),
            'phase datasets': self._data_file_entries(self.phase_data_ids),
        }
        return {file_type: entries for file_type, entries in files.items() if entries}

    @staticmethod
    def _file_entries(model_label, field_name, file_names):
        """Returns [model label, field name, file name] for each non-empty file name"""
        return [[model_label, field_name, name] for name in file_names if name]

    def _data_file_entries(self, data_ids):
        """Returns the file entries of the datasets in `data_ids`"""
        file_names = Data.objects.filter(id__in=data_ids).values_list('data_file', flat=True)
        return self._file_entries('datasets.Data', 'data_file', file_names)

    def delete(self):
        """Deletes the records in one transaction, then queues the deletion of their files"""
        # Files and competition details are read before the records they come from are deleted
        files = self.files()
        competition_id = self.competition.id
        competition_title = self.competition.title
        with transaction.atomic():
            SubmissionScore.objects.filter(id__in=self.collector.score_ids).delete()
            # Deleting datasets also deletes their dumps and solutions
            Data.objects.filter(id__in=self.data_ids).delete()
            Solution.objects.filter(id__in=self.solution_ids).delete()
            # Deletes phases, submissions, pages, participants and forum with it
            self.competition.delete()
            # Also deletes the parent auth group and its memberships; user accounts are kept
            CustomGroup.objects.filter(id__in=self.collector.group_ids).delete()
            # Leaderboards and tasks are deleted after the phases that point to them
            Leaderboard.objects.filter(id__in=self.collector.leaderboard_ids).delete()
            Task.objects.filter(id__in=self.task_ids).delete()
            # robust=True: if the task cannot be queued, the error is logged and the delete still succeeds;
            # the files left behind are then found by the orphan files cleanup
            transaction.on_commit(
                lambda: delete_storage_files.delay(
                    competition_id=competition_id,
                    competition_title=competition_title,
                    files=files,
                ),
                robust=True,
            )
