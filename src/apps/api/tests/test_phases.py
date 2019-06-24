import json
import os
import tempfile
from datetime import timedelta

from PIL import Image
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APIClient

from api.serializers.competitions import PhaseSerializer, CompetitionSerializer
from competitions.models import Phase, Competition
from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory


class ReRunPhaseSubmissionTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.admin = UserFactory(username='admin', super_user=True)
        self.collab = UserFactory(username='collab')
        self.normal_user = UserFactory(username='norm')
        self.competition = CompetitionFactory(created_by=self.user)
        self.competition.collaborators.add(self.collab)
        self.phase = PhaseFactory(competition=self.competition)
        self.client = APIClient()

        for _ in range(4):
            self.make_submission()

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.user)
        kwargs.setdefault('phase', self.phase)
        SubmissionFactory(**kwargs)

    def assert_rerun_succeeds(self):
        response = self.client.get(reverse('phases-rerun_submissions', kwargs={'pk': self.phase.id}))
        assert response.data['count'] == 4
        assert self.phase.submissions.count() == 8

    def test_comp_creator_can_re_run_whole_phase(self):
        self.client.login(username='test', password='test')
        self.assert_rerun_succeeds()

    def test_super_user_can_re_run_whole_phase(self):
        self.client.login(username='admin', password='test')
        self.assert_rerun_succeeds()

    def test_collab_can_re_run_whole_phase(self):
        self.client.login(username='collab', password='test')
        self.assert_rerun_succeeds()

    def test_normal_user_cannot_re_run_whole_phase(self):
        self.client.login(username='norm', password='test')
        resp = self.client.get(reverse('phases-rerun_submissions', kwargs={'pk': self.phase.id}))
        assert resp.status_code == 403, 'Did not raise permission denied and should have'
        assert self.phase.submissions.count() == 4


# TODO: Still needs logic completed for validation
class CompetitionPhaseMigrationValidation(TestCase):
    # def setUp(self):
        # self.user = UserFactory(username='test')
        # self.competition = CompetitionFactory(created_by=self.user, id=1)
        # self.phase = PhaseFactory(competition=self.competition, auto_migrate_to_this_phase=True)

    def test_phase_serializer_checks_auto_migration(self):
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)

        with open(tmp_file.name, 'rb') as data:
            image = data

        data = [{
            "id": 1,
            "logo": image,
            "title": "It's a competition",
            "published": True,
            "created_by": "me",
            "created_when": now(),
            "phases": {
                "id": 1,
                "index": 1,
                "start": now(),
                "end": now() + timedelta(5000),
                "name": "Phase 1",
                "description": "adsf",
                "status": Phase.CURRENT,
                "auto_migrate_to_this_phase": True,
            },
        }]

        serializer = CompetitionSerializer(data=data, many=True)

        if serializer.is_valid(raise_exception=True):
            print("It's valid nice")
            assert True
        else:
            print('nope')
            assert False
