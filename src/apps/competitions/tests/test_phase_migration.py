import datetime
import time

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework.test import APIClient

from competitions.tasks import do_phase_migrations
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, SubmissionScoreFactory, \
    CompetitionParticipantFactory

User = get_user_model()


class CompetitionPhaseToPhase(TestCase):
    def setUp(self):
        self.owner = UserFactory(username='owner', super_user=True)
        self.normal_user = UserFactory(username='norm')
        self.normal_user2 = UserFactory(username='norm2')
        self.normal_user3 = UserFactory(username='norm3')
        self.competition = CompetitionFactory(created_by=self.owner)
        self.competition_participant = CompetitionParticipantFactory(user=self.normal_user,
                                                                     competition=self.competition)
        self.competition_participant2 = CompetitionParticipantFactory(user=self.normal_user2,
                                                                      competition=self.competition)
        self.competition_participant3 = CompetitionParticipantFactory(user=self.normal_user3,
                                                                      competition=self.competition)
        self.phase1 = PhaseFactory(competition=self.competition, auto_migration=True, status='Current')
        self.phase2 = PhaseFactory(competition=self.competition, auto_migration=True, status='Next')
        self.phase3 = PhaseFactory(competition=self.competition, auto_migration=False, status='Final')
        self.submission = self.make_submission()
        self.submission2 = self.make_submission(participant=self.competition_participant2)
        self.client = APIClient()

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.owner)
        kwargs.setdefault('participant', self.competition_participant)
        kwargs.setdefault('phase', self.phase1)
        kwargs.setdefault('status', 'None')
        sub = SubmissionFactory(**kwargs)
        SubmissionScoreFactory(submission=sub)
        return sub

    def test_migrate_submissions(self):
        """
        Determine whether all submissions in phase1 end up in phase2
        :return:
        """
        assert self.phase2.submissions.count() == 0
        self.competition.apply_phase_migration(self.phase1, self.phase2)
        assert self.phase1.submissions.count() == self.phase2.submissions.count()

    def test_migrating_competitions(self):
        """
        Make sure competitions which are already migrating do not migrate.
        :return:
        """
        self.competition.is_migrating = True
        self.competition.apply_phase_migration(self.phase1, self.phase2)
        self.assertFalse(self.phase1.submissions.count() == self.phase2.submissions.count())

    def test_migrating_scoring_submissions(self):
        """
        Test to see if there are submissions being scored currently. If there are, delay migration.
        :return:
        """
        self.submission3 = self.make_submission(status='Scoring', participant=self.competition_participant3)
        self.competition.apply_phase_migration(self.phase1, self.phase2)
        self.assertFalse(self.phase1.submissions.count() == self.phase2.submissions.count())

    def test_auto_migrate(self):
        """
        Test auto-migration is triggered by new phase starting
        :return:
        """
        self.phase1.end = now() - datetime.timedelta(hours=0, minutes=20)
        self.phase2.start = now() - datetime.timedelta(hours=0, minutes=5)
        self.phase1.save()
        self.phase2.save()
        do_phase_migrations.apply()

        assert self.phase1.submissions.count() == self.phase2.submissions.count()

    def test_submission_ran_after_migration(self):
        """
        Test if the submissions are being run after they are migrated from the previous phase.
        :return:
        """

        self.phase1.end = now() - datetime.timedelta(hours=0, minutes=20)
        self.phase2.start = now() - datetime.timedelta(hours=0, minutes=5)
        self.phase1.save()
        self.phase2.save()
        do_phase_migrations.apply()

        for submission in self.phase2.submissions.all():
            assert(submission.status is not 'None')
