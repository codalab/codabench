from django.urls import reverse
from rest_framework.test import APITestCase

from factories import UserFactory, CompetitionFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionFactory


class CompetitionLeaderboardStressTests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.other_user = UserFactory(username='other_user', password='other')
        self.comp = CompetitionFactory(created_by=self.creator)
        self.phase = PhaseFactory(competition=self.comp)
        self.leaderboard = LeaderboardFactory(competition=self.comp)
        ColumnFactory(leaderboard=self.leaderboard, index=0)  # need to set index here otherwise it's seq

        for _ in range(10):
            SubmissionFactory(phase=self.phase, leaderboard=self.leaderboard)

    def test_getting_many_submissions_doesnt_cause_too_many_queries(self):
        self.client.login(username='creator', password='creator')
        with self.assertNumQueries(7):
            resp = self.client.get(reverse('leaderboard-detail', args=(self.leaderboard.pk,)))
            assert resp.status_code == 200


# TODO: Test leaderboard viewset permissions!
# TODO: Test listing all leaderboards isn't a thing?
