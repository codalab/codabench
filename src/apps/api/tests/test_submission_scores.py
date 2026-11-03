import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import Submission
from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionScoreFactory, TaskFactory
from leaderboards.models import Leaderboard


class SubmissionScoreChangeTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.admin = UserFactory(username='admin', super_user=True)
        self.collab = UserFactory(username='collab')
        self.normal_user = UserFactory(username='norm')
        self.competition = CompetitionFactory(created_by=self.user)
        self.competition.collaborators.add(self.collab)
        self.leaderboard = LeaderboardFactory()
        self.phase = PhaseFactory(competition=self.competition, leaderboard=self.leaderboard)
        self.column = ColumnFactory(leaderboard=self.leaderboard, key='test')
        self.submission = self.make_submission()

    def make_submission(self, create_score=True, **kwargs):
        kwargs.setdefault('owner', self.user)
        kwargs.setdefault('phase', self.phase)
        parent_sub = kwargs.pop('parent_submission', None)
        sub = SubmissionFactory(**kwargs)
        subs = [sub]
        if parent_sub:
            subs.append(parent_sub)
        if create_score:
            SubmissionScoreFactory(submissions=subs, column=self.column)
        return sub

    def change_score(self, new_score, submission=None):
        submission = submission or self.submission
        sub_score = submission.scores.first()
        data = {
            'id': sub_score.id,
            'score': new_score,
        }
        resp = self.client.patch(reverse('submission_scores-detail', kwargs={'pk': sub_score.id}), data=data)
        return resp

    def test_comp_creator_can_change_scores(self):
        self.client.login(username='test', password='test')
        new_score = self.submission.scores.first().score / 2
        self.change_score(new_score)
        assert self.submission.scores.first().score == new_score

    def test_super_user_can_change_scores(self):
        self.client.login(username='admin', password='test')
        new_score = self.submission.scores.first().score / 2
        self.change_score(new_score)
        assert self.submission.scores.first().score == new_score

    def test_collaborator_can_change_scores(self):
        self.client.login(username='collab', password='test')
        new_score = self.submission.scores.first().score / 2
        self.change_score(new_score)
        assert self.submission.scores.first().score == new_score

    def test_normal_user_cannot_change_scores(self):
        self.client.login(username='norm', password='test')
        new_score = self.submission.scores.first().score / 2
        with pytest.raises(PermissionError):
            self.change_score(new_score)
        assert self.submission.scores.first().score != new_score

    def test_changing_score_on_parent_sub_changes_child_score(self):
        self.client.login(username='admin', password='test')
        self.parent_sub = self.make_submission(create_score=False)  # so the child and parent will share score object
        self.child_sub = self.make_submission(parent_submission=self.parent_sub)
        new_score = self.parent_sub.scores.first().score / 2
        self.change_score(new_score, submission=self.parent_sub)
        assert self.child_sub.scores.first().score == new_score


class UploadSubmissionScoresTests(APITestCase):
    """Tests for the upload_submission_scores endpoint the compute worker calls to upload a submission's scores."""

    def setUp(self):
        self.participant = UserFactory(username='participant')
        self.comp = CompetitionFactory()
        self.leaderboard = LeaderboardFactory(primary_index=0, submission_rule=Leaderboard.FORCE_LATEST_MULTIPLE)
        self.task_1 = TaskFactory()
        self.task_2 = TaskFactory()
        self.phase = PhaseFactory(competition=self.comp, leaderboard=self.leaderboard, tasks=[self.task_1, self.task_2])
        self.final_score_column = ColumnFactory(leaderboard=self.leaderboard, index=0, key='final_score', sorting='desc')
        self.accuracy_column = ColumnFactory(leaderboard=self.leaderboard, index=1, key='accuracy', sorting='desc')
        self.submission = self.make_submission(task=self.task_1)

    def make_submission(self, task, parent=None):
        return SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            task=task,
            parent=parent,
            status=Submission.FINISHED,
            leaderboard=None,
        )

    def upload_scores(self, submission, scores=None, secret=None):
        data = {'secret': str(secret or submission.secret)}
        if scores is not None:
            data['scores'] = scores
        return self.client.post(f'/api/upload_submission_scores/{submission.pk}/', data=data, format='json')

    def get_scores(self, submission):
        return {score.column.key: float(score.score) for score in submission.scores.select_related('column')}

    def test_upload_creates_one_score_per_leaderboard_column(self):
        """Uploading scores returns 200 and creates one score row per leaderboard column with the uploaded values."""
        resp = self.upload_scores(submission=self.submission, scores={'final_score': 0.42, 'accuracy': 0.9})

        assert resp.status_code == 200
        assert self.submission.scores.count() == 2
        assert self.get_scores(submission=self.submission) == {'final_score': 0.42, 'accuracy': 0.9}

    def test_upload_ignores_keys_that_are_not_leaderboard_columns(self):
        """Keys that are not leaderboard columns are skipped; only the matching column gets a score row."""
        resp = self.upload_scores(submission=self.submission, scores={'final_score': 0.42, 'not_a_column': 0.5})

        assert resp.status_code == 200
        assert self.get_scores(submission=self.submission) == {'final_score': 0.42}

    def test_upload_puts_submission_on_leaderboard(self):
        """With the Force_Latest_Multiple rule, a successful upload puts the submission on the phase leaderboard."""
        self.upload_scores(submission=self.submission, scores={'final_score': 0.42, 'accuracy': 0.9})

        self.submission.refresh_from_db()
        assert self.submission.leaderboard == self.leaderboard

    def test_upload_with_wrong_secret_is_rejected(self):
        """An upload with a secret that does not match the submission returns 403 and creates no score rows."""
        resp = self.upload_scores(
            submission=self.submission,
            scores={'final_score': 0.42},
            secret='7df3600c-1234-5678-bbc8-bbe91f42d875',
        )

        assert resp.status_code == 403
        assert self.submission.scores.count() == 0

    def test_upload_without_scores_is_rejected(self):
        """An upload without a 'scores' field returns 400 and creates no score rows."""
        resp = self.upload_scores(submission=self.submission)

        assert resp.status_code == 400
        assert self.submission.scores.count() == 0

    def test_repeated_upload_is_rejected_and_adds_no_scores(self):
        """A second upload for the same submission returns 409, adds no score rows and keeps the first upload's values."""
        first_resp = self.upload_scores(submission=self.submission, scores={'final_score': 0.17, 'accuracy': 0.5})
        second_resp = self.upload_scores(submission=self.submission, scores={'final_score': 0.99, 'accuracy': 0.99})

        assert first_resp.status_code == 200
        assert second_resp.status_code == 409
        assert second_resp.data['detail'] == 'Scores have already been uploaded for this submission.'
        assert self.submission.scores.count() == 2
        assert self.get_scores(submission=self.submission) == {'final_score': 0.17, 'accuracy': 0.5}

    def test_child_upload_adds_scores_to_parent(self):
        """A child submission's upload creates the score on the child and attaches the same score to its parent."""
        parent = self.make_submission(task=self.task_1)
        child = self.make_submission(task=self.task_1, parent=parent)

        resp = self.upload_scores(submission=child, scores={'final_score': 0.42})

        assert resp.status_code == 200
        assert self.get_scores(submission=child) == {'final_score': 0.42}
        assert self.get_scores(submission=parent) == {'final_score': 0.42}

    def test_each_child_can_upload_once_when_parent_already_has_scores(self):
        """Each child can upload once even if the parent already holds another child's scores; a child's repeat upload returns 409."""
        parent = self.make_submission(task=self.task_1)
        child_1 = self.make_submission(task=self.task_1, parent=parent)
        child_2 = self.make_submission(task=self.task_2, parent=parent)

        child_1_resp = self.upload_scores(submission=child_1, scores={'final_score': 0.42})
        child_2_resp = self.upload_scores(submission=child_2, scores={'final_score': 0.3})
        child_1_repeat_resp = self.upload_scores(submission=child_1, scores={'final_score': 0.99})

        assert child_1_resp.status_code == 200
        assert child_2_resp.status_code == 200
        assert child_1_repeat_resp.status_code == 409
        assert child_1.scores.count() == 1
        assert child_2.scores.count() == 1
        assert sorted(float(score.score) for score in parent.scores.all()) == [0.3, 0.42]
