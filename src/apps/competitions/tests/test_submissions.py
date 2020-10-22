import json
import uuid
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from api.serializers.competitions import CompetitionSerializer
from competitions.models import Submission
from competitions.tasks import run_submission
from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory, TaskFactory, LeaderboardFactory, \
    ColumnFactory


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
        yesterday = timezone.now() - timedelta(days=1)
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
        with mock.patch('competitions.tasks._send_submission'):
            sub.start()
            assert Submission.objects.all().count() == 1
            sub.re_run()
        assert Submission.objects.all().count() == 2
        subs = Submission.objects.all()
        assert subs[0].owner == subs[1].owner
        assert subs[0].phase == subs[1].phase
        assert subs[0].data == subs[1].data

    def test_cancel_submission_sets_status(self):
        sub = self.make_submission()
        assert sub.cancel(), 'Cancel returned False, meaning the submission could not be cancelled when it should'
        assert sub.status == 'Cancelled'
        assert sub.status == 'Cancelled'

    def test_cancel_does_nothing_if_status_is_cancelled_failed_or_finished(self):
        sub = self.make_submission()
        for status in ['Failed', 'Cancelled', 'Finished']:
            sub.status = status
            assert not sub.cancel(), "Cancel returned True, meaning submission could be cancelled when it shouldn\'t"
            assert sub.status == status, 'Status was changed and should not have been'

    def test_adding_submission_to_leaderboard_adds_all_children(self):
        parent_sub = self.make_submission(has_children=True)

        for _ in range(10):
            leaderboard = LeaderboardFactory()
            parent_sub.phase.leaderboard = leaderboard
            parent_sub.phase.save()

            ColumnFactory(leaderboard=leaderboard)
            self.make_submission(parent=parent_sub)

        self.client.force_login(parent_sub.owner)
        url = reverse('submission-submission-leaderboard-connection', kwargs={'pk': parent_sub.pk})
        resp = self.client.post(url)
        assert resp.status_code == 200
        for submission in Submission.objects.filter(parent=parent_sub):
            assert submission.leaderboard

    def test_remove_submission_from_leaderboard(self):
        parent_sub = self.make_submission(has_children=True)

        for _ in range(10):
            leaderboard = LeaderboardFactory(submission_rule="Add_And_Delete")
            parent_sub.phase.leaderboard = leaderboard
            parent_sub.phase.save()

            ColumnFactory(leaderboard=leaderboard)
            self.make_submission(parent=parent_sub)

        self.client.force_login(parent_sub.owner)
        url = reverse('submission-submission-leaderboard-connection', kwargs={'pk': parent_sub.pk})
        self.client.post(url)
        resp = self.client.delete(url)
        assert resp.status_code == 200
        for submission in Submission.objects.filter(parent=parent_sub):
            assert submission.leaderboard is None

    def test_only_owner_can_add_submission_to_leaderboard(self):
        parent_sub = self.make_submission(has_children=True)

        for _ in range(10):
            leaderboard = LeaderboardFactory()
            parent_sub.phase.leaderboard = leaderboard
            parent_sub.phase.save()

            ColumnFactory(leaderboard=leaderboard)
            self.make_submission(parent=parent_sub)
        different_user = UserFactory()
        self.client.force_login(different_user)
        url = reverse('submission-submission-leaderboard-connection', kwargs={'pk': parent_sub.pk})
        resp = self.client.post(url)
        assert resp.status_code == 404


class MultipleTasksPerPhaseTests(SubmissionTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.comp = CompetitionFactory()
        self.tasks = [TaskFactory() for _ in range(2)]
        self.phase = PhaseFactory(competition=self.comp, tasks=self.tasks)

    def mock_run_submission(self, submission, task=None):
        with mock.patch('competitions.tasks.app.send_task') as celery_app:
            with mock.patch('competitions.tasks.make_url_sassy') as mock_sassy:
                class Task:
                    def __init__(self):
                        self.id = uuid.uuid4()

                if task is None:
                    task = Task()
                celery_app.return_value = task
                mock_sassy.return_value = ''
                run_submission(submission.pk)
                return celery_app

    def test_making_submission_creates_parent_sub_and_additional_sub_per_task(self):
        self.sub = self.make_submission()
        with mock.patch('competitions.tasks.send_parent_status'):
            with mock.patch('competitions.tasks.send_child_id'):
                resp = self.mock_run_submission(self.sub)
        assert resp.call_count == 2
        sub = Submission.objects.get(id=self.sub.id)
        assert sub.has_children
        assert sub.children.count() == 2

    def test_children_always_created_in_the_same_order(self):
        self.sub = self.make_submission()
        with mock.patch('competitions.tasks.send_parent_status'):
            with mock.patch('competitions.tasks.send_child_id'):
                resp = self.mock_run_submission(self.sub)
        assert resp.call_count == 2

        self.sub = Submission.objects.get(id=self.sub.id)
        children = self.sub.children.order_by('id').values_list('id', flat=True)
        first_call_args = resp.call_args_list[0][1]['args'][0]
        second_call_args = resp.call_args_list[1][1]['args'][0]
        assert first_call_args['id'] == children[0]
        assert second_call_args['id'] == children[1]

    def test_making_submission_to_phase_with_one_task_does_not_create_parents_or_children(self):
        self.single_phase = PhaseFactory(competition=self.comp)
        self.sub = self.make_submission(phase=self.single_phase)
        resp = self.mock_run_submission(self.sub)
        assert resp.call_count == 1
        sub = Submission.objects.get(id=self.sub.id)
        assert not sub.has_children

    def test_adding_task_to_phase_runs_submissions_on_new_task(self):

        leaderboard = LeaderboardFactory()

        for phase in self.comp.phases.all():
            phase.leaderboard = leaderboard
            phase.save()

        SubmissionFactory(owner=self.user, phase=self.phase)

        competition_data = CompetitionSerializer(self.comp).data
        new_task = TaskFactory()
        competition_data["phases"][0]['tasks'].append(new_task.key)
        competition_data['logo'] = None

        for task_d, task in enumerate(competition_data["phases"][0]['tasks']):
            competition_data["phases"][0]['tasks'][task_d] = str(task)
        url = reverse("competition-detail", args=(self.comp.pk,))

        self.client.force_login(self.comp.created_by)

        # during our put we should expect 1 new run to happen
        with mock.patch('api.views.competitions.CompetitionViewSet.run_new_task_submissions') as run_new_task_submission:
            self.client.put(url, json.dumps(competition_data), content_type="application/json")
            run_new_task_submission.assert_called_once()
