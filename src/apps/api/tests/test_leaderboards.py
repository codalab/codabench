from django.urls import reverse
from rest_framework.test import APITestCase

import factories


class CompetitionLeaderboardStressTests(APITestCase):
    def setUp(self):
        self.creator = factories.UserFactory(username='creator', password='creator')
        self.other_user = factories.UserFactory(username='other_user', password='other')
        self.comp = factories.CompetitionFactory(created_by=self.creator)
        self.leaderboard = factories.LeaderboardFactory()
        self.phase = factories.PhaseFactory(competition=self.comp, leaderboard=self.leaderboard)
        factories.ColumnFactory(leaderboard=self.leaderboard, index=0)  # need to set index here otherwise it's seq

        for _ in range(10):
            factories.SubmissionFactory(phase=self.phase, leaderboard=self.leaderboard)

    def test_getting_many_submissions_doesnt_cause_too_many_queries(self):
        self.client.login(username='creator', password='creator')
        with self.assertNumQueries(11):
            resp = self.client.get(reverse('leaderboard-detail', args=(self.leaderboard.pk,)))
            assert resp.status_code == 200


class LeaderboardTest(APITestCase):
    def setUp(self):
        leaderboard1 = factories.LeaderboardFactory()
        leaderboard2 = factories.LeaderboardFactory()
        _ = factories.ColumnFactory(leaderboard=leaderboard1, index=0)
        _ = factories.ColumnFactory(leaderboard=leaderboard2, index=0)

    def test_get_all_leaderboards(self):
        url = reverse('leaderboard-list')
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data == []


class HiddenLeaderboardTests(APITestCase):
    def setUp(self):
        self.admin = factories.UserFactory(username='admin', password='test', super_user=True)
        self.creator = factories.UserFactory(username='creator', password='test')
        self.collab = factories.UserFactory(username='collab', password='test')
        self.norm = factories.UserFactory(username='norm', password='test')
        self.comp = factories.CompetitionFactory(created_by=self.creator, collaborators=[self.collab])
        self.lb = factories.LeaderboardFactory(hidden=True)
        self.phase = factories.PhaseFactory(competition=self.comp, leaderboard=self.lb)
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
        self.lb.hidden = False
        self.lb.save()
        resp = self.get_leaderboard()
        assert resp.status_code == 200


class LeaderboardMissingScoreOrderingTests(APITestCase):
    def setUp(self):
        self.creator = factories.UserFactory(username='creator', password='creator')
        self.comp = factories.CompetitionFactory(created_by=self.creator)
        self.leaderboard = factories.LeaderboardFactory(primary_index=0)
        self.phase = factories.PhaseFactory(competition=self.comp, leaderboard=self.leaderboard)
        self.accuracy_column = factories.ColumnFactory(leaderboard=self.leaderboard, index=0, key='accuracy', sorting='desc')
        self.time_column = factories.ColumnFactory(leaderboard=self.leaderboard, index=1, key='time', sorting='asc')

        self.sub_low = self.make_submission(accuracy=0.8, time=10)
        self.sub_high = self.make_submission(accuracy=0.9, time=12)
        # Submission without an accuracy score, shown as n/a on the leaderboard
        self.sub_missing = self.make_submission(accuracy=None, time=5)

    def make_submission(self, accuracy, time):
        submission = factories.SubmissionFactory(phase=self.phase, leaderboard=self.leaderboard)
        if accuracy is not None:
            factories.SubmissionScoreFactory(submissions=submission, column=self.accuracy_column, score=accuracy)
        factories.SubmissionScoreFactory(submissions=submission, column=self.time_column, score=time)
        return submission

    def get_phase_leaderboard_ids(self):
        self.client.force_login(self.creator)
        resp = self.client.get(reverse('phases-get-leaderboard', kwargs={'pk': self.phase.pk}))
        assert resp.status_code == 200
        return [submission['id'] for submission in resp.json()['submissions']]

    def get_leaderboard_entries_ids(self):
        self.client.force_login(self.creator)
        resp = self.client.get(reverse('leaderboard-detail', kwargs={'pk': self.leaderboard.pk}))
        assert resp.status_code == 200
        return [submission['id'] for submission in resp.json()['submissions']]

    def test_missing_primary_score_ranked_last_on_phase_leaderboard_desc(self):
        """Phase leaderboard with primary column sorted desc: expected order is 0.9, 0.8, then the submission without a primary score."""
        assert self.get_phase_leaderboard_ids() == [self.sub_high.id, self.sub_low.id, self.sub_missing.id]

    def test_missing_primary_score_ranked_last_on_phase_leaderboard_asc(self):
        """Phase leaderboard with primary column sorted asc: expected order is 0.8, 0.9, then the submission without a primary score."""
        self.accuracy_column.sorting = 'asc'
        self.accuracy_column.save()
        assert self.get_phase_leaderboard_ids() == [self.sub_low.id, self.sub_high.id, self.sub_missing.id]

    def test_missing_primary_score_ranked_last_on_leaderboard_entries_desc(self):
        """Leaderboard entries endpoint with primary column sorted desc: expected order is 0.9, 0.8, then the submission without a primary score."""
        assert self.get_leaderboard_entries_ids() == [self.sub_high.id, self.sub_low.id, self.sub_missing.id]

    def test_missing_primary_score_ranked_last_on_leaderboard_entries_asc(self):
        """Leaderboard entries endpoint with primary column sorted asc: expected order is 0.8, 0.9, then the submission without a primary score."""
        self.accuracy_column.sorting = 'asc'
        self.accuracy_column.save()
        assert self.get_leaderboard_entries_ids() == [self.sub_low.id, self.sub_high.id, self.sub_missing.id]
