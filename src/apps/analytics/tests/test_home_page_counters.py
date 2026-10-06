from unittest import mock

from django.test import TestCase

from analytics.tasks import update_home_page_counters
from competitions.models import CompetitionParticipant
from factories import CompetitionFactory, UserFactory
from profiles.models import User


class HomePageCountersTaskTests(TestCase):

    def setUp(self):
        # Organizers: creator_a, creator_b and collaborator (also auto-approved participants)
        self.creator_a = UserFactory()
        self.creator_b = UserFactory()
        self.collaborator = UserFactory()
        self.competition = CompetitionFactory(created_by=self.creator_a, published=True)
        CompetitionFactory(created_by=self.creator_b, published=False, collaborators=[self.collaborator])

        # Participants: one approved, one pending, one approved but deleted
        self.approved = UserFactory()
        self.pending = UserFactory()
        self.deleted = UserFactory()
        CompetitionParticipant.objects.create(user=self.approved, competition=self.competition, status='approved')
        CompetitionParticipant.objects.create(user=self.pending, competition=self.competition, status='pending')
        CompetitionParticipant.objects.create(user=self.deleted, competition=self.competition, status='approved')
        User.objects.filter(pk=self.deleted.pk).update(is_deleted=True)

        # A user with no competitions at all
        UserFactory()

    def run_task(self):
        """Run the daily task without writing the real file and return the data it would write."""
        with mock.patch('builtins.open', mock.mock_open()), mock.patch('analytics.tasks.json.dump') as dump:
            update_home_page_counters()
        return dump.call_args.args[0]

    def test_counts(self):
        """
        Uses 2 competitions (1 published), 3 organizers (2 creators and a collaborator),
        an approved, a pending and a deleted participant, and one inactive user.
        Expects 1 public competition, 6 users (deleted left out), 3 organizers and
        4 participants (the 3 organizers are auto-approved, plus the approved user;
        pending and deleted are left out).
        """
        counters = self.run_task()

        assert counters["public_competitions"] == 1
        assert counters["users"] == 6
        assert counters["organizers"] == 3
        assert counters["participants"] == 4
        assert counters["submissions"] == 0

    def test_organizer_with_many_competitions_counted_once(self):
        """
        Creates 2 more competitions for an existing organizer.
        Expects the organizer count to stay at 3.
        """
        CompetitionFactory(created_by=self.creator_a)
        CompetitionFactory(created_by=self.creator_a)

        assert self.run_task()["organizers"] == 3

    def test_writes_all_counters(self):
        """
        Runs the daily task.
        Expects the written data to have every counter plus last_updated.
        """
        assert set(self.run_task().keys()) == {
            "public_competitions", "users", "organizers", "participants", "submissions", "last_updated"
        }
