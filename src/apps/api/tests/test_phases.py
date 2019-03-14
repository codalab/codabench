import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

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

    def test_normal_user_can_re_run_whole_phase(self):
        self.client.login(username='norm', password='test')
        resp = self.client.get(reverse('phases-rerun_submissions', kwargs={'pk': self.phase.id}))
        assert resp.status_code == 403, 'Did not raise permission denied and should have'
        assert self.phase.submissions.count() == 4
