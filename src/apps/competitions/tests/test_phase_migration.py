import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, SubmissionScoreFactory, \
    CompetitionParticipantFactory

User = get_user_model()


class CompetitionPhaseToPhase(TestCase):
    def setUp(self):
        self.owner = UserFactory(username='owner', super_user=True)
        self.normal_user = UserFactory(username='norm')
        self.competition = CompetitionFactory(created_by=self.owner)
        self.competition_participant = CompetitionParticipantFactory(user=self.normal_user,
                                                                     competition=self.competition)
        self.phase1 = PhaseFactory(competition=self.competition, auto_migration=True)
        self.phase2 = PhaseFactory(competition=self.competition, auto_migration=True)
        self.submission = self.make_submission()
        self.client = APIClient()

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.owner)
        kwargs.setdefault('participant', self.competition_participant)
        kwargs.setdefault('phase', self.phase1)
        sub = SubmissionFactory(**kwargs)
        SubmissionScoreFactory(submission=sub)
        return sub

    def test_migrate_submissions(self):
        self.competition.apply_phase_migration(self.phase1, self.phase2)
        assert self.phase1.submissions.count() == self.phase2.submissions.count()
