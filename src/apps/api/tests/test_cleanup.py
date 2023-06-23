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
from competitions.models import Submission
from datasets.models import Data


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
            DataFactory(created_by=user, type=Data.REFERENCE_DATA),
            DataFactory(created_by=user, type=Data.PUBLIC_DATA)
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
