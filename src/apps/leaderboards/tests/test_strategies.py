from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

import factories
from competitions.models import Submission
from leaderboards.models import Leaderboard
from leaderboards.strategies import BestModeStrategy


class BestModeStrategyTests(TestCase):
    def setUp(self):
        self.leaderboard = factories.LeaderboardFactory(submission_rule=Leaderboard.FORCE_BEST, primary_index=0)
        self.accuracy = factories.ColumnFactory(leaderboard=self.leaderboard, index=0, key='accuracy', sorting='desc')
        self.time = factories.ColumnFactory(leaderboard=self.leaderboard, index=1, key='time', sorting='desc')
        self.phase = factories.PhaseFactory(leaderboard=self.leaderboard)
        self.owner = factories.UserFactory()

    def make_submission(self, created_when, scores):
        """Create a finished submission that is not on the leaderboard, with a score for each given column"""
        submission = factories.SubmissionFactory(
            owner=self.owner,
            phase=self.phase,
            leaderboard=None,
            status=Submission.FINISHED,
            created_when=created_when,
        )
        for column, score in scores.items():
            factories.SubmissionScoreFactory(column=column, score=score, submissions=submission)
        return submission

    def put_on_leaderboard(self, submission):
        """Run the best strategy as it runs after scores are uploaded, then reload the submission"""
        BestModeStrategy().put_on_leaderboard(request=None, submission_pk=submission.pk)
        submission.refresh_from_db()

    def test_submission_missing_primary_score_is_not_chosen_as_best(self):
        """A newer submission without a primary score is put on the leaderboard; the older scored submission must stay as best"""
        older = self.make_submission(created_when=now() - timedelta(hours=1), scores={self.accuracy: 0.92, self.time: 10})
        newer = self.make_submission(created_when=now(), scores={self.time: 5})

        self.put_on_leaderboard(submission=newer)
        older.refresh_from_db()

        assert older.leaderboard == self.leaderboard
        assert newer.leaderboard is None

    def test_submission_missing_secondary_column_score_is_not_chosen_as_best(self):
        """Two submissions have the same primary score and the newer one has no secondary column score; the older one must stay as best"""
        older = self.make_submission(created_when=now() - timedelta(hours=1), scores={self.accuracy: 0.9, self.time: 10})
        newer = self.make_submission(created_when=now(), scores={self.accuracy: 0.9})

        self.put_on_leaderboard(submission=newer)
        older.refresh_from_db()

        assert older.leaderboard == self.leaderboard
        assert newer.leaderboard is None

    def test_newer_submission_with_better_score_replaces_older(self):
        """A newer submission has a better primary score; it must go on the leaderboard and the older one must be removed"""
        older = self.make_submission(created_when=now() - timedelta(hours=1), scores={self.accuracy: 0.8, self.time: 10})
        newer = self.make_submission(created_when=now(), scores={self.accuracy: 0.92, self.time: 10})

        self.put_on_leaderboard(submission=newer)
        older.refresh_from_db()

        assert newer.leaderboard == self.leaderboard
        assert older.leaderboard is None

    def test_older_submission_is_kept_on_equal_scores(self):
        """Two submissions have exactly the same scores; the older one must stay on the leaderboard"""
        older = self.make_submission(created_when=now() - timedelta(hours=1), scores={self.accuracy: 0.92, self.time: 10})
        newer = self.make_submission(created_when=now(), scores={self.accuracy: 0.92, self.time: 10})

        self.put_on_leaderboard(submission=newer)
        older.refresh_from_db()

        assert older.leaderboard == self.leaderboard
        assert newer.leaderboard is None
