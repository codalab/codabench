from unittest import mock

from django.urls import reverse
import pytest
import random
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from api.serializers.competitions import CompetitionSerializer, PhaseDetailSerializer
from competitions.models import Submission
from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory, LeaderboardFactory, TaskFactory, PhaseTaskInstanceFactory


class ReRunPhaseSubmissionTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.admin = UserFactory(username='admin', super_user=True)
        self.collab = UserFactory(username='collab')
        self.normal_user = UserFactory(username='norm')
        self.competition = CompetitionFactory(created_by=self.user)
        self.competition.collaborators.add(self.collab)
        self.phase = PhaseFactory(competition=self.competition)
        self.task = TaskFactory()
        self.phase.tasks.add(self.task)

        for _ in range(4):
            self.make_submission(status=Submission.FINISHED, task=self.task)

        submission_count = 4
        for _ in range(submission_count):
            self.make_submission()

    def make_submission(self, **kwargs):
        kwargs.setdefault('owner', self.user)
        kwargs.setdefault('phase', self.phase)
        SubmissionFactory(**kwargs)

    def assert_rerun_succeeds(self):
        initial_parent_ids = set(
            self.phase.submissions
            .filter(parent__isnull=True)
            .values_list("pk", flat=True)
        )

        initial_child_ids = set(
            self.phase.submissions
            .filter(parent__isnull=False)
            .values_list("pk", flat=True)
        )

        with mock.patch("competitions.tasks.run_submission") as mocked_run:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.get(
                    reverse("phases-rerun_submissions", kwargs={"pk": self.phase.id})
                )

        assert response.status_code == 200
        assert response.data["count"] == 4
        assert mocked_run.call_count == 4

        final_parent_ids = set(
            self.phase.submissions
            .filter(parent__isnull=True)
            .values_list("pk", flat=True)
        )

        assert final_parent_ids == initial_parent_ids

        final_child_ids = set(
            self.phase.submissions
            .filter(parent__isnull=False)
            .values_list("pk", flat=True)
        )

        assert final_child_ids == initial_child_ids
        assert self.phase.submissions.count() == (
            len(initial_parent_ids) + len(initial_child_ids)
        )

    def test_comp_creator_can_re_run_whole_phase(self):
        self.client.login(username='test', password='test')
        self.assert_rerun_succeeds()

    def test_super_user_can_re_run_whole_phase(self):
        self.client.login(username='admin', password='test')
        self.assert_rerun_succeeds()

    def test_collab_can_re_run_whole_phase(self):
        self.client.login(username='collab', password='test')
        self.assert_rerun_succeeds()


class CompetitionPhaseMigrationValidation(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.competition = CompetitionFactory(created_by=self.user, id=1)
        self.leaderboard = LeaderboardFactory()
        self.phase = PhaseFactory(competition=self.competition, leaderboard=self.leaderboard)

    def serialize_and_validate_data(self):
        serializer = CompetitionSerializer(self.competition)
        data = serializer.data

        with pytest.raises(ValidationError) as exception:
            serializer = CompetitionSerializer(data=data)
            serializer.is_valid(raise_exception=True)

        return exception

    def test_phase_is_valid(self):
        self.phase.auto_migrate_to_this_phase = False
        self.phase.save()
        exception = self.serialize_and_validate_data()

        assert ("'phase:'" not in str(exception.value))

    def test_phase_serializer_auto_migrate_on_first_phase(self):
        self.phase.auto_migrate_to_this_phase = True
        self.phase.save()
        exception = self.serialize_and_validate_data()

        errors = ["You cannot auto migrate in a competition with one phase",
                  "You cannot auto migrate to the first phase of a competition"]

        assert any(error in str(exception.value) for error in errors)

    def test_phase_serializer_no_phases(self):
        self.phase.competition = None
        self.phase.save()
        exception = self.serialize_and_validate_data()

        assert ("Competitions must have at least one phase" in str(exception.value))


class PhaseTaskInstanceTests(APITestCase):
    def setUp(self):
        self.phase = PhaseFactory()
        self.dummy_task = self.phase.tasks.first()
        self.tasks = [TaskFactory() for x in range(10)]
        self.tasks_random = [task for task in self.tasks]
        random.shuffle(self.tasks_random)
        for task in self.tasks:
            order_index = self.tasks_random.index(task)
            PhaseTaskInstanceFactory(phase=self.phase, task=task, order_index=order_index)
        self.phase.tasks.remove(self.dummy_task)

    def test_phase_detail_tasks_ordered(self):
        self.serializer = PhaseDetailSerializer(self.phase).data
        assert len(self.tasks) == len(self.serializer['tasks'])

        for index in range(len(self.tasks)):
            assert self.tasks_random[index].id == self.serializer['tasks'][index]['id']
