"""
Code to delete submissions.

Use SubmissionDeleter whenever a submission is deleted or soft deleted.
Submission.delete() and Submission.soft_delete() use it too.
When a parent submission is deleted, its child submissions are deleted too.
(A parent has one child per task, in phases with more than one task.)
"""
import logging

from django.db import transaction
from django.db.models import Count, F, Q
from django.db.models.functions import Greatest
from django.utils.timezone import now

from competitions.models import Competition, Submission, SubmissionDetails
from datasets.models import Data
from leaderboards.models import SubmissionScore

logger = logging.getLogger(__name__)

SUBMISSION_FILE_FIELDS = ['prediction_result', 'scoring_result', 'detailed_result']


class SubmissionDeleter:
    """
    Deletes submissions and everything they have.

    For each submission, it deletes:
        - its child submissions
        - its logs
        - its leaderboard scores
        - its zip
        - its files: prediction result, scoring result, detailed result, logs and zip

    It works for a submission with children and for a submission without children.
    If you give it a child, it deletes only that child.

    A zip is not deleted if another submission still uses it.

    First the database records are deleted. Then the files are deleted.

    There are two ways to delete:
        - delete(): deletes everything, including the submission records.
        - soft_delete(): deletes everything, but keeps the submission records.
          The records are marked as soft deleted.
    """

    def __init__(self, submissions):
        """`submissions`: the submissions to delete. Their children are added here."""
        given_ids = [submission.id for submission in submissions]

        # Ids of the submissions to delete: the given ones and their children
        self.submission_ids = list(
            Submission.objects.filter(Q(id__in=given_ids) | Q(parent_id__in=given_ids)).values_list('id', flat=True)
        )
        submissions = Submission.objects.filter(id__in=self.submission_ids)

        # Ids of their leaderboard scores
        self.score_ids = list(
            SubmissionScore.objects.filter(submissions__in=submissions).values_list('id', flat=True).distinct()
        )

        # Ids of their zips
        zip_ids = set(submissions.exclude(data__isnull=True).values_list('data_id', flat=True))

        # Some zips must not be deleted.
        # Why: another submission can use the same zip, for example after a phase migration.
        # If that other submission is not deleted, it still needs the zip.
        # So: find the submissions that use our zips and are NOT in our list. Their zips are kept.
        # (Children use their parent's zip too. But they are in our list, so they don't count.)
        used_zip_ids = set(
            Submission.objects.filter(data_id__in=zip_ids).exclude(id__in=self.submission_ids)
            .values_list('data_id', flat=True)
        )

        # Ids of the zips to delete: our zips, without the ones to keep
        self.zip_ids = sorted(zip_ids - used_zip_ids)

        # How many parent submissions we delete in each competition.
        # Why: each competition shows a submission count. Only parents are counted, not children.
        # We lower that count by this number.
        self.parents_deleted_per_competition = {
            row['phase__competition']: row['count']
            for row in submissions.filter(parent__isnull=True).values('phase__competition').annotate(count=Count('id'))
        }

    def files(self):
        """
        Returns the files to delete, grouped by type: {type: [(storage, file name)]}.
        The types are: result files, log files and zips. They are used for the log report.
        """
        submissions = Submission.objects.filter(id__in=self.submission_ids)

        # Result files of the submissions
        result_files = []
        for field in SUBMISSION_FILE_FIELDS:
            storage = Submission._meta.get_field(field).storage
            result_files += [(storage, name) for name in submissions.values_list(field, flat=True) if name]

        # Log files of the submissions
        details = SubmissionDetails.objects.filter(submission__in=self.submission_ids)
        details_storage = SubmissionDetails._meta.get_field('data_file').storage
        log_files = [(details_storage, name) for name in details.values_list('data_file', flat=True) if name]

        # Zip files
        zips = Data.objects.filter(id__in=self.zip_ids)
        zip_storage = Data._meta.get_field('data_file').storage
        zip_files = [(zip_storage, name) for name in zips.values_list('data_file', flat=True) if name]

        return {
            'result files': result_files,
            'log files': log_files,
            'zips': zip_files,
        }

    def delete(self):
        """Deletes the database records first, then the files."""
        # Get the file names now. After the records are deleted, we can't read them anymore.
        files = self.files()

        # Everything inside this block is deleted together. If one step fails, nothing is deleted.
        with transaction.atomic():
            SubmissionScore.objects.filter(id__in=self.score_ids).delete()

            # This also deletes the logs of the submissions.
            # It does not call Submission.delete(), so it does not come back to this class.
            # (A queryset delete never calls the model's delete():
            # https://docs.djangoproject.com/en/5.2/ref/models/querysets/#delete)
            Submission.objects.filter(id__in=self.submission_ids).delete()

            Data.objects.filter(id__in=self.zip_ids).delete()

            # Lower the submission count of each competition. It never goes below 0.
            for competition_id, count in self.parents_deleted_per_competition.items():
                Competition.objects.filter(id=competition_id).update(
                    submissions_count=Greatest(F('submissions_count') - count, 0)
                )

            # Delete the files only after the records are really deleted.
            # robust=True: if deleting the files fails, we log the error and the delete still succeeds.
            transaction.on_commit(lambda: self._delete_files(files), robust=True)

    def soft_delete(self):
        """
        Deletes everything except the submission records, then the files.
        The submission records (parents and children) stay and are marked as soft deleted.
        The competition's submission count does not change, because the records stay.
        """
        # Get the file names now. After the records are cleared, we can't read them anymore.
        files = self.files()

        # Everything inside this block is done together. If one step fails, nothing is changed.
        with transaction.atomic():
            SubmissionScore.objects.filter(id__in=self.score_ids).delete()
            SubmissionDetails.objects.filter(submission__in=self.submission_ids).delete()

            # Keep the submission records, but remove their links to the deleted files and zip,
            # and mark them as soft deleted
            Submission.objects.filter(id__in=self.submission_ids).update(
                prediction_result=None,
                prediction_result_file_size=0,
                scoring_result=None,
                scoring_result_file_size=0,
                detailed_result=None,
                detailed_result_file_size=0,
                data=None,
                organization=None,
                is_soft_deleted=True,
                soft_deleted_when=now(),
            )

            Data.objects.filter(id__in=self.zip_ids).delete()

            # Delete the files only after the records are really changed.
            # robust=True: if deleting the files fails, we log the error and the soft delete still succeeds.
            transaction.on_commit(lambda: self._delete_files(files), robust=True)

    def _delete_files(self, files):
        """
        Deletes the files from storage, and logs one report at the end.
        If one file fails, we add it to the report and continue with the other files.
        `files`: the files to delete, grouped by type (see files()).
        """
        # We build the whole report first and log it once at the end,
        # so it is not mixed with other logs
        total_count = sum(len(type_files) for type_files in files.values())
        total_failed = 0
        report = [
            "=" * 80,
            f"Deleting files of submissions {self.submission_ids}",
            f"Files to delete: {total_count}",
            "=" * 80,
        ]

        for file_type, type_files in files.items():
            failed_files = []
            for storage, file_name in type_files:
                try:
                    storage.delete(file_name)
                except Exception as e:
                    failed_files.append(f"Failed to delete {file_name}: {e}")

            # One line per type, e.g. "log files    15 of 16 deleted, 1 failed"
            deleted_count = len(type_files) - len(failed_files)
            failed_text = f", {len(failed_files)} failed" if failed_files else ""
            report.append(f"{file_type:<16} {deleted_count} of {len(type_files)} deleted{failed_text}")
            # Then one line for each file that failed
            report.extend(f"    {failed_file}" for failed_file in failed_files)
            total_failed += len(failed_files)

        report += [
            "=" * 80,
            f"Total: {total_count - total_failed} deleted, {total_failed} failed",
            "=" * 80,
        ]
        # Logged as an error if any file failed, so it is easy to find
        log = logger.error if total_failed else logger.info
        log("\n" + "\n".join(report))
