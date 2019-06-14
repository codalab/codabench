import datetime

from django.test import TestCase
from django.utils.timezone import now

from competitions.tasks import do_phase_migrations
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, SubmissionScoreFactory, \
    CompetitionParticipantFactory

twenty_minutes_ago = now() - datetime.timedelta(hours=0, minutes=20)
five_minutes_ago = now() - datetime.timedelta(hours=0, minutes=5)


class CompetitionPhaseToPhase(TestCase):
    def setUp(self):
        # Competition Owner
        self.owner = UserFactory(username='owner', super_user=True)

        # Users
        self.normal_user = UserFactory(username='norm')
        self.normal_user2 = UserFactory(username='norm2')
        self.normal_user3 = UserFactory(username='norm3')

        # Competitions
        self.competition = CompetitionFactory(created_by=self.owner)
        self.competition2 = CompetitionFactory(created_by=self.owner)

        # Competition Participants
        self.competition_participant = CompetitionParticipantFactory(user=self.normal_user,
                                                                     competition=self.competition)
        self.competition_participant2 = CompetitionParticipantFactory(user=self.normal_user2,
                                                                      competition=self.competition)
        self.competition_participant3 = CompetitionParticipantFactory(user=self.normal_user3,
                                                                      competition=self.competition)

        # Competition 1 Phases
        self.phase1 = PhaseFactory(competition=self.competition, auto_migrate_to_this_phase=False,
                                   end=twenty_minutes_ago, index=1, name='Phase1')
        self.phase2 = PhaseFactory(competition=self.competition, auto_migrate_to_this_phase=True,
                                   start=five_minutes_ago, index=2, name='Phase2')
        self.phase3 = PhaseFactory(competition=self.competition, auto_migrate_to_this_phase=False,
                                   index=3, name='Phase3')

        # Competition 2 Phases
        self.phase1_competition2 = PhaseFactory(competition=self.competition2, auto_migrate_to_this_phase=False,
                                                end=twenty_minutes_ago, has_been_migrated=True,
                                                index=1)
        self.phase2_competition2 = PhaseFactory(competition=self.competition2, auto_migrate_to_this_phase=True,
                                                start=five_minutes_ago, index=2)

        # Competition 1 Submissions
        self.submission = self.make_submission()
        self.submission2 = self.make_submission(participant=self.competition_participant2)

        # Competition 2 Submissions
        self.submission1_competition2 = self.make_submission(phase=self.phase1_competition2,
                                                             participant=self.competition_participant)
        self.submission2_competition2 = self.make_submission(phase=self.phase1_competition2,
                                                             participant=self.competition_participant3)

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.owner)
        kwargs.setdefault('participant', self.competition_participant)
        kwargs.setdefault('phase', self.phase1)
        kwargs.setdefault('status', 'None')
        sub = SubmissionFactory(**kwargs)
        SubmissionScoreFactory(submission=sub)
        return sub

    def test_migrate_submissions(self):
        assert self.phase2.submissions.count() == 0
        do_phase_migrations.apply()
        assert self.phase1.submissions.count() == self.phase2.submissions.count()

    def test_currently_migrating_competitions_dont_migrate(self):
        self.competition.is_migrating = True
        self.competition.save()
        do_phase_migrations.apply()
        self.assertFalse(self.phase1.submissions.count() == self.phase2.submissions.count())

    def test_competitions_with_scoring_submissions_dont_migrate(self):
        self.submission3 = self.make_submission(status='Scoring', participant=self.competition_participant3)
        do_phase_migrations.apply()
        self.assertFalse(self.phase1.submissions.count() == self.phase2.submissions.count())

    def test_auto_migration_at_new_phase(self):
        do_phase_migrations.apply()
        assert self.phase1.submissions.count() == self.phase2.submissions.count()

    def test_submission_ran_after_migration_complete(self):
        do_phase_migrations.apply()
        for submission in self.phase2.submissions.all():
            assert (submission.status is not 'None')

    def test_has_been_migrated_competitions_arent_migrated(self):
        assert self.phase2_competition2.submissions.count() == 0
        do_phase_migrations.apply()
        self.assertFalse(self.phase1_competition2.submissions.count() == self.phase2_competition2.submissions.count())

    def test_prevent_migration_to_auto_migrate_to_the_phase_is_false(self):
        assert self.phase2.submissions.count() == 0
        assert self.phase3.submissions.count() == 0
        do_phase_migrations.apply()
        assert self.phase1.submissions.count() == self.phase2.submissions.count()
        assert self.phase1.submissions.count() != self.phase3.submissions.count()
        assert self.phase2.submissions.count() != self.phase3.submissions.count()
