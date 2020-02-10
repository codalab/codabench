from django.urls import reverse
from rest_framework.test import APITestCase

import factories


class CompetitionLeaderboardStressTests(APITestCase):
    def setUp(self):
        self.creator = factories.UserFactory(username='creator', password='creator')
        self.other_user = factories.UserFactory(username='other_user', password='other')
        self.comp = factories.CompetitionFactory(created_by=self.creator)
        self.phase = factories.PhaseFactory(competition=self.comp)
        self.leaderboard = factories.LeaderboardFactory(competition=self.comp)
        factories.ColumnFactory(leaderboard=self.leaderboard, index=0)  # need to set index here otherwise it's seq

        for _ in range(10):
            factories.SubmissionFactory(phase=self.phase, leaderboard=self.leaderboard)

    def test_getting_many_submissions_doesnt_cause_too_many_queries(self):
        self.client.login(username='creator', password='creator')
        with self.assertNumQueries(10):
            resp = self.client.get(reverse('leaderboard-detail', args=(self.leaderboard.pk,)))
            assert resp.status_code == 200


# TODO: Test listing all leaderboards isn't a thing?


class HiddenLeaderboardTests(APITestCase):
    def setUp(self):
        self.admin = factories.UserFactory(username='admin', password='test', super_user=True)
        self.creator = factories.UserFactory(username='creator', password='test')
        self.collab = factories.UserFactory(username='collab', password='test')
        self.norm = factories.UserFactory(username='norm', password='test')
        self.comp = factories.CompetitionFactory(created_by=self.creator, collaborators=[self.collab])
        self.lb = factories.LeaderboardFactory(competition=self.comp, hidden=True)
        factories.ColumnFactory(leaderboard=self.lb, index=0)

    def get_comp(self):
        return self.client.get(reverse('competition-detail', kwargs={'pk': self.comp.id}))

    def get_leaderboard(self):
        return self.client.get(reverse('leaderboard-detail', kwargs={'pk': self.lb.id}))

    def get_leaderboards(self, resp):
        data = resp.json()
        leaderboards = data.get('leaderboards', [])
        return leaderboards

    def test_creator_can_see_hidden_leaderboard_on_competition(self):
        self.client.force_login(self.creator)
        resp = self.get_comp()
        assert resp.status_code == 200
        leaderboards = self.get_leaderboards(resp)
        assert len(leaderboards) == 1
        assert leaderboards[0]['id'] == self.lb.id

    def test_admin_can_see_hidden_leaderboard_on_competition(self):
        self.client.force_login(self.admin)
        resp = self.get_comp()
        assert resp.status_code == 200
        leaderboards = self.get_leaderboards(resp)
        assert len(leaderboards) == 1
        assert leaderboards[0]['id'] == self.lb.id

    def test_collab_can_see_hidden_leaderboard_on_competition(self):
        self.client.force_login(self.collab)
        resp = self.get_comp()
        assert resp.status_code == 200
        leaderboards = self.get_leaderboards(resp)
        assert len(leaderboards) == 1
        assert leaderboards[0]['id'] == self.lb.id

    def test_normal_user_cannot_see_hidden_leaderboard_on_competition(self):
        self.client.force_login(self.norm)
        resp = self.get_comp()
        assert resp.status_code == 200
        leaderboards = self.get_leaderboards(resp)
        assert len(leaderboards) == 0

    def test_anonymous_user_cannot_see_hidden_leaderboard_on_competition(self):
        resp = self.get_comp()
        assert resp.status_code == 200
        leaderboards = self.get_leaderboards(resp)
        assert len(leaderboards) == 0

    def test_creator_can_see_leaderboard_entries(self):
        self.client.force_login(self.creator)
        resp = self.get_leaderboard()
        assert resp.status_code == 200
        assert 'submissions' in resp.json()

    def test_admin_can_see_leaderboard_entries(self):
        self.client.force_login(self.admin)
        resp = self.get_leaderboard()
        assert resp.status_code == 200
        assert 'submissions' in resp.json()

    def test_collab_can_see_leaderboard_entries(self):
        self.client.force_login(self.collab)
        resp = self.get_leaderboard()
        assert resp.status_code == 200
        assert 'submissions' in resp.json()

    def test_normal_user_cannot_see_leaderboard_entries(self):
        self.client.force_login(self.norm)
        resp = self.get_leaderboard()
        assert resp.status_code == 403
        assert 'You do not have permission' in resp.json().get('detail')

    def test_anonymous_user_cannot_see_leaderboard_entries(self):
        resp = self.get_leaderboard()
        assert resp.status_code == 403
        assert 'Authentication credentials were not provided.' in resp.json().get('detail')
