from unittest import mock
from rest_framework.test import APITestCase
from django.urls import reverse
import json
from factories import (
    UserFactory,
    CompetitionFactory,
    PhaseFactory,
    TaskFactory,
    SubmissionFactory,
    DataFactory
)
from competitions.models import Competition, Submission, SubmissionDetails
from datasets.models import Data
from utils.storage import BundleStorage


class CleanUpTests(APITestCase):
    def setUp(self):

        # Create a user
        user = UserFactory(username='test_user', password='test_user')

        # Create a competition
        comp = CompetitionFactory(created_by=user)

        # Create used tasks
        self.used_tasks = [
            TaskFactory(created_by=user),
            TaskFactory(created_by=user)
        ]

        # Create unused task
        self.unused_tasks = [
            TaskFactory(created_by=user),
            TaskFactory(created_by=user)
        ]

        # Create phase with used tasks
        phase = PhaseFactory(competition=comp, tasks=self.used_tasks)

        # Create used-failed submission
        self.failed_submissions = [SubmissionFactory(
            phase=phase,
            owner=user,
            status=Submission.FAILED,
            data=DataFactory(created_by=user, type=Data.SUBMISSION, competition=comp)
        )]

        # Create unused submission
        self.unused_submissions = [
            DataFactory(created_by=user, type=Data.SUBMISSION),
            DataFactory(created_by=user, type=Data.SUBMISSION)
        ]

        # Create unused datasets and programs
        self.unused_datasets_programs = [
            DataFactory(created_by=user, type=Data.INGESTION_PROGRAM),
            DataFactory(created_by=user, type=Data.SCORING_PROGRAM),
            DataFactory(created_by=user, type=Data.INPUT_DATA),
            DataFactory(created_by=user, type=Data.REFERENCE_DATA)
        ]

        # Create unused starting kits
        self.unused_starting_kits = [
            DataFactory(created_by=user, type=Data.STARTING_KIT),
            DataFactory(created_by=user, type=Data.STARTING_KIT)
        ]

        # Create unused competition bundles
        self.unused_competition_bundles = [
            DataFactory(created_by=user, type=Data.COMPETITION_BUNDLE),
            DataFactory(created_by=user, type=Data.COMPETITION_BUNDLE)
        ]

        self.client.login(username='test_user', password='test_user')

    def test_cleanup_stats(self):

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_tasks"] == len(self.unused_tasks)
        assert content["unused_datasets_programs"] == len(self.unused_datasets_programs)
        assert content["unused_submissions"] == len(self.unused_submissions)
        assert content["failed_submissions"] == len(self.failed_submissions)
        assert content["unused_starting_kits"] == len(self.unused_starting_kits)
        assert content["unused_competition_bundles"] == len(self.unused_competition_bundles)

    def test_delete_unused_tasks(self):

        url = reverse('delete_unused_tasks')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["success"]
        assert content["message"] == "Unused tasks deleted successfully"

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_tasks"] == 0

    def test_delete_unused_datasets(self):

        url = reverse('delete_unused_datasets')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["success"]
        assert content["message"] == "Unused datasets and programs deleted successfully"

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_datasets_programs"] == 0

    def test_delete_unused_submissions(self):

        url = reverse('delete_unused_submissions')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["success"]
        assert content["message"] == "Unused submissions deleted successfully"

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_submissions"] == 0

    def test_delete_failed_submissions(self):

        url = reverse('delete_failed_submissions')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["success"]
        assert content["message"] == "Failed submissions deleted successfully"

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["failed_submissions"] == 0

    def test_delete_unused_starting_kits(self):

        url = reverse('delete_unused_starting_kits')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["success"]
        assert content["message"] == "Unused starting kits deleted successfully"

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_starting_kits"] == 0

    def test_delete_unused_competition_bundles(self):

        url = reverse('delete_unused_competition_bundles')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["success"]
        assert content["message"] == "Unused competition bundles deleted successfully"

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_competition_bundles"] == 0


class DeleteFailedSubmissionsTests(APITestCase):
    """
    Tests for "Delete failed submissions" on the quota page: which submissions are deleted with their
    children, logs, zips and files, which ones are kept, and the failed submissions counter.
    BundleStorage.delete is mocked, so no real file is deleted; all submission files are in BundleStorage.
    """

    def setUp(self):
        self.user = UserFactory(username='user', password='user')
        self.other_user = UserFactory(username='other_user', password='other_user')
        self.competition = CompetitionFactory(created_by=self.user)
        self.phase = PhaseFactory(competition=self.competition)
        self.client.force_login(self.user)

    def _submission(self, name, status, owner=None, parent=None):
        """
        Creates a submission with 3 result files and 1 log. File names are only stored, not uploaded.
        A child shares its parent's zip; other submissions get their own zip.
        """
        owner = owner or self.user
        data = parent.data if parent else DataFactory(
            type=Data.SUBMISSION, created_by=owner, data_file=f'dataset/{name}.zip', file_size=10,
        )
        submission = SubmissionFactory(
            owner=owner,
            phase=self.phase,
            parent=parent,
            status=status,
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

    def _delete_failed_submissions(self):
        """Calls "Delete failed submissions" and returns the response and the names of the files deleted from storage"""
        # Replace the storage's delete with a mock, so no real file is deleted.
        # The mock records each file name it is called with, so we can check which files were deleted.
        with mock.patch.object(BundleStorage, 'delete') as storage_delete:
            # Files are deleted with transaction.on_commit, which only runs after a real commit.
            # Tests run inside a transaction that is rolled back after each test, so the callback would
            # never run. captureOnCommitCallbacks(execute=True) runs it at the end of this block.
            with self.captureOnCommitCallbacks(execute=True):
                resp = self.client.delete(reverse('delete_failed_submissions'))
        return resp, {call.args[0] for call in storage_delete.call_args_list}

    def _failed_counter(self):
        """Returns the failed submissions counter shown on the quota page"""
        return json.loads(self.client.get(reverse('user_quota_cleanup')).content)['failed_submissions']

    def _submissions_count(self):
        """Returns the competition's submission count, as stored in the database"""
        return Competition.objects.get(pk=self.competition.pk).submissions_count

    def test_failed_submission_is_deleted_with_its_files(self):
        """A failed submission without children is deleted with its log, zip and files; the count goes down"""
        submission = self._submission(name='failed', status=Submission.FAILED)
        count_before = self._submissions_count()

        resp, deleted_files = self._delete_failed_submissions()

        assert json.loads(resp.content)['success']
        assert not Submission.objects.filter(pk=submission.pk).exists()
        assert not SubmissionDetails.objects.filter(submission_id=submission.pk).exists()
        assert not Data.objects.filter(pk=submission.data_id).exists()
        # `|` joins the two sets: the 4 files of the submission, plus its zip
        assert deleted_files == self._file_names('failed') | {'dataset/failed.zip'}
        assert self._submissions_count() == count_before - 1

    def test_failed_parent_is_deleted_with_its_children(self):
        """A failed parent is deleted with its children, all their logs and files, and their shared zip"""
        parent = self._submission(name='parent', status=Submission.FAILED)
        child_1 = self._submission(name='child_1', status=Submission.FAILED, parent=parent)
        child_2 = self._submission(name='child_2', status=Submission.FAILED, parent=parent)

        resp, deleted_files = self._delete_failed_submissions()

        assert not Submission.objects.filter(pk__in=[parent.pk, child_1.pk, child_2.pk]).exists()
        assert not Data.objects.filter(pk=parent.data_id).exists()
        # `|` joins the sets: the 4 files of the parent and of each child, plus the shared zip
        assert deleted_files == (
            self._file_names('parent') | self._file_names('child_1') | self._file_names('child_2') |
            {'dataset/parent.zip'}
        )

    def test_other_submissions_are_kept(self):
        """
        Only the user's failed submissions are deleted. Kept: the user's finished submission,
        another user's failed submission, and a failed child whose parent did not fail
        """
        failed = self._submission(name='failed', status=Submission.FAILED)
        finished = self._submission(name='finished', status=Submission.FINISHED)
        other_users_failed = self._submission(name='other', status=Submission.FAILED, owner=self.other_user)
        finished_parent = self._submission(name='finished_parent', status=Submission.FINISHED)
        failed_child = self._submission(name='failed_child', status=Submission.FAILED, parent=finished_parent)

        resp, deleted_files = self._delete_failed_submissions()

        assert not Submission.objects.filter(pk=failed.pk).exists()
        kept_ids = [finished.pk, other_users_failed.pk, finished_parent.pk, failed_child.pk]
        assert Submission.objects.filter(pk__in=kept_ids).count() == 4
        # Only the files of the deleted submission are deleted
        assert deleted_files == self._file_names('failed') | {'dataset/failed.zip'}

    def test_failed_counter_shows_what_is_deleted(self):
        """
        The failed submissions counter counts what the button deletes: failed parents and failed submissions
        without children, not their children. It is 0 after the cleanup.
        """
        parent = self._submission(name='parent', status=Submission.FAILED)
        self._submission(name='child', status=Submission.FAILED, parent=parent)
        self._submission(name='failed', status=Submission.FAILED)

        # The parent and the submission without children, not the child
        assert self._failed_counter() == 2
        self._delete_failed_submissions()
        assert self._failed_counter() == 0
