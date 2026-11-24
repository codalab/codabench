from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from factories import UserFactory, PhaseFactory, LeaderboardFactory, ColumnFactory, SubmissionFactory, SubmissionScoreFactory
from competitions.models import Submission
from leaderboards.models import Leaderboard
from leaderboards.strategies import BestModeStrategy

from rest_framework.test import APITestCase


class BestModeStrategyTests(TestCase):
    def setUp(self):
        self.leaderboard = LeaderboardFactory(submission_rule=Leaderboard.FORCE_BEST, primary_index=0)
        self.accuracy = ColumnFactory(leaderboard=self.leaderboard, index=0, key='accuracy', sorting='desc')
        self.time = ColumnFactory(leaderboard=self.leaderboard, index=1, key='time', sorting='desc')
        self.phase = PhaseFactory(leaderboard=self.leaderboard)
        self.owner = UserFactory()

    def make_submission(self, created_when, scores, status=Submission.FINISHED, **kwargs):
        """Create a submission that is not on the leaderboard (finished by default), with a score for each given column"""
        submission = SubmissionFactory(
            owner=self.owner,
            phase=self.phase,
            leaderboard=None,
            status=status,
            created_when=created_when,
            **kwargs,
        )
        for column, score in scores.items():
            SubmissionScoreFactory(column=column, score=score, submissions=submission)
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

    def test_first_submission_still_scoring_is_put_on_leaderboard(self):
        """The compute worker uploads scores before marking the submission Finished; a first submission must still go on the leaderboard"""
        scoring = self.make_submission(created_when=now(), scores={self.accuracy: 0.8, self.time: 10}, status=Submission.SCORING)

        self.put_on_leaderboard(submission=scoring)

        assert scoring.leaderboard == self.leaderboard

    def test_better_submission_still_scoring_replaces_finished_one(self):
        """A newer submission whose scores are being uploaded (not Finished yet) with a better score replaces the finished one"""
        older = self.make_submission(created_when=now() - timedelta(hours=1), scores={self.accuracy: 0.8, self.time: 10})
        newer = self.make_submission(created_when=now(), scores={self.accuracy: 0.92, self.time: 10}, status=Submission.SCORING)

        self.put_on_leaderboard(submission=newer)
        older.refresh_from_db()

        assert newer.leaderboard == self.leaderboard
        assert older.leaderboard is None

    def test_other_unfinished_submissions_are_not_candidates(self):
        """Only the submission being scored is a candidate before it is Finished; another failed submission with a better score is not"""
        failed = self.make_submission(created_when=now() - timedelta(hours=1), scores={self.accuracy: 0.99, self.time: 10}, status=Submission.FAILED)
        scoring = self.make_submission(created_when=now(), scores={self.accuracy: 0.8, self.time: 10}, status=Submission.SCORING)

        self.put_on_leaderboard(submission=scoring)
        failed.refresh_from_db()

        assert scoring.leaderboard == self.leaderboard
        assert failed.leaderboard is None

    def test_parent_is_candidate_only_when_last_child_is_scored(self):
        """A multi-task parent is a candidate only once every other child is done, as it is Finished as soon as the last child is"""
        parent = self.make_submission(created_when=now(), scores={}, status=Submission.RUNNING, has_children=True)
        first_child = self.make_submission(created_when=now(), scores={}, status=Submission.SCORING, parent=parent)
        second_child = self.make_submission(created_when=now(), scores={}, status=Submission.RUNNING, parent=parent)

        assert BestModeStrategy()._candidate_pks(first_child) == [first_child.pk]

        first_child.status = Submission.FINISHED
        first_child.save()
        second_child.status = Submission.SCORING
        second_child.save()

        assert BestModeStrategy()._candidate_pks(second_child) == [second_child.pk, parent.pk]


class ForceLastStrategyTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.leaderboard = LeaderboardFactory(submission_rule=Leaderboard.FORCE_LAST)
        ColumnFactory(leaderboard=self.leaderboard, index=0, key='score')
        self.phase = PhaseFactory(leaderboard=self.leaderboard)

        # A previous 2-task submission that is already on the leaderboard
        self.previous_parent = SubmissionFactory(
            phase=self.phase,
            owner=self.user,
            has_children=True,
            leaderboard=None,
            status=Submission.FINISHED,
        )
        self.previous_children = [
            SubmissionFactory(
                phase=self.phase,
                owner=self.user,
                parent=self.previous_parent,
                leaderboard=self.leaderboard,
                status=Submission.FINISHED,
            )
            for _ in range(2)
        ]

        # A new 2-task submission that is still scoring
        self.new_parent = SubmissionFactory(
            phase=self.phase,
            owner=self.user,
            has_children=True,
            leaderboard=None,
            status=Submission.SCORING,
        )
        self.new_child_submission_1 = SubmissionFactory(
            phase=self.phase,
            owner=self.user,
            parent=self.new_parent,
            leaderboard=None,
            status=Submission.SCORING,
        )
        self.new_child_submission_2 = SubmissionFactory(
            phase=self.phase,
            owner=self.user,
            parent=self.new_parent,
            leaderboard=None,
            status=Submission.SCORING,
        )

    def send_scores_like_compute_worker(self, submission, score):
        """Posts scores for one submission, the same way the compute worker does when a task finishes."""
        url = f'/api/upload_submission_scores/{submission.pk}/'
        resp = self.client.post(url, {'secret': str(submission.secret), 'scores': {'score': score}}, format='json')
        assert resp.status_code == 200

    def test_force_last_keeps_previous_submission_until_all_tasks_have_scores(self):
        """
        Only task 1 of the new submission sends its scores.
        Expect the previous submission to stay on the leaderboard, and the new child not to be on it yet.
        """
        self.send_scores_like_compute_worker(submission=self.new_child_submission_1, score=5)

        for child in self.previous_children:
            child.refresh_from_db()
            assert child.leaderboard == self.leaderboard
        self.new_child_submission_1.refresh_from_db()
        assert self.new_child_submission_1.leaderboard is None

    def test_force_last_puts_all_tasks_on_leaderboard_when_last_task_has_scores(self):
        """
        Task 1 and then task 2 of the new submission send their scores.
        Expect both new children on the leaderboard, and the previous submission removed from it.
        """
        self.send_scores_like_compute_worker(submission=self.new_child_submission_1, score=5)
        self.send_scores_like_compute_worker(submission=self.new_child_submission_2, score=7)

        self.new_child_submission_1.refresh_from_db()
        self.new_child_submission_2.refresh_from_db()
        assert self.new_child_submission_1.leaderboard == self.leaderboard
        assert self.new_child_submission_2.leaderboard == self.leaderboard
        for child in self.previous_children:
            child.refresh_from_db()
            assert child.leaderboard is None

    def test_force_last_single_task_submission_replaces_previous_submission(self):
        """
        A new submission without children sends its scores.
        Expect it on the leaderboard, and the previous submission removed from it.
        """
        single_task_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.user,
            leaderboard=None,
            status=Submission.SCORING,
        )

        self.send_scores_like_compute_worker(submission=single_task_submission, score=5)

        single_task_submission.refresh_from_db()
        assert single_task_submission.leaderboard == self.leaderboard
        for child in self.previous_children:
            child.refresh_from_db()
            assert child.leaderboard is None
