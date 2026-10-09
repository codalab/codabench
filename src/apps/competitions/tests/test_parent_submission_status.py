from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import Submission
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory


class ParentSubmissionStatusTests(APITestCase):
    """
    Tests for the status of a parent submission, set from the statuses of its children
    (Submission.check_child_submission_statuses).

    The rule: the parent is Finished if at least one child finished,
    otherwise Failed if at least one child failed, otherwise Cancelled.

    Child statuses are reported through the API, the same way the compute worker does.
    """

    def setUp(self):
        self.owner = UserFactory()
        self.phase = PhaseFactory(competition=CompetitionFactory(created_by=self.owner))
        self.parent = SubmissionFactory(
            owner=self.owner, phase=self.phase, status=Submission.RUNNING, has_children=True,
        )

    def _create_child_submissions(self, count):
        """Creates `count` running child submissions of the parent and returns them"""
        return [
            SubmissionFactory(owner=self.owner, phase=self.phase, parent=self.parent, status=Submission.RUNNING)
            for _ in range(count)
        ]

    def _report_child_status_like_compute_worker(self, child, status):
        """Sends the child's new status to the API, like the compute worker does: a PATCH with the child's secret"""
        response = self.client.patch(
            reverse('submission-detail', kwargs={'pk': child.pk}),
            {'status': status, 'secret': str(child.secret)},
            format='json',
        )
        assert response.status_code == 200, response.content

    def _get_parent_status(self):
        """Reloads the parent from the database and returns its status"""
        self.parent.refresh_from_db()
        return self.parent.status

    def test_parent_is_finished_when_all_children_finished(self):
        """All children finished: the parent is Finished"""
        child_1, child_2 = self._create_child_submissions(count=2)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.FINISHED)
        self._report_child_status_like_compute_worker(child=child_2, status=Submission.FINISHED)

        assert self._get_parent_status() == Submission.FINISHED

    def test_parent_is_failed_when_all_children_failed(self):
        """All children failed: the parent is Failed (before the fix it was Finished)"""
        child_1, child_2 = self._create_child_submissions(count=2)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.FAILED)
        self._report_child_status_like_compute_worker(child=child_2, status=Submission.FAILED)

        assert self._get_parent_status() == Submission.FAILED

    def test_parent_is_cancelled_when_all_children_cancelled(self):
        """All children cancelled: the parent is Cancelled (before the fix it was Finished)"""
        child_1, child_2 = self._create_child_submissions(count=2)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.CANCELLED)
        self._report_child_status_like_compute_worker(child=child_2, status=Submission.CANCELLED)

        assert self._get_parent_status() == Submission.CANCELLED

    def test_parent_is_finished_when_one_child_finished_and_one_failed(self):
        """One child finished and one failed: the parent is Finished, because one child finished"""
        child_1, child_2 = self._create_child_submissions(count=2)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.FINISHED)
        self._report_child_status_like_compute_worker(child=child_2, status=Submission.FAILED)

        assert self._get_parent_status() == Submission.FINISHED

    def test_parent_is_finished_when_one_child_finished_and_one_cancelled(self):
        """One child finished and one cancelled: the parent is Finished, because one child finished"""
        child_1, child_2 = self._create_child_submissions(count=2)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.FINISHED)
        self._report_child_status_like_compute_worker(child=child_2, status=Submission.CANCELLED)

        assert self._get_parent_status() == Submission.FINISHED

    def test_parent_is_failed_when_one_child_failed_and_one_cancelled(self):
        """One child failed and one cancelled: the parent is Failed, because no child finished and one failed"""
        child_1, child_2 = self._create_child_submissions(count=2)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.FAILED)
        self._report_child_status_like_compute_worker(child=child_2, status=Submission.CANCELLED)

        assert self._get_parent_status() == Submission.FAILED

    def test_parent_is_finished_when_children_finished_failed_and_cancelled(self):
        """Three children, one finished, one failed and one cancelled: the parent is Finished, because one child finished"""
        child_1, child_2, child_3 = self._create_child_submissions(count=3)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.FINISHED)
        self._report_child_status_like_compute_worker(child=child_2, status=Submission.FAILED)
        self._report_child_status_like_compute_worker(child=child_3, status=Submission.CANCELLED)

        assert self._get_parent_status() == Submission.FINISHED

    def test_parent_status_does_not_change_until_all_children_are_done(self):
        """
        One child failed and the other is still running: the parent stays Running.
        When the other child also fails, the parent becomes Failed.
        """
        child_1, child_2 = self._create_child_submissions(count=2)

        self._report_child_status_like_compute_worker(child=child_1, status=Submission.FAILED)
        assert self._get_parent_status() == Submission.RUNNING

        self._report_child_status_like_compute_worker(child=child_2, status=Submission.FAILED)
        assert self._get_parent_status() == Submission.FAILED
