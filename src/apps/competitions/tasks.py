import base64
import datetime
import json
import logging
import os
import re

import oyaml as yaml
import shutil
import zipfile

from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db.models import Subquery, OuterRef, Count, Case, When, Value, F
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from celery_config import app
from dateutil import parser
from django.core.files import File
from django.utils.timezone import now

from tempfile import TemporaryDirectory

from api.serializers.competitions import CompetitionSerializer
from api.serializers.tasks import TaskSerializer, SolutionSerializer
from competitions.models import Submission, CompetitionCreationTaskStatus, SubmissionDetails, Competition, \
    CompetitionDump, Phase
from competitions.unpackers.utils import CompetitionUnpackingException
from competitions.unpackers.v1 import V15Unpacker
from competitions.unpackers.v2 import V2Unpacker
from datasets.models import Data
from tasks.models import Task, Solution
from utils.data import make_url_sassy

logger = logging.getLogger()

# TODO: Double check fields; computation, computation_indexes, etc will be implemented in the future
COMPETITION_FIELDS = [
    "title"
]

TASK_FIELDS = [
    'name',
    'description',
    'key',
    'is_public',
]
SOLUTION_FIELDS = [
    'name',
    'description',
    'tasks',
    'key',
]

PHASE_FIELDS = [
    'index',
    'name',
    'description',
    'start',
    'end',
    'max_submissions_per_day',
    'max_submissions_per_person',
    'execution_time_limit',
]
PHASE_FILES = [
    "input_data",
    "reference_data",
    "scoring_program",
    "ingestion_program",
    "public_data",
    "starting_kit",
]
PAGE_FIELDS = [
    "title"
]
LEADERBOARD_FIELDS = [
    'title',
    'key',

    # For later
    # 'force_submission_to_leaderboard',
    # 'force_best_submission_to_leaderboard',
    # 'disallow_leaderboard_modifying',
]

COLUMN_FIELDS = [
    'title',
    'key',
    'index',
    'sorting',
    'computation',
    'computation_indexes',
    'decimal_count',
]


def _send_submission(submission, task, is_scoring, run_args):
    if not submission.prediction_result.name:
        submission.prediction_result.save('prediction_result.zip', ContentFile(''.encode()))  # must encode here for GCS
        submission.save(update_fields=['prediction_result'])
    if not submission.scoring_result.name:
        submission.scoring_result.save('scoring_result.zip', ContentFile(''.encode()))  # must encode here for GCS
        submission.save(update_fields=['scoring_result'])
    submission = Submission.objects.get(id=submission.id)

    if not is_scoring:
        run_args['prediction_result'] = make_url_sassy(
            path=submission.prediction_result.name,
            permission='w'
        )
    else:
        run_args['prediction_result'] = make_url_sassy(
            path=submission.prediction_result.name,
            permission='r'
        )
        run_args['scoring_result'] = make_url_sassy(
            path=submission.scoring_result.name,
            permission='w'
        )

    if task.ingestion_program:
        if (task.ingestion_only_during_scoring and is_scoring) or (not task.ingestion_only_during_scoring and not is_scoring):
            run_args['ingestion_program'] = make_url_sassy(task.ingestion_program.data_file.name)

    if not is_scoring and task.input_data:
        run_args['input_data'] = make_url_sassy(task.input_data.data_file.name)

    if is_scoring and task.reference_data:
        run_args['reference_data'] = make_url_sassy(task.reference_data.data_file.name)

    run_args['ingestion_only_during_scoring'] = task.ingestion_only_during_scoring

    run_args['program_data'] = make_url_sassy(
        path=submission.data.data_file.name if not is_scoring else task.scoring_program.data_file.name
    )

    run_args['task_pk'] = task.id

    if not is_scoring:
        detail_names = SubmissionDetails.DETAILED_OUTPUT_NAMES_PREDICTION
    else:
        detail_names = SubmissionDetails.DETAILED_OUTPUT_NAMES_SCORING

    for detail_name in detail_names:
        run_args[detail_name] = create_detailed_output_file(detail_name, submission)

    print("Task data:")
    print(run_args)

    # Pad timelimit so worker has time to cleanup
    time_padding = 60 * 20  # 20 minutes
    time_limit = submission.phase.execution_time_limit + time_padding

    task = app.send_task('compute_worker_run', args=(run_args,), queue='compute-worker',
                         soft_time_limit=time_limit)
    submission.task_id = task.id
    submission.status = Submission.SUBMITTED
    submission.save()


def create_detailed_output_file(detail_name, submission):
    # Detail logs like stdout/etc.
    new_details = SubmissionDetails.objects.create(submission=submission, name=detail_name)
    new_details.data_file.save(f'{detail_name}.txt', ContentFile(''.encode()))  # must encode here for GCS
    return make_url_sassy(new_details.data_file.name, permission="w")


def run_submission(submission_pk, task_pk=None, is_scoring=False):
    return _run_submission.apply_async((submission_pk, task_pk, is_scoring))


@app.task(queue='site-worker', soft_time_limit=60)
def _run_submission(submission_pk, task_pk=None, is_scoring=False):
    """This function is wrapped so that when we run tests we can run this function not
    via celery"""
    select_models = (
        'phase',
        'phase__competition',
    )
    prefetch_models = (
        'details',
        'phase__tasks__input_data',
        'phase__tasks__reference_data',
        'phase__tasks__scoring_program',
        'phase__tasks__ingestion_program',
    )
    qs = Submission.objects.select_related(*select_models).prefetch_related(*prefetch_models)
    submission = qs.get(pk=submission_pk)

    run_arguments = {
        "submissions_api_url": os.environ.get('SUBMISSIONS_API_URL', "http://django/api"),
        "secret": submission.secret,
        "docker_image": submission.phase.competition.docker_image,
        "execution_time_limit": submission.phase.execution_time_limit,
        "id": submission.pk,
        "is_scoring": is_scoring,
    }

    tasks = submission.phase.tasks.all()
    if task_pk is None:  # This is the initial submission object
        if len(tasks) > 1:
            # The initial submission object becomes the parent submission and we create children for each task
            submission.has_children = True
            submission.status = 'Running'
            submission.save()
            for task in tasks:
                # TODO: make a duplicate submission method and use it here
                sub = Submission(
                    owner=submission.owner,
                    phase=submission.phase,
                    data=submission.data,
                    participant=submission.participant,
                    parent=submission,
                )
                sub.save(ignore_submission_limit=True)
                # run_submission.apply_async((sub.id, task.id))
                run_submission(sub.id, task.id)
        else:
            # The initial submission object will be the only submission
            task = tasks.first()
            _send_submission(
                submission=submission,
                task=task,
                run_args=run_arguments,
                is_scoring=is_scoring
            )
    else:
        task = Task.objects.get(id=task_pk)
        _send_submission(
            submission=submission,
            task=task,
            run_args=run_arguments,
            is_scoring=is_scoring
        )


@app.task(queue='site-worker', soft_time_limit=60 * 60)  # 1 hour timeout
def unpack_competition(competition_dataset_pk):
    competition_dataset = Data.objects.get(pk=competition_dataset_pk)
    creator = competition_dataset.created_by

    # Children datasets are those that are created specifically for this "parent" competition.
    # They will be deleted if the competition creation fails
    # TODO: children_datasets = []

    status = CompetitionCreationTaskStatus.objects.create(
        dataset=competition_dataset,
        status=CompetitionCreationTaskStatus.STARTING,
    )

    try:
        with TemporaryDirectory() as temp_directory:
            # ---------------------------------------------------------------------
            # Extract bundle
            try:
                with zipfile.ZipFile(competition_dataset.data_file, 'r') as zip_pointer:
                    zip_pointer.extractall(temp_directory)
            except zipfile.BadZipFile:
                raise CompetitionUnpackingException("Bad zip file uploaded.")

            # ---------------------------------------------------------------------
            # Read metadata (competition.yaml)
            yaml_path = os.path.join(temp_directory, "competition.yaml")
            if not os.path.exists(yaml_path):
                raise CompetitionUnpackingException("competition.yaml is missing from zip, check your folder structure "
                                                    "to make sure it is in the root directory.")
            with open(yaml_path) as f:
                competition_yaml = yaml.load(f.read())

            yaml_version = str(competition_yaml.get('version', '1'))

            logger.info(f"The YAML version is: {yaml_version}")
            if yaml_version == '1':
                unpacker_class = V15Unpacker
            elif yaml_version == '2':
                unpacker_class = V2Unpacker
            else:
                raise CompetitionUnpackingException(
                    'A suitable version could not be found for this competition. Make sure one is supplied in the yaml.'
                )

            unpacker = unpacker_class(
                competition_yaml=competition_yaml,
                temp_directory=temp_directory,
                creator=creator,
            )

            unpacker.unpack()
            competition = unpacker.save()

            status.status = CompetitionCreationTaskStatus.FINISHED
            status.resulting_competition = competition
            status.save()
            logger.info("Competition saved!")

    except Exception as e:
        logger.info(str(e))
        status.details = str(e)
        status.status = CompetitionCreationTaskStatus.FAILED
        status.save()
        raise e


@app.task(queue='site-worker', soft_time_limit=60 * 10)
def create_competition_dump(competition_pk, keys_instead_of_files=True):
    yaml_data = {}
    try:
        # -------- SetUp -------

        logger.info(f"Finding competition {competition_pk}")
        comp = Competition.objects.get(pk=competition_pk)
        zip_buffer = BytesIO()
        zip_name = f"{comp.title}-{comp.created_when.isoformat()}.zip"
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        # -------- Main Competition Details -------
        for field in COMPETITION_FIELDS:
            if hasattr(comp, field):
                yaml_data[field] = getattr(comp, field, "")
        if comp.logo:
            logger.info("Checking logo")
            try:
                yaml_data['image'] = re.sub(r'.*/', '', comp.logo.name)
                zip_file.writestr(yaml_data['image'], comp.logo.read())
                logger.info(f"Logo found for competition {comp.pk}")
            except OSError:
                logger.warning(
                    f"Competition {comp.pk} has no file associated with the logo, even though the logo field is set."
                )

        # -------- Competition Pages -------
        yaml_data['pages'] = []
        for page in comp.pages.all():
            temp_page_data = {}
            for field in PAGE_FIELDS:
                if hasattr(page, field):
                    temp_page_data[field] = getattr(page, field, "")
            page_file_name = f"{slugify(page.title)}-{page.pk}.md"
            temp_page_data['file'] = page_file_name
            yaml_data['pages'].append(temp_page_data)
            zip_file.writestr(temp_page_data['file'], page.content)

        # -------- Competition Tasks/Solutions -------

        yaml_data['tasks'] = []
        yaml_data['solutions'] = []

        task_solution_pairs = {}
        tasks = [task for phase in comp.phases.all() for task in phase.tasks.all()]

        index_two = 0

        # Go through all tasks
        for index, task in enumerate(tasks):

            task_solution_pairs[task.id] = {
                'index': index,
                'solutions': {
                    'ids': [],
                    'indexes': []
                }
            }

            temp_task_data = {
                'index': index
            }
            for field in TASK_FIELDS:
                data = getattr(task, field, "")
                if field == 'key':
                    data = str(data)
                temp_task_data[field] = data
            for file_type in PHASE_FILES:
                if hasattr(task, file_type):
                    temp_dataset = getattr(task, file_type)
                    if temp_dataset:
                        if temp_dataset.data_file:
                            try:
                                temp_task_data[file_type] = f"{file_type}-{task.pk}.zip"
                                zip_file.writestr(temp_task_data[file_type], temp_dataset.data_file.read())
                            except OSError:
                                logger.error(
                                    f"The file field is set, but no actual"
                                    f" file was found for dataset: {temp_dataset.pk} with name {temp_dataset.name}"
                                )
                        else:
                            logger.warning(f"Could not find data file for dataset object: {temp_dataset.pk}")
            # Now for all of our solutions for the tasks, write those too
            for solution in task.solutions.all():
                # for index_two, solution in enumerate(task.solutions.all()):
                #     temp_index = index_two
                # IF OUR SOLUTION WAS ALREADY ADDED
                if solution.id in task_solution_pairs[task.id]['solutions']['ids']:
                    for solution_data in yaml_data['solutions']:
                        if solution_data['key'] == solution.key:
                            solution_data['tasks'].append(task.id)
                            break
                    break
                # Else if our index is already taken
                elif index_two in task_solution_pairs[task.id]['solutions']['indexes']:
                    index_two += 1
                task_solution_pairs[task.id]['solutions']['indexes'].append(index_two)
                task_solution_pairs[task.id]['solutions']['ids'].append(solution.id)

                temp_solution_data = {
                    'index': index_two
                }
                for field in SOLUTION_FIELDS:
                    if hasattr(solution, field):
                        data = getattr(solution, field, "")
                        if field == 'key':
                            data = str(data)
                        temp_solution_data[field] = data
                if solution.data:
                    temp_dataset = getattr(solution, 'data')
                    if temp_dataset:
                        if temp_dataset.data_file:
                            try:
                                temp_solution_data['path'] = f"solution-{solution.pk}.zip"
                                zip_file.writestr(temp_solution_data['path'], temp_dataset.data_file.read())
                            except OSError:
                                logger.error(
                                    f"The file field is set, but no actual"
                                    f" file was found for dataset: {temp_dataset.pk} with name {temp_dataset.name}"
                                )
                        else:
                            logger.warning(f"Could not find data file for dataset object: {temp_dataset.pk}")
                # TODO: Make sure logic here is right. Needs to be outputted as a list, but what others can we tie to?
                temp_solution_data['tasks'] = [index]
                yaml_data['solutions'].append(temp_solution_data)
                index_two += 1
            # End for loop for solutions; Append tasks data
            yaml_data['tasks'].append(temp_task_data)

        # -------- Competition Phases -------

        yaml_data['phases'] = []
        for phase in comp.phases.all():
            temp_phase_data = {}
            for field in PHASE_FIELDS:
                if hasattr(phase, field):
                    if field == 'start' or field == 'end':
                        temp_date = getattr(phase, field)
                        if not temp_date:
                            continue
                        temp_date = temp_date.strftime("%m-%d-%Y")
                        temp_phase_data[field] = temp_date
                    elif field == 'max_submissions_per_person':
                        temp_phase_data['max_submissions'] = getattr(phase, field)
                    elif field == 'execution_time_limit':
                        temp_phase_data['execution_time_limit_ms'] = getattr(phase, field)
                    else:
                        temp_phase_data[field] = getattr(phase, field, "")
            task_indexes = [task_solution_pairs[task.id]['index'] for task in phase.tasks.all()]
            temp_phase_data['tasks'] = task_indexes
            temp_phase_solutions = []
            for task in phase.tasks.all():
                temp_phase_solutions += task_solution_pairs[task.id]['solutions']['indexes']
            temp_phase_data['solutions'] = temp_phase_solutions
            yaml_data['phases'].append(temp_phase_data)
        yaml_data['phases'] = sorted(yaml_data['phases'], key=lambda phase: phase['index'])

        # -------- Leaderboards -------

        yaml_data['leaderboards'] = []
        for index, leaderboard in enumerate(comp.leaderboards.all()):
            ldb_data = {
                'index': index
            }
            for field in LEADERBOARD_FIELDS:
                if hasattr(leaderboard, field):
                    ldb_data[field] = getattr(leaderboard, field, "")
            ldb_data['columns'] = []
            for column in leaderboard.columns.all():
                col_data = {}
                for field in COLUMN_FIELDS:
                    if hasattr(column, field):
                        col_data[field] = getattr(column, field, "")
                ldb_data['columns'].append(col_data)
            yaml_data['leaderboards'].append(ldb_data)

        # ------- Finalize --------
        logger.info(f"YAML data to be written is: {yaml_data}")
        comp_yaml = yaml.safe_dump(yaml_data, default_flow_style=False, allow_unicode=True, encoding="utf-8")
        logger.info(f"YAML output: {comp_yaml}")
        zip_file.writestr("competition.yaml", comp_yaml)
        zip_file.close()
        logger.info("Creating ZIP file")
        competition_dump_file = ContentFile(zip_buffer.getvalue())
        logger.info("Creating new Data object with type competition_bundle")
        bundle_count = CompetitionDump.objects.count() + 1
        temp_dataset_bundle = Data.objects.create(
            created_by=comp.created_by,
            name=f"{comp.title} Dump #{bundle_count} Created {comp.created_when.date()}",
            type='competition_bundle',
            description='Automatically created competition dump',
            # 'data_file'=,
        )
        logger.info("Saving zip to Competition Bundle")
        temp_dataset_bundle.data_file.save(zip_name, competition_dump_file)
        logger.info("Creating new CompetitionDump object")
        temp_comp_dump = CompetitionDump.objects.create(
            dataset=temp_dataset_bundle,
            status="Finished",
            details="Competition Bundle {0} for Competition {1}".format(temp_dataset_bundle.pk, comp.pk),
            competition=comp
        )
        logger.info(f"Finished creating competition dump: {temp_comp_dump.pk} for competition: {comp.pk}")
    except ObjectDoesNotExist:
        logger.info("Could not find competition with pk {} to create a competition dump".format(competition_pk))


@app.task(queue='site-worker', soft_time_limit=60 * 5)
def do_phase_migrations():
    # Update phase statuses
    previous_subquery = Phase.objects.filter(
        competition=OuterRef('competition'),
        end__lte=now()
    ).order_by('-index').values('index')[:1]

    current_subquery = Phase.objects.filter(
        competition=OuterRef('competition'),
        start__lte=now(),
        end__gt=now(),
    ).values('index')[:1]

    next_subquery = Phase.objects.filter(
        competition=OuterRef('competition'),
        start__gt=now()
    ).order_by('index').values('index')[:1]

    Phase.objects.annotate(
        previous_index=Subquery(previous_subquery),
        current_index=Subquery(current_subquery),
        next_index=Subquery(next_subquery),
    ).update(status=Case(
        When(index=F('previous_index'), then=Value(Phase.PREVIOUS)),
        When(index=F('current_index'), then=Value(Phase.CURRENT)),
        When(index=F('next_index'), then=Value(Phase.NEXT)),
        default=None
    ))

    # Updating Competitions whose phases have finished migrating to `is_migrating=False`
    completed_statuses = [Submission.FINISHED, Submission.FAILED, Submission.CANCELLED, Submission.NONE]

    running_subs_query = Submission.objects.filter(
        created_by_migration=OuterRef('pk')
    ).exclude(
        status__in=completed_statuses
    ).values_list('pk')[:1]

    Competition.objects.filter(
        pk__in=Phase.objects.annotate(
            running_subs=Count(Subquery(running_subs_query))
        ).filter(
            running_subs=0,
            competition__is_migrating=True,
            status=Phase.PREVIOUS
        ).values_list('competition__pk', flat=True)
    ).update(is_migrating=False)

    # Checking for new phases to start migrating
    new_phases = Phase.objects.filter(
        auto_migrate_to_this_phase=True,
        start__lte=now(),
        competition__is_migrating=False,
        has_been_migrated=False
    )

    logger.info(f"Checking {len(new_phases)} phases for phase migrations.")

    for p in new_phases:
        p.check_future_phase_submissions()
