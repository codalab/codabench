from rest_framework.test import APITestCase
from django.urls import reverse
from unittest import mock
import json
from factories import (
    UserFactory,
    CompetitionFactory,
    PhaseFactory,
    TaskFactory,
    SubmissionFactory,
    DataFactory,
    SolutionFactory
)
from competitions.models import Submission, CompetitionDump
from datasets.models import Data
from profiles.models import User
from tasks.models import Solution


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
        assert content["unused_competition_bundles_and_dumps"] == len(self.unused_competition_bundles)

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

        url = reverse('delete_unused_competition_bundles_and_dumps')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["success"]
        assert content["message"] == "Unused competition bundles and dumps deleted successfully"

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_competition_bundles_and_dumps"] == 0


    def test_delete_unused_datasets_keeps_solution_datasets(self):
        """
        Adds a solution linked to a used task, then counts and deletes unused datasets.
        Expected: the solution dataset is not counted, and the solution and its dataset still exist after the delete.
        """
        user = User.objects.get(username='test_user')
        solution_dataset = DataFactory(created_by=user, type=Data.SOLUTION)
        solution = SolutionFactory(data=solution_dataset)
        solution.tasks.add(self.used_tasks[0])

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_datasets_programs"] == len(self.unused_datasets_programs)

        url = reverse('delete_unused_datasets')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        assert json.loads(resp.content)["success"]

        assert Data.objects.filter(pk=solution_dataset.pk).exists()
        assert Solution.objects.filter(pk=solution.pk).exists()

    def test_delete_unused_datasets_removes_files_from_storage(self):
        """
        Gives each unused dataset a file, then presses "Delete unused datasets/programs".
        Expected: the datasets are deleted, and the file of each one is deleted from storage.
        """
        # update() instead of save().
        # Why: save() reads the file size from storage, and these test files don't exist there.
        file_names = []
        for dataset in self.unused_datasets_programs:
            file_name = f'dataset/test/{dataset.pk}.zip'
            Data.objects.filter(pk=dataset.pk).update(data_file=file_name)
            file_names.append(file_name)

        storage = Data._meta.get_field('data_file').storage
        # The files are deleted after the delete is saved, so we run those steps here
        with mock.patch.object(storage, 'delete') as delete_file, self.captureOnCommitCallbacks(execute=True):
            resp = self.client.delete(reverse('delete_unused_datasets'))

        assert resp.status_code == 200
        assert not Data.objects.filter(pk__in=[dataset.pk for dataset in self.unused_datasets_programs]).exists()
        deleted_file_names = [call.args[0] for call in delete_file.call_args_list]
        assert sorted(deleted_file_names) == sorted(file_names)

    def test_delete_unused_submissions_removes_files_from_storage(self):
        """
        Gives each unused submission zip a file, then presses "Delete unused submissions".
        Expected: the zips are deleted, and the file of each one is deleted from storage.
        """
        # update() instead of save().
        # Why: save() reads the file size from storage, and these test files don't exist there.
        file_names = []
        for submission_zip in self.unused_submissions:
            file_name = f'dataset/test/{submission_zip.pk}.zip'
            Data.objects.filter(pk=submission_zip.pk).update(data_file=file_name)
            file_names.append(file_name)

        storage = Data._meta.get_field('data_file').storage
        # The files are deleted after the delete is saved, so we run those steps here
        with mock.patch.object(storage, 'delete') as delete_file, self.captureOnCommitCallbacks(execute=True):
            resp = self.client.delete(reverse('delete_unused_submissions'))

        assert resp.status_code == 200
        assert not Data.objects.filter(pk__in=[submission_zip.pk for submission_zip in self.unused_submissions]).exists()
        deleted_file_names = [call.args[0] for call in delete_file.call_args_list]
        assert sorted(deleted_file_names) == sorted(file_names)

    def test_delete_unused_starting_kits_removes_files_from_storage(self):
        """
        Gives each unused starting kit a file, then presses "Delete unused starting kits".
        Expected: the starting kits are deleted, and the file of each one is deleted from storage.
        """
        # update() instead of save().
        # Why: save() reads the file size from storage, and these test files don't exist there.
        file_names = []
        for starting_kit in self.unused_starting_kits:
            file_name = f'dataset/test/{starting_kit.pk}.zip'
            Data.objects.filter(pk=starting_kit.pk).update(data_file=file_name)
            file_names.append(file_name)

        storage = Data._meta.get_field('data_file').storage
        # The files are deleted after the delete is saved, so we run those steps here
        with mock.patch.object(storage, 'delete') as delete_file, self.captureOnCommitCallbacks(execute=True):
            resp = self.client.delete(reverse('delete_unused_starting_kits'))

        assert resp.status_code == 200
        assert not Data.objects.filter(pk__in=[starting_kit.pk for starting_kit in self.unused_starting_kits]).exists()
        deleted_file_names = [call.args[0] for call in delete_file.call_args_list]
        assert sorted(deleted_file_names) == sorted(file_names)

    def test_delete_unused_competition_bundles_removes_files_from_storage(self):
        """
        Gives each unused competition bundle a file, then presses "Delete unused competition bundles".
        Expected: the bundles are deleted, and the file of each one is deleted from storage.
        """
        # update() instead of save().
        # Why: save() reads the file size from storage, and these test files don't exist there.
        file_names = []
        for bundle in self.unused_competition_bundles:
            file_name = f'dataset/test/{bundle.pk}.zip'
            Data.objects.filter(pk=bundle.pk).update(data_file=file_name)
            file_names.append(file_name)

        storage = Data._meta.get_field('data_file').storage
        # The files are deleted after the delete is saved, so we run those steps here
        with mock.patch.object(storage, 'delete') as delete_file, self.captureOnCommitCallbacks(execute=True):
            resp = self.client.delete(reverse('delete_unused_competition_bundles_and_dumps'))

        assert resp.status_code == 200
        assert not Data.objects.filter(pk__in=[bundle.pk for bundle in self.unused_competition_bundles]).exists()
        deleted_file_names = [call.args[0] for call in delete_file.call_args_list]
        assert sorted(deleted_file_names) == sorted(file_names)

    def test_delete_unused_competition_bundles_keeps_dumps_of_existing_competitions(self):
        """
        Adds a dump of an existing competition, then counts and deletes unused competition bundles.
        Expected: the dump is not counted, and the dump still exists after the delete.
        """
        user = User.objects.get(username='test_user')
        competition = CompetitionFactory(created_by=user)
        dump_dataset = DataFactory(created_by=user, type=Data.COMPETITION_BUNDLE)
        dump = CompetitionDump.objects.create(competition=competition, dataset=dump_dataset)

        url = reverse('user_quota_cleanup')
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = json.loads(resp.content)
        assert content["unused_competition_bundles_and_dumps"] == len(self.unused_competition_bundles)

        url = reverse('delete_unused_competition_bundles_and_dumps')
        resp = self.client.delete(url)
        assert resp.status_code == 200
        assert json.loads(resp.content)["success"]

        assert Data.objects.filter(pk=dump_dataset.pk).exists()
        assert CompetitionDump.objects.filter(pk=dump.pk).exists()
