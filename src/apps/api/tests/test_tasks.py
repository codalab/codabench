from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import Submission
from factories import UserFactory, CompetitionFactory, TaskFactory, SolutionFactory, PhaseFactory, SubmissionFactory


class TestTasks(APITestCase):
    def test_task_shown_as_validated_properly(self):
        user = UserFactory(username='test')
        solution = SolutionFactory(md5="12345")
        task = TaskFactory(created_by=user, solutions=[solution])
        competition = CompetitionFactory(created_by=user)
        phase = PhaseFactory(competition=competition, tasks=[task])
        submission = SubmissionFactory(md5="12345", phase=phase, status=Submission.FINISHED)

        self.client.login(username=user.username, password='test')

        # task should be validated because we have a successful submission matching
        # our solution
        resp = self.client.get(reverse('task-list'))
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["validated"]

        # make submission anything but Submission.FINISHED, task -> invalidated
        submission.status = Submission.FAILED
        submission.save()
        resp = self.client.get(reverse('task-list'))
        assert resp.status_code == 200
        assert not resp.data["results"][0]["validated"]

        # make submission Submission.Finished, task -> re-validated
        submission.status = Submission.FINISHED
        submission.save()
        resp = self.client.get(reverse('task-list'))
        assert resp.status_code == 200
        assert resp.data["results"][0]["validated"]

        # delete submission, task -> re-invalidated
        submission.delete()
        resp = self.client.get(reverse('task-list'))
        assert resp.status_code == 200
        assert not resp.data["results"][0]["validated"]

        # make submission with different Sha -> still invalid
        SubmissionFactory(md5="different", phase=phase, status=Submission.FINISHED)
        resp = self.client.get(reverse('task-list'))
        assert resp.status_code == 200
        assert not resp.data["results"][0]["validated"]
