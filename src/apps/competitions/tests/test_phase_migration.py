import datetime
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now

from competitions.models import Submission, Competition, Phase
from competitions.tasks import do_phase_migrations
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, SubmissionScoreFactory, \
    CompetitionParticipantFactory

twenty_minutes_ago = now() - datetime.timedelta(hours=0, minutes=20)
five_minutes_ago = now() - datetime.timedelta(hours=0, minutes=5)


class CompetitionPhaseToPhase(TestCase):
    def setUp(self):
        self.owner = UserFactory(username='owner', super_user=True)
        self.normal_user = UserFactory(username='norm')
        self.competition = CompetitionFactory(created_by=self.owner, title="Competition One")
        self.competition_participant = CompetitionParticipantFactory(user=self.normal_user,
                                                                     competition=self.competition)
        self.phase1 = PhaseFactory(competition=self.competition, auto_migrate_to_this_phase=False,
                                   end=twenty_minutes_ago, index=1, name='Phase1')
        self.phase2 = PhaseFactory(competition=self.competition, auto_migrate_to_this_phase=True,
                                   start=five_minutes_ago, index=2, name='Phase2')
        self.phase3 = PhaseFactory(competition=self.competition, auto_migrate_to_this_phase=False,
                                   index=3, name='Phase3')

        for _ in range(4):
            self.make_submission()

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.owner)
        kwargs.setdefault('participant', self.competition_participant)
        kwargs.setdefault('phase', self.phase1)
        kwargs.setdefault('status', 'None')
        sub = SubmissionFactory(**kwargs)
        return sub

    def mock_migration(self):
        with mock.patch('competitions.models.Submission.start') as submission_start:
            do_phase_migrations()
            return submission_start

    def test_migrate_submissions(self):
        assert not self.phase2.submissions.exists()
        mock_start = self.mock_migration()
        assert mock_start.call_count == self.phase1.submissions.count()
        assert self.phase1.submissions.count() == self.phase2.submissions.count()

    def test_currently_migrating_competitions_dont_migrate(self):
        self.competition.is_migrating = True
        self.competition.save()
        self.mock_migration()
        assert self.phase1.submissions.count() != self.phase2.submissions.count()

    def test_competitions_with_scoring_submissions_dont_migrate(self):
        self.make_submission(status=Submission.SCORING, participant=self.competition_participant)
        self.mock_migration()
        assert self.phase1.submissions.count() != self.phase2.submissions.count()

    def test_submission_ran_after_migration_complete(self):
        self.mock_migration()
        assert not self.phase2.submissions.filter(status='None').exists()

    def test_has_been_migrated_competitions_arent_migrated(self):
        self.phase1.has_been_migrated = True
        self.phase1.save()
        assert not self.phase2.submissions.exists()
        self.mock_migration()
        assert self.phase1.submissions.count() != self.phase2.submissions.count()

    def test_prevent_migration_to_auto_migrate_to_the_phase_is_false(self):
        assert not self.phase2.submissions.exists()
        assert not self.phase3.submissions.exists()
        self.mock_migration()
        assert self.phase1.submissions.count() == self.phase2.submissions.count()
        assert self.phase1.submissions.count() != self.phase3.submissions.count()
        assert self.phase2.submissions.count() != self.phase3.submissions.count()

    def test_all_submissions_migrated_before_changing_phase_status(self):
        self.mock_migration()
        self.phase1.status = Phase.PREVIOUS
        self.phase1.save()
        assert Competition.objects.get(id=self.competition.id).is_migrating

        self.mock_migration()
        assert Competition.objects.get(id=self.competition.id).is_migrating

        self.phase2.submissions.update(status='Finished')
        self.mock_migration()
        assert not Competition.objects.get(id=self.phase1.competition.id).is_migrating

        mock_start = self.mock_migration()
        assert mock_start.call_count == 0

    def test_only_parent_submissions_migrated(self):
        self.parent_submission = self.make_submission()
        self.phase1.submissions.exclude(id=self.parent_submission.id).update(parent=self.parent_submission)
        mock_sub_start = self.mock_migration()
        assert mock_sub_start.call_count == 1
