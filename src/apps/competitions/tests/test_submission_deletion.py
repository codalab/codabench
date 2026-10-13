from unittest import mock

from django.test import TestCase
from django.urls import reverse

from competitions.models import Competition, Submission, SubmissionDetails
from competitions.submission_deletion import SubmissionDeleter
from datasets.models import Data
from factories import (
    UserFactory, CompetitionFactory, PhaseFactory, LeaderboardFactory, ColumnFactory, SubmissionFactory,
    SubmissionScoreFactory, DataFactory,
)
from leaderboards.models import SubmissionScore
from utils.storage import BundleStorage


class SubmissionDeletionTestBase(TestCase):
    """
    Shared setup and helpers for the delete and soft delete tests of SubmissionDeleter.
    BundleStorage.delete is mocked, so no real file is deleted; all submission files are in BundleStorage.
    """

    def setUp(self):
        self.organizer = UserFactory(username='organizer', password='organizer')
        self.competition = CompetitionFactory(created_by=self.organizer)
        self.leaderboard = LeaderboardFactory()
        self.column = ColumnFactory(leaderboard=self.leaderboard)
        self.phase = PhaseFactory(competition=self.competition, leaderboard=self.leaderboard)

    def _submission(self, name, parent=None, data=None):
        """
        Creates a submission with 3 result files, 1 log and 1 score. File names are only stored, not uploaded.
        A child shares its parent's zip; other submissions get their own zip unless `data` is given.
        """
        if data is None:
            data = parent.data if parent else DataFactory(
                type=Data.SUBMISSION, created_by=self.organizer, data_file=f'dataset/{name}.zip', file_size=10,
            )
        submission = SubmissionFactory(
            owner=self.organizer,
            phase=self.phase,
            parent=parent,
            leaderboard=self.leaderboard,
            data=data,
            prediction_result=f'prediction_result/{name}.zip',
            prediction_result_file_size=10,
            scoring_result=f'scoring_result/{name}.zip',
            scoring_result_file_size=10,
            detailed_result=f'detailed_result/{name}.html',
            detailed_result_file_size=10,
        )
        SubmissionDetails.objects.create(
            submission=submission, name='prediction_stdout', data_file=f'submission_details/{name}.txt', file_size=10,
        )
        SubmissionScoreFactory(column=self.column, submissions=submission)
        return submission

    @staticmethod
    def _file_names(name):
        """Returns the names of the result files and log created by _submission for `name`"""
        return {
            f'prediction_result/{name}.zip',
            f'scoring_result/{name}.zip',
            f'detailed_result/{name}.html',
            f'submission_details/{name}.txt',
        }

    def _delete(self, submissions, storage_errors=None, soft=False):
        """
        Deletes `submissions` with SubmissionDeleter and returns the names of the files deleted from storage.
        `storage_errors` gives what each storage delete does, in order: None succeeds, an exception fails.
        `soft=True` soft deletes them instead.
        """
        # Replace the storage's delete with a mock, so no real file is deleted.
        # All submission files are in BundleStorage, so this catches every file delete.
        # The mock records each file name it is called with, so we can check which files were deleted.
        # side_effect: what each call does, in order. None = the delete works, an exception = the delete fails.
        # If storage_errors is None, every delete works.
        with mock.patch.object(BundleStorage, 'delete', side_effect=storage_errors) as storage_delete:
            # Files are deleted with transaction.on_commit, which only runs after a real commit.
            # Tests run inside a transaction that is rolled back after each test, so the callback would
            # never run. captureOnCommitCallbacks(execute=True) runs it at the end of this block.
            with self.captureOnCommitCallbacks(execute=True):
                deleter = SubmissionDeleter(submissions=submissions)
                if soft:
                    deleter.soft_delete()
                else:
                    deleter.delete()
        return {call.args[0] for call in storage_delete.call_args_list}

    def _submissions_count(self):
        """Returns the competition's submission count, as stored in the database"""
        return Competition.objects.get(pk=self.competition.pk).submissions_count


class SubmissionDeleteTests(SubmissionDeletionTestBase):
    """
    Tests for deleting submissions (SubmissionDeleter.delete): which records are deleted or kept,
    which files are deleted from storage and how the competition's submission count changes.
    """

    def test_submission_without_children_is_deleted_with_everything(self):
        """A submission without children is deleted with its log, score and zip, and all its files"""
        submission = self._submission(name='single')
        zip_data = submission.data
        count_before = self._submissions_count()

        deleted_files = self._delete(submissions=[submission])

        assert not Submission.objects.filter(pk=submission.pk).exists()
        assert not SubmissionDetails.objects.filter(submission_id=submission.pk).exists()
        assert not SubmissionScore.objects.filter(submissions=submission.pk).exists()
        assert not Data.objects.filter(pk=zip_data.pk).exists()
        # `|` joins the two sets: the 4 files of the submission, plus its zip
        assert deleted_files == self._file_names('single') | {'dataset/single.zip'}
        assert self._submissions_count() == count_before - 1

    def test_parent_is_deleted_with_its_children(self):
        """A parent is deleted with its children, all their logs, scores and files, and their shared zip"""
        parent = self._submission(name='parent')
        child_1 = self._submission(name='child_1', parent=parent)
        child_2 = self._submission(name='child_2', parent=parent)
        count_before = self._submissions_count()

        deleted_files = self._delete(submissions=[parent])

        submission_ids = [parent.pk, child_1.pk, child_2.pk]
        assert not Submission.objects.filter(pk__in=submission_ids).exists()
        assert not SubmissionDetails.objects.filter(submission_id__in=submission_ids).exists()
        assert not SubmissionScore.objects.filter(submissions__in=submission_ids).exists()
        # The zip is shared by the parent and its children, so it is deleted with them
        assert not Data.objects.filter(pk=parent.data_id).exists()
        # `|` joins the sets: the 4 files of the parent and of each child, plus the shared zip
        assert deleted_files == (
            self._file_names('parent') | self._file_names('child_1') | self._file_names('child_2') |
            {'dataset/parent.zip'}
        )
        # Only the parent is counted in the competition's submission count
        assert self._submissions_count() == count_before - 1

    def test_zip_used_by_another_submission_is_kept(self):
        """A zip also used by a submission that is not deleted (e.g. a phase migration) is kept with its file"""
        submission = self._submission(name='original')
        migrated = self._submission(name='migrated', data=submission.data)

        deleted_files = self._delete(submissions=[submission])

        assert Submission.objects.filter(pk=migrated.pk).exists()
        assert Data.objects.filter(pk=submission.data_id).exists()
        assert deleted_files == self._file_names('original')

    def test_deleting_a_child_alone_keeps_parent_and_count(self):
        """Deleting a child on its own deletes only the child and its files; the parent and the count stay"""
        parent = self._submission(name='parent')
        child = self._submission(name='child', parent=parent)
        count_before = self._submissions_count()

        deleted_files = self._delete(submissions=[child])

        assert not Submission.objects.filter(pk=child.pk).exists()
        assert Submission.objects.filter(pk=parent.pk).exists()
        # The zip is still used by the parent
        assert Data.objects.filter(pk=parent.data_id).exists()
        assert deleted_files == self._file_names('child')
        assert self._submissions_count() == count_before

    def test_failed_file_is_logged_and_other_files_still_deleted(self):
        """
        When a file fails to delete, the other files are still deleted,
        and one report is logged as an error, with the failed file under its type
        """
        submission = self._submission(name='single')

        # Files are deleted in this order: 3 result files, 1 log file, 1 zip.
        # The first one (the prediction result) fails, the other 4 are deleted.
        with self.assertLogs('competitions.submission_deletion', level='INFO') as logs:
            deleted_files = self._delete(submissions=[submission], storage_errors=[Exception('storage error')] + [None] * 4)

        # All 5 files were tried, and the record is deleted anyway
        assert len(deleted_files) == 5
        assert not Submission.objects.filter(pk=submission.pk).exists()

        # The whole report is logged once, as an error because a file failed
        assert len(logs.records) == 1
        assert logs.records[0].levelname == 'ERROR'
        report = logs.records[0].getMessage()
        assert f'Deleting files of submissions [{submission.pk}]' in report
        assert f"{'result files':<16} 2 of 3 deleted, 1 failed" in report
        assert 'Failed to delete prediction_result/single.zip: storage error' in report
        assert f"{'log files':<16} 1 of 1 deleted" in report
        assert f"{'zips':<16} 1 of 1 deleted" in report
        assert 'Total: 4 deleted, 1 failed' in report

    def test_submission_delete_uses_the_deleter(self):
        """Submission.delete() creates a SubmissionDeleter for the submission and calls its delete()"""
        submission = self._submission(name='single')

        # Replace SubmissionDeleter with a mock, to check how Submission.delete() uses it.
        # This works because Submission.delete() imports SubmissionDeleter from this module when it runs.
        with mock.patch('competitions.submission_deletion.SubmissionDeleter') as deleter_class:
            submission.delete()

        # SubmissionDeleter was created once, for this submission...
        deleter_class.assert_called_once_with(submissions=[submission])
        # ...and its delete() was called once
        deleter_class.return_value.delete.assert_called_once_with()

    def test_api_delete_removes_children_and_files(self):
        """Deleting a submission through the API as the organizer deletes its children and files too"""
        parent = self._submission(name='parent')
        child = self._submission(name='child', parent=parent)
        self.client.force_login(self.organizer)

        with mock.patch.object(BundleStorage, 'delete') as storage_delete:
            with self.captureOnCommitCallbacks(execute=True):
                resp = self.client.delete(reverse('submission-detail', kwargs={'pk': parent.pk}))

        assert resp.status_code == 204
        assert not Submission.objects.filter(pk__in=[parent.pk, child.pk]).exists()
        # `|` joins the sets: the 4 files of the parent and of the child, plus the shared zip
        assert {call.args[0] for call in storage_delete.call_args_list} == (
            self._file_names('parent') | self._file_names('child') | {'dataset/parent.zip'}
        )


class SubmissionSoftDeleteTests(SubmissionDeletionTestBase):
    """
    Tests for soft deleting submissions (SubmissionDeleter.soft_delete): the submission records stay
    and are marked as soft deleted, everything else (logs, scores, zip and files) is deleted.
    """

    def _assert_soft_deleted(self, submission_ids):
        """Checks that the submissions still exist, are marked soft deleted and no longer point to files or a zip"""
        submissions = Submission.objects.filter(pk__in=submission_ids)
        assert submissions.count() == len(submission_ids)
        for submission in submissions:
            assert submission.is_soft_deleted
            assert submission.soft_deleted_when is not None
            assert not submission.prediction_result
            assert not submission.scoring_result
            assert not submission.detailed_result
            assert submission.data_id is None

    def test_soft_delete_keeps_only_the_record(self):
        """
        Soft deleting a submission without children keeps its record, marked as soft deleted.
        Its log, score, zip and files are deleted, and the competition's submission count does not change.
        """
        submission = self._submission(name='single')
        zip_data = submission.data
        count_before = self._submissions_count()

        deleted_files = self._delete(submissions=[submission], soft=True)

        self._assert_soft_deleted([submission.pk])
        assert not SubmissionDetails.objects.filter(submission_id=submission.pk).exists()
        assert not SubmissionScore.objects.filter(submissions=submission.pk).exists()
        assert not Data.objects.filter(pk=zip_data.pk).exists()
        # `|` joins the two sets: the 4 files of the submission, plus its zip
        assert deleted_files == self._file_names('single') | {'dataset/single.zip'}
        assert self._submissions_count() == count_before

    def test_soft_delete_parent_also_soft_deletes_its_children(self):
        """
        Soft deleting a parent keeps the records of the parent and its children, all marked as soft deleted.
        All their logs, scores and files are deleted, and the shared zip too.
        """
        parent = self._submission(name='parent')
        child_1 = self._submission(name='child_1', parent=parent)
        child_2 = self._submission(name='child_2', parent=parent)
        zip_data = parent.data

        deleted_files = self._delete(submissions=[parent], soft=True)

        submission_ids = [parent.pk, child_1.pk, child_2.pk]
        self._assert_soft_deleted(submission_ids)
        assert not SubmissionDetails.objects.filter(submission_id__in=submission_ids).exists()
        assert not SubmissionScore.objects.filter(submissions__in=submission_ids).exists()
        assert not Data.objects.filter(pk=zip_data.pk).exists()
        # `|` joins the sets: the 4 files of the parent and of each child, plus the shared zip
        assert deleted_files == (
            self._file_names('parent') | self._file_names('child_1') | self._file_names('child_2') |
            {'dataset/parent.zip'}
        )

    def test_submission_soft_delete_uses_the_deleter(self):
        """Submission.soft_delete() creates a SubmissionDeleter for the submission and calls its soft_delete()"""
        submission = self._submission(name='single')

        # Replace SubmissionDeleter with a mock, to check how Submission.soft_delete() uses it.
        # This works because Submission.soft_delete() imports SubmissionDeleter from this module when it runs.
        with mock.patch('competitions.submission_deletion.SubmissionDeleter') as deleter_class:
            submission.soft_delete()

        # SubmissionDeleter was created once, for this submission...
        deleter_class.assert_called_once_with(submissions=[submission])
        # ...and its soft_delete() was called once
        deleter_class.return_value.soft_delete.assert_called_once_with()

    def test_soft_delete_keeps_zip_used_by_another_submission(self):
        """Soft deleting keeps a zip that another submission (e.g. a phase migration) still uses"""
        submission = self._submission(name='original')
        migrated = self._submission(name='migrated', data=submission.data)

        deleted_files = self._delete(submissions=[submission], soft=True)

        self._assert_soft_deleted([submission.pk])
        assert Data.objects.filter(pk=migrated.data_id).exists()
        assert deleted_files == self._file_names('original')

    def test_api_soft_delete_as_owner(self):
        """The owner's soft delete through the API soft deletes the submission and its children"""
        parent = self._submission(name='parent')
        child = self._submission(name='child', parent=parent)
        # The API only allows soft deleting a finished submission that is not on the leaderboard
        Submission.objects.filter(pk__in=[parent.pk, child.pk]).update(status=Submission.FINISHED, leaderboard=None)
        self.client.force_login(self.organizer)

        with mock.patch.object(BundleStorage, 'delete') as storage_delete:
            with self.captureOnCommitCallbacks(execute=True):
                resp = self.client.delete(reverse('submission-soft-delete', kwargs={'pk': parent.pk}))

        assert resp.status_code == 200
        self._assert_soft_deleted([parent.pk, child.pk])
        # `|` joins the sets: the 4 files of the parent and of the child, plus the shared zip
        assert {call.args[0] for call in storage_delete.call_args_list} == (
            self._file_names('parent') | self._file_names('child') | {'dataset/parent.zip'}
        )
