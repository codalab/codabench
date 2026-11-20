from django.urls import reverse
from rest_framework.test import APITestCase

import factories
from leaderboards.models import Column
from profiles.models import CustomGroup


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


class HiddenColumnScoreTests(APITestCase):
    """
    Column.hidden is meant to hide a score from everyone
    viewing the leaderboard (e.g. so participants can't tune submissions
    against it), so a hidden column's score must never appear in the
    leaderboard-detail (`/api/leaderboards/<id>/`) response, for any viewer
    - anonymous, logged-in, or organizer/admin alike - consistent with how
    the `columns` metadata list already filters hidden columns out.
    (Previously `submissions[*].scores` was built from a query with no
    hidden-column filter, so a hidden column's score leaked through even
    though the UI never rendered a column for it.)
    """

    def setUp(self):
        self.creator = factories.UserFactory(username='hcs_creator', password='test')
        self.admin = factories.UserFactory(username='hcs_admin', password='test', super_user=True)
        self.normal_user = factories.UserFactory(username='hcs_normal', password='test')
        self.comp = factories.CompetitionFactory(created_by=self.creator)
        self.leaderboard = factories.LeaderboardFactory(hidden=False, primary_index=0)
        self.phase = factories.PhaseFactory(competition=self.comp, leaderboard=self.leaderboard)

        self.visible_column = factories.ColumnFactory(
            leaderboard=self.leaderboard, index=0, key='visible_col', hidden=False)
        self.hidden_column = factories.ColumnFactory(
            leaderboard=self.leaderboard, index=1, key='hidden_col', hidden=True)

        self.submission = factories.SubmissionFactory(phase=self.phase, leaderboard=self.leaderboard)
        factories.SubmissionScoreFactory(submissions=[self.submission], column=self.visible_column)
        factories.SubmissionScoreFactory(submissions=[self.submission], column=self.hidden_column)

    def get_leaderboard(self):
        return self.client.get(reverse('leaderboard-detail', kwargs={'pk': self.leaderboard.id}))

    def score_column_keys(self, resp):
        submissions = resp.json()['submissions']
        assert len(submissions) == 1
        return {score['column_key'] for score in submissions[0]['scores']}

    def test_anonymous_user_does_not_see_hidden_column_score(self):
        """
        An anonymous (unauthenticated) GET on leaderboard-detail must not
        include the hidden column's score in the submission's scores array.
        Expected: only the visible column's score is returned.
        """
        resp = self.get_leaderboard()
        assert resp.status_code == 200
        keys = self.score_column_keys(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys

    def test_normal_authenticated_user_does_not_see_hidden_column_score(self):
        """
        A logged-in user with no organizer/collaborator/admin relationship to
        the competition must not see the hidden column's score via
        leaderboard-detail either. Expected: only the visible column's score
        is returned.
        """
        self.client.force_login(self.normal_user)
        resp = self.get_leaderboard()
        assert resp.status_code == 200
        keys = self.score_column_keys(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys

    def test_competition_creator_does_not_see_hidden_column_score(self):
        """
        For consistency with the columns metadata (which already filters out
        hidden columns for everyone, organizers included), the competition
        creator must not see the hidden column's score via leaderboard-detail
        either. Expected: only the visible column's score is returned.
        """
        self.client.force_login(self.creator)
        resp = self.get_leaderboard()
        assert resp.status_code == 200
        keys = self.score_column_keys(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys

    def test_superuser_does_not_see_hidden_column_score(self):
        """
        Even a superuser/site-admin must not see the hidden column's score
        via this endpoint, for the same consistency reason. Expected: only
        the visible column's score is returned.
        """
        self.client.force_login(self.admin)
        resp = self.get_leaderboard()
        assert resp.status_code == 200
        keys = self.score_column_keys(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys


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

    def make_submission(self, phase, task, parent=None, has_children=False, queue=None):
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
            queue=queue,
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

    def test_group_queue_rows_show_parent_id(self):
        """Children of a submission sent to several group queues are shown as one row per group;
        expects every row ID to be the parent ID, with the group telling the rows apart."""
        phase = self.make_phase(tasks=[self.task1])
        queue_a = factories.QueueFactory(name='comp__GroupA')
        queue_b = factories.QueueFactory(name='comp__GroupB')
        parent = self.make_submission(phase=phase, task=None, has_children=True)
        self.make_submission(phase=phase, task=self.task1, parent=parent, queue=queue_a)
        self.make_submission(phase=phase, task=self.task1, parent=parent, queue=queue_b)

        rows = self.get_rows(phase=phase)

        assert len(rows) == 2
        assert [row['id'] for row in rows] == [parent.id, parent.id]
        assert {row['queue_name'] for row in rows} == {f'{parent.id}_GroupA', f'{parent.id}_GroupB'}


class PhaseLeaderboardResponseTests(APITestCase):
    """Content of the phase leaderboard response (Results tab, `phases/<pk>/get_leaderboard/`)."""

    def setUp(self):
        self.creator = factories.UserFactory(username='plr_creator', password='test')
        self.participant = factories.UserFactory(username='plr_participant', password='test')
        self.comp = factories.CompetitionFactory(created_by=self.creator)
        self.leaderboard = factories.LeaderboardFactory(primary_index=0)
        self.column = factories.ColumnFactory(
            leaderboard=self.leaderboard, index=0, key='accuracy', sorting='desc', precision=2)
        self.task = factories.TaskFactory()
        self.phase = factories.PhaseFactory(competition=self.comp, leaderboard=self.leaderboard, tasks=[self.task])

    def make_submission(self, owner=None, task=None, parent=None, has_children=False, queue=None, score=0.5, **kwargs):
        """Create a submission (on the leaderboard with one `accuracy` score, unless it is a parent)."""
        submission = factories.SubmissionFactory(
            owner=owner or self.participant,
            phase=self.phase,
            task=None if has_children else (task or self.task),
            parent=parent,
            has_children=has_children,
            leaderboard=None if has_children else self.leaderboard,
            queue=queue,
            **kwargs,
        )
        if not has_children:
            factories.SubmissionScoreFactory(column=self.column, submissions=[submission], score=score)
        return submission

    def get_leaderboard(self):
        self.client.force_login(self.creator)
        resp = self.client.get(reverse('phases-get-leaderboard', kwargs={'pk': self.phase.pk}))
        assert resp.status_code == 200
        return resp.json()

    def test_response_content_for_a_single_submission(self):
        """Expects the top-level fields, the task headers and one row with a score rounded to the column precision."""
        submission = self.make_submission(score=0.123456)

        data = self.get_leaderboard()

        assert data['title'] == self.leaderboard.title
        assert data['id'] == self.phase.id
        assert data['primary_index'] == 0
        assert data['fact_sheet_keys'] is None
        assert data['has_group_queues'] is False
        assert data['count'] == 1
        assert data['page_size'] == '50'
        assert data['next'] is None
        assert data['previous'] is None
        assert data['allowed_page_sizes'] == [50, 100, 500, 'all']

        assert len(data['tasks']) == 1
        task = data['tasks'][0]
        assert (task['id'], task['name'], task['colWidth']) == (self.task.id, self.task.name, 1)
        assert [col['key'] for col in task['columns']] == ['accuracy']

        assert len(data['submissions']) == 1
        row = data['submissions'][0]
        assert row['id'] == submission.id
        assert row['owner'] == (self.participant.display_name or self.participant.username)
        assert row['queue_name'] is None
        assert row['organization'] is None
        assert row['slug_url'] == self.participant.slug_url
        assert row['detailed_results'] == [{'task': self.task.id, 'id': submission.id}]
        assert len(row['scores']) == 1
        assert row['scores'][0]['score'] == '0.12'
        assert row['scores'][0]['task_id'] == self.task.id
        assert row['scores'][0]['column_key'] == 'accuracy'

    def test_fact_sheet_keys_only_list_questions_shown_on_leaderboard(self):
        """Expects [key, title] pairs for the fact sheet questions marked `is_on_leaderboard`."""
        self.comp.fact_sheet = {
            'q1': {'key': 'model', 'title': 'Model', 'is_on_leaderboard': 'true'},
            'q2': {'key': 'secret', 'title': 'Secret', 'is_on_leaderboard': 'false'},
        }
        self.comp.save()

        data = self.get_leaderboard()

        assert data['fact_sheet_keys'] == [['model', 'Model']]

    def test_multi_task_row_lists_detailed_results_of_every_child(self):
        """Children of a multi-task submission form one row; expects one detailed result per child."""
        task2 = factories.TaskFactory()
        self.phase.tasks.add(task2)
        parent = self.make_submission(has_children=True)
        child1 = self.make_submission(task=self.task, parent=parent)
        child2 = self.make_submission(task=task2, parent=parent)

        data = self.get_leaderboard()

        assert len(data['submissions']) == 1
        row = data['submissions'][0]
        assert row['id'] == parent.id
        assert sorted(row['detailed_results'], key=lambda d: d['id']) == [
            {'task': self.task.id, 'id': child1.id},
            {'task': task2.id, 'id': child2.id},
        ]
        assert data['has_group_queues'] is False

    def test_children_on_the_same_task_without_queue_get_one_row_each(self):
        """Several children of one parent on the same task, with no queue: expects one row per child."""
        parent = self.make_submission(has_children=True)
        self.make_submission(parent=parent)
        self.make_submission(parent=parent)

        data = self.get_leaderboard()

        assert [row['id'] for row in data['submissions']] == [parent.id, parent.id]
        assert [row['queue_name'] for row in data['submissions']] == [None, None]
        assert data['has_group_queues'] is True

    def test_group_label_comes_from_the_participant_group(self):
        """Participant group linked to the submission queue: expects the row group label to be the group name."""
        queue = factories.QueueFactory(name='comp__queue-name')
        group = CustomGroup.objects.create(name='comp__Team', queue=queue)
        group.user_set.add(self.participant)
        self.comp.participant_groups.add(group)
        submission = self.make_submission(queue=queue)

        data = self.get_leaderboard()

        assert [row['queue_name'] for row in data['submissions']] == [f'{submission.id}_Team']
        assert data['has_group_queues'] is True

    def test_queue_label_used_when_no_participant_group(self):
        """Submission queue not linked to a group of the owner: expects the row group label to be the queue name."""
        queue = factories.QueueFactory(name='comp__GroupA')
        submission = self.make_submission(queue=queue)

        data = self.get_leaderboard()

        assert [row['queue_name'] for row in data['submissions']] == [f'{submission.id}_GroupA']
        assert data['has_group_queues'] is True

    def test_owners_whose_name_and_id_look_alike_get_separate_rows(self):
        """Owners `u1` (submission 2900) and `u12` (submission 900): expects two rows, not one merged row."""
        self.make_submission(owner=factories.UserFactory(username='u1'), id=2900)
        self.make_submission(owner=factories.UserFactory(username='u12'), id=900)

        data = self.get_leaderboard()

        assert sorted(row['id'] for row in data['submissions']) == [900, 2900]

    def test_average_rank_uses_scores_before_rounding(self):
        """Scores 0.9004 and 0.9001 both show as 0.9; expects average ranks 1 and 2, not a tie at 1.5."""
        factories.ColumnFactory(
            leaderboard=self.leaderboard, index=1, key='avg_rank', sorting='asc', precision=2,
            computation=Column.AVERAGE_RANK, computation_indexes='0')
        self.column.precision = 1
        self.column.save()
        best = self.make_submission(score=0.9004)
        second = self.make_submission(score=0.9001)

        data = self.get_leaderboard()

        scores = {
            row['id']: {score['column_key']: score['score'] for score in row['scores']}
            for row in data['submissions']
        }
        assert scores[best.id] == {'accuracy': '0.9', 'avg_rank': '1.0'}
        assert scores[second.id] == {'accuracy': '0.9', 'avg_rank': '2.0'}
