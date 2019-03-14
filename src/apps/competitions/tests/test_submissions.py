from datetime import timedelta

from django.test import TestCase

from competitions.models import Submission
from django.utils.timezone import now
from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory


class MaxSubmissionsTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.competition = CompetitionFactory(created_by=self.user)
        self.phase = PhaseFactory(competition=self.competition)

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.user)
        kwargs.setdefault('phase', self.phase)
        SubmissionFactory(**kwargs)

    def set_max_submissions(self, phase=None, per_person=None, per_day=None):
        phase = self.phase if phase is None else phase
        phase.has_max_submissions = True
        phase.max_submissions_per_person = per_person
        phase.max_submissions_per_day = per_day
        phase.save()

    def test_creating_submission_checks_max_submission_per_day_not_exceeded(self):
        self.set_max_submissions(per_day=1)
        self.make_submission()
        try:
            self.make_submission()
            assert False, "This should have raised a PermissionError"
        except PermissionError:
            pass

    def test_creating_submission_checks_max_submission_per_person_not_exceeded(self):
        self.set_max_submissions(per_person=1)
        self.make_submission()
        try:
            self.make_submission()
            assert False, "This should have raised a PermissionError"
        except PermissionError:
            pass

    def test_failed_submissions_not_counted_towards_max(self):
        self.set_max_submissions(per_person=1, per_day=1)
        self.make_submission(status="Failed")
        try:
            self.make_submission()
        except PermissionError:
            assert False, "This counted failed submissions"

    def test_max_per_day_not_counting_previous_days_submissions(self):
        self.set_max_submissions(per_day=1)
        yesterday = now() - timedelta(days=1)
        self.make_submission(created_when=yesterday)
        try:
            self.make_submission()
        except PermissionError:
            assert False, "This counted yesterday's submissions"

    def test_max_submissions_not_counting_other_user_submissions(self):
        self.set_max_submissions(per_person=1, per_day=1)
        other_user = UserFactory()
        self.make_submission(owner=other_user)
        try:
            self.make_submission()
        except PermissionError:
            assert False, "This counted other user's submissions"

    def test_submission_not_created_if_max_reached(self):
        self.set_max_submissions(per_person=1)
        self.make_submission()
        try:
            self.make_submission(name='Find Me')
        except PermissionError:
            try:
                Submission.objects.get(name='Find Me')
                assert False, "Submission should not have been created"
            except Submission.DoesNotExist:
                pass


class SubmissionManagerTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.competition = CompetitionFactory(created_by=self.user)
        self.phase = PhaseFactory(competition=self.competition)

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.user)
        kwargs.setdefault('phase', self.phase)
        return SubmissionFactory(**kwargs)

    def test_re_run_submission_creates_new_submission_with_same_data_owner_and_phase(self):
        sub = self.make_submission()
        assert Submission.objects.all().count() == 1
        sub.re_run()
        assert Submission.objects.all().count() == 2
        subs = Submission.objects.all()
        assert subs[0].owner == subs[1].owner
        assert subs[0].phase == subs[1].phase
        assert subs[0].data == subs[1].data

    # def test_cancel_submission_sets_status(self):
    #     sub = self.make_submission()
    #     assert sub.cancel(), 'Cancel returned False, meaning the submission could not be cancelled when it should'
    #     assert sub.status == 'Cancelled'
    #
    # def test_cancel_does_nothing_if_status_is_cancelled_failed_or_finished(self):
    #     sub = self.make_submission()
    #     for status in ['Failed', 'Cancelled', 'Finished']:
    #         sub.status = status
    #         assert not sub.cancel(), "Cancel returned True, meaning submission could be cancelled when it shouldn\'t"
    #         assert sub.status == status, 'Status was changed and should not have been'
