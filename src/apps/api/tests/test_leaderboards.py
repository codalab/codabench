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


class PhaseLeaderboardRowIdTests(APITestCase):
    """Which submission ID each row of the phase leaderboard (Results tab) shows."""

    def setUp(self):
        self.creator = factories.UserFactory(username='creator', password='test')
        self.participant = factories.UserFactory(username='participant', password='test')
        self.comp = factories.CompetitionFactory(created_by=self.creator)
        self.leaderboard = factories.LeaderboardFactory()
        self.column = factories.ColumnFactory(leaderboard=self.leaderboard, index=0)
        self.task1 = factories.TaskFactory()
        self.task2 = factories.TaskFactory()

    def make_phase(self, tasks):
        """Create a phase in the test competition, using the test leaderboard and the given tasks."""
        return factories.PhaseFactory(competition=self.comp, leaderboard=self.leaderboard, tasks=tasks)

    def make_submission(self, phase, task, parent=None, has_children=False):
        """Create a submission owned by the participant.

        - Parent of a multi-task submission (has_children=True): created without scores and
          not put on the leaderboard, because the platform puts only the children on it.
        - Single-task submission or child of a parent: put on the leaderboard with one score.
        """
        submission = factories.SubmissionFactory(
            owner=self.participant,
            phase=phase,
            task=task,
            parent=parent,
            has_children=has_children,
            leaderboard=None if has_children else self.leaderboard,
        )
        if not has_children:
            factories.SubmissionScoreFactory(column=self.column, submissions=[submission])
        return submission

    def get_rows(self, phase):
        """Fetch the phase leaderboard as the creator and return its rows."""
        self.client.force_login(self.creator)
        resp = self.client.get(reverse('phases-get-leaderboard', kwargs={'pk': phase.pk}))
        assert resp.status_code == 200
        return resp.json()['submissions']

    def test_multi_task_row_shows_parent_id(self):
        """Children of a multi-task submission are shown as one row; expects the row ID to be the parent ID."""
        phase = self.make_phase(tasks=[self.task1, self.task2])
        parent = self.make_submission(phase=phase, task=None, has_children=True)
        self.make_submission(phase=phase, task=self.task1, parent=parent)
        self.make_submission(phase=phase, task=self.task2, parent=parent)

        rows = self.get_rows(phase=phase)

        assert len(rows) == 1
        assert rows[0]['id'] == parent.id
        assert {score['task_id'] for score in rows[0]['scores']} == {self.task1.id, self.task2.id}

    def test_single_task_row_shows_submission_id(self):
        """A submission without children is shown as one row; expects the row ID to be the submission's own ID."""
        phase = self.make_phase(tasks=[self.task1])
        submission = self.make_submission(phase=phase, task=self.task1)

        rows = self.get_rows(phase=phase)

        assert len(rows) == 1
        assert rows[0]['id'] == submission.id

    # TODO: add a test for a submission split into several rows by participant group queues
    # (one row per group). Decide first which ID those rows should show.
