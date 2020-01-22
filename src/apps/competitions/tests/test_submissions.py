import uuid
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now
from django.utils import timezone

from competitions.models import Submission
from competitions.tasks import run_submission
from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory, TaskFactory


class SubmissionTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.competition = CompetitionFactory(created_by=self.user)
        self.phase = PhaseFactory(competition=self.competition)

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.user)
        kwargs.setdefault('phase', self.phase)
        kwargs.setdefault('created_when', timezone.now())
        return SubmissionFactory(**kwargs)


class MaxSubmissionsTests(SubmissionTestCase):
    def set_max_submissions(self, phase=None, per_person=None, per_day=None):
        phase = self.phase if phase is None else phase
        phase.has_max_submissions = True
        phase.max_submissions_per_person = per_person
        phase.max_submissions_per_day = per_day
        phase.save()

    def test_creating_submission_checks_max_submission_per_day_not_exceeded(self):
        self.set_max_submissions(per_day=1)
        self.make_submission()
        self.assertRaises(PermissionError, self.make_submission)

    def test_creating_submission_checks_max_submission_per_person_not_exceeded(self):
        self.set_max_submissions(per_person=1)
        self.make_submission()
        self.assertRaises(PermissionError, self.make_submission)

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
        self.assertRaises(PermissionError, self.make_submission)
        assert not Submission.objects.filter(name='Find Me').exists()

    def test_children_submissions_dont_count_toward_max(self):
        self.make_submission(parent=self.make_submission())
        self.set_max_submissions(per_person=2)
        self.make_submission()
        self.assertRaises(PermissionError, self.make_submission)


class SubmissionManagerTests(SubmissionTestCase):
    def test_re_run_submission_creates_new_submission_with_same_data_owner_and_phase(self):
        sub = self.make_submission()
        assert Submission.objects.all().count() == 1
        sub.re_run()
        assert Submission.objects.all().count() == 2
        subs = Submission.objects.all()
        assert subs[0].owner == subs[1].owner
        assert subs[0].phase == subs[1].phase
        assert subs[0].data == subs[1].data

    # TODO: Figure out why this test causes CircleCI to freeze
    # def test_cancel_submission_sets_status(self):
    #     sub = self.make_submission()
    #     assert sub.cancel(), 'Cancel returned False, meaning the submission could not be cancelled when it should'
    #     assert sub.status == 'Cancelled'

    def test_cancel_does_nothing_if_status_is_cancelled_failed_or_finished(self):
        sub = self.make_submission()
        for status in ['Failed', 'Cancelled', 'Finished']:
            sub.status = status
            assert not sub.cancel(), "Cancel returned True, meaning submission could be cancelled when it shouldn\'t"
            assert sub.status == status, 'Status was changed and should not have been'


class MultipleTasksPerPhaseTests(SubmissionTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.comp = CompetitionFactory()
        self.tasks = [TaskFactory() for _ in range(2)]
        self.phase = PhaseFactory(competition=self.comp, tasks=self.tasks)

    def mock_run_submission(self, submission):
        with mock.patch('competitions.tasks.app.send_task') as celery_app:
            with mock.patch('competitions.tasks.make_url_sassy') as mock_sassy:
                class Task:
                    def __init__(self):
                        self.id = uuid.uuid4()

                task = Task()
                celery_app.return_value = task
                mock_sassy.return_value = ''
                run_submission(submission.pk)
                return celery_app

    def test_making_submission_creates_parent_sub_and_additional_sub_per_task(self):
        self.sub = self.make_submission()
        with mock.patch('competitions.tasks.send_parent_status') as parent_websocket_mock:
            with mock.patch('competitions.tasks.send_child_id') as child_websocket_mock:
                assert parent_websocket_mock.call_count == 1
                assert child_websocket_mock.call_count == 2
                resp = self.mock_run_submission(self.sub)
        assert resp.call_count == 2
        sub = Submission.objects.get(id=self.sub.id)
        assert sub.has_children
        assert sub.children.count() == 2

    def test_making_submission_to_phase_with_one_task_does_not_create_parents_or_children(self):
        self.single_phase = PhaseFactory(competition=self.comp)
        self.sub = self.make_submission(phase=self.single_phase)
        resp = self.mock_run_submission(self.sub)
        assert resp.call_count == 1
        sub = Submission.objects.get(id=self.sub.id)
        assert not sub.has_children
