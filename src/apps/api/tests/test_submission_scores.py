import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionScoreFactory


class SubmissionScoresTest(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.admin = UserFactory(username='admin', super_user=True)
        self.collab = UserFactory(username='collab')
        self.normal_user = UserFactory(username='norm')
        self.competition = CompetitionFactory(created_by=self.user)
        self.competition.collaborators.add(self.collab)
        self.phase = PhaseFactory(competition=self.competition)
        self.leaderboard = LeaderboardFactory(competition=self.competition)
        self.column = ColumnFactory(leaderboard=self.leaderboard, key='test')
        self.submission = self.make_submission()
        self.client = APIClient()

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.user)
        kwargs.setdefault('phase', self.phase)
        sub = SubmissionFactory(**kwargs)
        SubmissionScoreFactory(submission=sub, column=self.column)
        return sub

    def change_score(self, new_score):
        sub_score = self.submission.scores.first()
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
