
from unittest import mock
from datetime import timedelta
from django.test import TestCase
from django.utils.timezone import now

from competitions.models import Submission, Competition, Phase
from competitions.tasks import do_phase_migrations
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, CompetitionParticipantFactory, \
    TaskFactory, LeaderboardFactory

twenty_minutes_ago = now() - timedelta(hours=0, minutes=20)
twenty_five_minutes_ago = now() - timedelta(hours=0, minutes=25)
five_minutes_ago = now() - timedelta(hours=0, minutes=5)
twenty_minutes_from_now = now() + timedelta(hours=0, minutes=20)


class PhaseToPhaseMigrationTests(TestCase):
    def setUp(self):
        self.owner = UserFactory(username='owner', super_user=True)
        self.normal_user = UserFactory(username='norm')
        self.competition = CompetitionFactory(created_by=self.owner, title="Competition One")
        self.competition_participant = CompetitionParticipantFactory(user=self.normal_user,
                                                                     competition=self.competition)
        self.leaderboard = LeaderboardFactory()
        self.phase1 = PhaseFactory(
            competition=self.competition,
            auto_migrate_to_this_phase=False,
            start=twenty_five_minutes_ago,
            end=twenty_minutes_ago,
            index=0,
            name='Phase1',
            status=Phase.CURRENT
        )

        self.phase2 = PhaseFactory(
            competition=self.competition,
            auto_migrate_to_this_phase=True,
            start=five_minutes_ago,
            end=twenty_minutes_from_now,
            index=1,
            name='Phase2',
            status=Phase.NEXT
        )

        self.phase3 = PhaseFactory(
            competition=self.competition,
            auto_migrate_to_this_phase=False,
            start=twenty_minutes_from_now,
            index=2,
            name='Phase3',
            status=Phase.FINAL
        )

        for _ in range(4):
            self.make_submission()

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.owner)
        kwargs.setdefault('participant', self.competition_participant)
        kwargs.setdefault('phase', self.phase1)
        kwargs.setdefault('status', Submission.FINISHED)
        kwargs.setdefault('leaderboard', self.leaderboard)
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
        self.mock_migration()
        assert Competition.objects.get(id=self.competition.id).is_migrating
        mock_start = self.mock_migration()
        assert not mock_start.called

    def test_competitions_with_scoring_submissions_dont_migrate(self):
        self.make_submission(status=Submission.SCORING, participant=self.competition_participant)
        self.mock_migration()
        assert self.phase1.submissions.count() != self.phase2.submissions.count()

    def test_submission_ran_after_migration_complete(self):
        self.mock_migration()
        assert not self.phase2.submissions.filter(status='None').exists()

    def test_has_been_migrated_competitions_arent_migrated(self):
        self.phase2.has_been_migrated = True
        self.phase2.save()
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
        assert Phase.objects.get(id=self.phase1.id).status == Phase.PREVIOUS
        assert Competition.objects.get(id=self.competition.id).is_migrating
        phase2 = Phase.objects.get(id=self.phase2.id)
        assert phase2.has_been_migrated
        assert phase2.status == Phase.CURRENT

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
        assert Submission.objects.get(id=self.parent_submission.id).children.exists()
        assert Submission.objects.get(id=self.parent_submission.id).children.count() > 0
        mock_sub_start = self.mock_migration()
        assert mock_sub_start.call_count == 1


class PhaseStatusTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.comp = CompetitionFactory(created_by=self.user)
        self.tasks = [TaskFactory(created_by=self.user)]
        self.base = {'competition': self.comp, 'tasks': self.tasks}
        self.phase1 = PhaseFactory.create(**self.base)
        self.phase2 = PhaseFactory.create(**self.base)
        self.phase3 = PhaseFactory.create(**self.base)

        self.before_previous = {'start': now() - timedelta(minutes=20), 'end': now() - timedelta(minutes=15)}
        self.previous = {'start': now() - timedelta(minutes=10), 'end': now() - timedelta(minutes=5)}
        self.current = {'start': now() - timedelta(minutes=1), 'end': now() + timedelta(minutes=5)}
        self.next = {'start': now() + timedelta(minutes=10), 'end': now() + timedelta(minutes=15)}
        self.after_next = {'start': now() + timedelta(minutes=20), 'end': now() + timedelta(minutes=25)}

    def set_start_end(self, phase, start, end):
        phase.start = start
        phase.end = end
        phase.save()
        return phase

    def set_phase_indexes(self, phases=None):
        phases = [self.phase1, self.phase2, self.phase3] if phases is None else phases
        for i, phase in enumerate(phases):
            phase.index = i
            phase.save(update_fields=['index'])

    def test_three_phases_updated_correctly(self):
        self.set_start_end(self.phase1, **self.current)
        self.set_start_end(self.phase2, **self.next)
        self.set_start_end(self.phase3, **self.after_next)
        do_phase_migrations()
        assert Phase.objects.get(id=self.phase1.id).status == Phase.CURRENT
        assert Phase.objects.get(id=self.phase2.id).status == Phase.NEXT
        assert Phase.objects.get(id=self.phase3.id).status is None

        self.set_start_end(self.phase1, **self.previous)
        self.set_start_end(self.phase2, **self.current)
        self.set_start_end(self.phase3, **self.next)
        do_phase_migrations()
        assert Phase.objects.get(id=self.phase1.id).status == Phase.PREVIOUS
        assert Phase.objects.get(id=self.phase2.id).status == Phase.CURRENT
        assert Phase.objects.get(id=self.phase3.id).status == Phase.NEXT

        self.set_start_end(self.phase1, **self.before_previous)
        self.set_start_end(self.phase2, **self.previous)
        self.set_start_end(self.phase3, **self.next)
        do_phase_migrations()
        assert Phase.objects.get(id=self.phase1.id).status is None
        assert Phase.objects.get(id=self.phase2.id).status == Phase.PREVIOUS
        assert Phase.objects.get(id=self.phase3.id).status == Phase.NEXT

        self.set_start_end(self.phase1, **self.before_previous)
        self.set_start_end(self.phase2, **self.previous)
        self.set_start_end(self.phase3, **self.current)
        do_phase_migrations()
        assert Phase.objects.get(id=self.phase1.id).status is None
        assert Phase.objects.get(id=self.phase2.id).status == Phase.PREVIOUS
        assert Phase.objects.get(id=self.phase3.id).status == Phase.CURRENT

    def test_five_phases_updated_correctly(self):
        self.phase4 = PhaseFactory.create(**self.base)
        self.phase5 = PhaseFactory.create(**self.base)

        self.set_start_end(self.phase1, **self.before_previous)
        self.set_start_end(self.phase2, **self.previous)
        self.set_start_end(self.phase3, **self.current)
        self.set_start_end(self.phase4, **self.next)
        self.set_start_end(self.phase5, **self.after_next)

        do_phase_migrations()

        assert Phase.objects.get(id=self.phase1.id).status is None
        assert Phase.objects.get(id=self.phase2.id).status == Phase.PREVIOUS
        assert Phase.objects.get(id=self.phase3.id).status == Phase.CURRENT
        assert Phase.objects.get(id=self.phase4.id).status == Phase.NEXT
        assert Phase.objects.get(id=self.phase5.id).status is None
