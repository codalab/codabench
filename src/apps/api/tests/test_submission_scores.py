import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionScoreFactory


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
