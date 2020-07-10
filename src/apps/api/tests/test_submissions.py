import random
from unittest import mock

from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import Submission
from factories import UserFactory, CompetitionFactory, PhaseFactory, CompetitionParticipantFactory, SubmissionFactory, TaskFactory

from datasets.models import Data

from src.apps.competitions.models import CompetitionParticipant


class SubmissionAPITests(APITestCase):
    def setUp(self):
        self.superuser = UserFactory(is_superuser=True, is_staff=True)

        # Competition and creator
        self.creator = UserFactory(username='creator', password='creator')
        self.collaborator = UserFactory(username='collab', password='collab')
        self.comp = CompetitionFactory(created_by=self.creator, collaborators=[self.collaborator])
        self.phase = PhaseFactory(competition=self.comp)
        for _ in range(2):
            self.phase.tasks.add(TaskFactory.create())

        # Extra phase for testing tasks can't be run on the wrong phase
        self.other_phase = PhaseFactory(competition=self.comp)

        # Extra dummy user to test permissions, they shouldn't have access to many things
        self.other_user = UserFactory(username='other_user', password='other')

        # Make a participant and submission into competition
        self.participant = UserFactory(username='participant', password='other')
        CompetitionParticipantFactory(user=self.participant, competition=self.comp)
        self.existing_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.SUBMITTED,
            secret='7df3600c-1234-5678-bbc8-bbe91f42d875'
        )

    def test_can_make_submission_checks_if_you_are_participant(self):
        # You should get a message back if you aren't registered in this competition
        self.client.login(username="other_user", password="other")

        resp = self.client.get(reverse("can_make_submission", args=(self.phase.pk,)))
        assert resp.status_code == 200
        assert not resp.data["can"]
        assert resp.data["reason"] == "User not approved to participate in this competition"
        self.client.logout()

        # If you are in the competition (the creator), should be good-to-go
        self.client.login(username="creator", password="creator")
        resp = self.client.get(reverse("can_make_submission", args=(self.phase.pk,)))
        assert resp.status_code == 200
        assert resp.data["can"]

    def test_making_a_submission_checks_if_you_are_a_participant(self):
        # You should get a message back if you aren't registered in this competition
        self.client.login(username="other_user", password="other")

        resp = self.client.post(reverse("submission-list"), {"phase": self.phase.pk})
        assert resp.status_code == 403
        assert "You do not have access to this competition to make a submission" in resp.data["detail"]

    def test_trying_to_change_submission_without_secret_raises_permission_denied(self):
        url = reverse('submission-detail', args=(self.existing_submission.pk,))
        # As anonymous user
        resp = self.client.patch(url, {"status": Submission.FINISHED})
        assert resp.status_code == 400
        assert "Secret: (None) not a valid UUID" in str(resp.content)
        assert Submission.objects.filter(pk=self.existing_submission.pk, status=Submission.SUBMITTED)

        # As superuser (bad secret)
        self.client.force_login(self.creator)
        resp = self.client.patch(url, {"status": Submission.FINISHED, "secret": '7df3600c-aa6d-41c5-bbc8-bbe91f42d875'})
        assert resp.status_code == 403
        assert resp.data["detail"] == "Submission secrets do not match"
        assert Submission.objects.filter(pk=self.existing_submission.pk, status=Submission.SUBMITTED)

        # As anonymous user with secret
        self.client.logout()
        resp = self.client.patch(url, {"status": Submission.FINISHED, "secret": self.existing_submission.secret})
        assert resp.status_code == 200
        assert Submission.objects.filter(pk=self.existing_submission.pk, status=Submission.FINISHED)

    def test_cannot_delete_submission_you_didnt_create(self):
        url = reverse('submission-detail', args=(self.existing_submission.pk,))

        # As anonymous user
        resp = self.client.delete(url)
        assert resp.status_code == 403
        assert resp.data["detail"] == "Cannot interact with submission you did not make"

        # As regular user
        self.client.force_login(self.other_user)
        resp = self.client.delete(url)
        assert resp.status_code == 403
        assert resp.data["detail"] == "Cannot interact with submission you did not make"

        # As user who made submission
        self.client.force_login(self.participant)
        resp = self.client.delete(url)
        assert resp.status_code == 204
        assert not Submission.objects.filter(pk=self.existing_submission.pk).exists()

        # As superuser (re-making submission since it has been destroyed)
        self.existing_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.SUBMITTED,
            secret='7df3600c-1234-5678-90c8-bbe91f42d875'
        )
        url = reverse('submission-detail', args=(self.existing_submission.pk,))

        self.client.force_login(self.superuser)
        resp = self.client.delete(url)
        assert resp.status_code == 204
        assert not Submission.objects.filter(pk=self.existing_submission.pk).exists()

    def test_cannot_get_details_of_submission_unless_creator_collab_or_superuser(self):
        url = reverse('submission-get-details', args=(self.existing_submission.pk,))

        # Non logged in user can't even see this
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Regular user can't see this
        self.client.force_login(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Actual user can see download details
        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Competition creator can see download details
        self.client.force_login(self.creator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Collaborator can see download details
        self.client.force_login(self.collaborator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Superuser can see download details
        self.client.force_login(self.superuser)
        resp = self.client.get(url)
        assert resp.status_code == 200

    def test_hidden_details_actually_stops_submission_creator_from_seeing_output(self):
        self.phase.hide_output = True
        self.phase.save()
        url = reverse('submission-get-details', args=(self.existing_submission.pk,))

        # Non logged in user can't even see this
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Regular user can't see this
        self.client.force_login(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Actual user cannot see their submission details
        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 403
        assert resp.data["detail"] == "Cannot access submission details while phase marked to hide output."

        # Competition creator can see download details
        self.client.force_login(self.creator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Collaborator can see download details
        self.client.force_login(self.collaborator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Superuser can see download details
        self.client.force_login(self.superuser)
        resp = self.client.get(url)
        assert resp.status_code == 200

    def test_bot_users_are_automatically_added_to_participants_on_submission(self):
        self.bot_user = UserFactory(username='bot_user', password='other', is_bot=True)
        self.bot_comp = CompetitionFactory(created_by=self.creator, collaborators=[self.collaborator], allow_robot_submissions=True)
        self.bot_phase = PhaseFactory(competition=self.bot_comp)
        self.client.login(username="bot_user", password="other")

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase.pk,)))

        assert resp.status_code == 200
        assert resp.data["can"]

    def test_max_submissions_per_day_limits_normal_users_and_not_bots(self):
        self.bot_user = UserFactory(username='bot_user', password='other', is_bot=True)
        self.bot_comp = CompetitionFactory(created_by=self.creator, collaborators=[self.collaborator], allow_robot_submissions=True)
        self.bot_phase = PhaseFactory(competition=self.bot_comp, has_max_submissions=True, max_submissions_per_day=1, max_submissions_per_person=1)
        self.client.login(username='bot_user', password='other')

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase.pk,)))

        assert resp.status_code == 200
        assert resp.data["can"]

        for _ in range(2):
            SubmissionFactory(
                phase=self.bot_phase,
                owner=self.bot_user,
                status=Submission.SUBMITTED,
                secret='7df3600c-1234-5678-bbc8-bbe91f42d875'
            )

        assert Submission.objects.filter(owner=self.bot_user, phase=self.bot_phase).count() > self.bot_phase.max_submissions_per_day
        assert Submission.objects.filter(owner=self.bot_user, phase=self.bot_phase).count() > self.bot_phase.max_submissions_per_person

        self.client.logout()

        CompetitionParticipant(user=self.participant, competition=self.bot_comp, status=CompetitionParticipant.APPROVED).save()

        self.client.login(username='participant', password='other')

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase.pk,)))

        assert resp.status_code == 200
        assert resp.data["can"]

        for _ in range(2):
            SubmissionFactory(
                phase=self.bot_phase,
                owner=self.bot_user,
                status=Submission.SUBMITTED,
                secret='7df3600c-1234-5678-bbc8-bbe91f42d875'
            )
    def test_can_select_tasks_when_making_submissions(self):
        self.client.login(username="creator", password="creator")

        # Make a new submission with a random set of tasks
        tasks = random.sample(list(self.phase.tasks.all().values_list('id', flat=True)), 2)
        url = reverse('submission-list')
        self.submission_data = Data.objects.create(created_by=self.participant, type=Data.SUBMISSION)
        data = {
            'phase': self.phase.id,
            'data': self.submission_data.key,
            'tasks': tasks
        }

        # Mock _send_submission so submissions don't actually run
        with mock.patch('competitions.tasks._send_submission'):
            resp = self.client.post(url, data)
            # Check that the submission was created
            assert resp.status_code == 201
            tasks.sort()
            # Make sure only the selected tasks are run
            assert list(self.phase.submissions.get(id=resp.json().get('id')).children.all().order_by('task__pk').values_list('task', flat=True)) == tasks

    def test_cannot_select_tasks_on_wrong_phase(self):
        self.client.login(username="creator", password="creator")

        # Make a new submission with a random set of tasks
        tasks = [*random.sample(list(self.phase.tasks.all().values_list('id', flat=True)), 2), self.other_phase.tasks.first().pk]
        url = reverse('submission-list')
        self.submission_data = Data.objects.create(created_by=self.participant, type=Data.SUBMISSION)
        data = {
            'phase': self.phase.id,
            'data': self.submission_data.key,
            'tasks': tasks
        }

        # Mock _send_submission so submissions don't actually run
        with mock.patch('competitions.tasks._send_submission'):
            resp = self.client.post(url, data)
            # Don't run any tasks if any task isn't a part of the phase
            assert resp.status_code == 400
            assert resp.json() == {'non_field_errors': ['All tasks must be part of the current phase.']}

    def test_can_re_run_submissions_with_multiple_tasks(self):
        self.client.login(username="creator", password="creator")

        # Make a new submission with a random set of tasks
        tasks = random.sample(list(self.phase.tasks.all().values_list('id', flat=True)), 2)
        url = reverse('submission-list')
        self.submission_data = Data.objects.create(created_by=self.participant, type=Data.SUBMISSION)
        data = {
            'phase': self.phase.id,
            'data': self.submission_data.key,
            'tasks': tasks
        }

        # Mock _send_submission so submissions don't actually run
        with mock.patch('competitions.tasks._send_submission'):
            resp = self.client.post(url, data)

            sub = Submission.objects.get(id=resp.json().get('id'))
            sub.re_run()

            sub_copy = Submission.objects.filter(has_children=True).order_by('created_when').last()
            # Check sub_copy is a new submission
            assert sub.pk != sub_copy.pk
            tasks.sort()
            # Make sure the selected tasks were run in the duplicate submission's children
            assert list(sub_copy.children.all().order_by('task__pk').values_list('task', flat=True)) == tasks
