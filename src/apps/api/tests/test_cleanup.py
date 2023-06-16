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
        self.user = UserFactory(username='test_user', password='test_user')
        # Create a competition
        self.comp = CompetitionFactory(created_by=self.user)
        # Create used tasks
        self.used_tasks = [TaskFactory(created_by=self.user), TaskFactory(created_by=self.user)]
        # Create unused task
        self.unused_tasks = [TaskFactory(created_by=self.user), TaskFactory(created_by=self.user)]
        # Create phase with used tasks
        self.phase = PhaseFactory(competition=self.comp, tasks=self.used_tasks)

        # Create used-failed submission
        self.failed_submissions = [SubmissionFactory(
            phase=self.phase,
            owner=self.user,
            status=Submission.FAILED,
            secret='7df3600c-1234-5678-bbc8-bbe91f42d875'
        )]
        # Create unused submission
        self.unused_submissions = [
            DataFactory(created_by=self.user, type=Data.SUBMISSION),
            DataFactory(created_by=self.user, type=Data.SUBMISSION)
        ]

        # Create unused datasets and programs
        self.unused_datasets_programs = [
            DataFactory(created_by=self.user, type=Data.INGESTION_PROGRAM),
            DataFactory(created_by=self.user, type=Data.SCORING_PROGRAM),
            DataFactory(created_by=self.user, type=Data.INPUT_DATA),
            DataFactory(created_by=self.user, type=Data.REFERENCE_DATA),
            DataFactory(created_by=self.user, type=Data.PUBLIC_DATA)
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
