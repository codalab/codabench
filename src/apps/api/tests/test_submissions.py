import random
from unittest import mock

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from competitions.models import Submission, CompetitionParticipant
from factories import UserFactory, CompetitionFactory, PhaseFactory, CompetitionParticipantFactory, SubmissionFactory, \
    TaskFactory, OrganizationFactory, DataFactory, LeaderboardFactory

from datasets.models import Data
from profiles.models import Membership


class SubmissionAPITests(APITestCase):
    def setUp(self):
        self.superuser = UserFactory(is_superuser=True, is_staff=True)

        # Competition and creator
        self.creator = UserFactory(username='creator', password='creator')
        self.collaborator = UserFactory(username='collab', password='collab')
        self.comp = CompetitionFactory(created_by=self.creator, collaborators=[self.collaborator])
        self.phase = PhaseFactory(competition=self.comp)

        # Extra dummy user to test permissions, they shouldn't have access to many things
        self.other_user = UserFactory(username='other_user', password='other')

        # Make participants
        self.participant = UserFactory(username='participant_approved', password='other')
        self.pending_participant = UserFactory(username='participant_pending', password='other')
        self.denied_participant = UserFactory(username='participant_denied', password='other')

        # Add user as participants in a competition with different statuses
        CompetitionParticipantFactory(user=self.participant, competition=self.comp, status=CompetitionParticipant.APPROVED)
        CompetitionParticipantFactory(user=self.pending_participant, competition=self.comp, status=CompetitionParticipant.PENDING)
        CompetitionParticipantFactory(user=self.denied_participant, competition=self.comp, status=CompetitionParticipant.DENIED)

        # add submission with owner = approved participant
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
        assert resp.status_code == 403
        assert "Submission secrets do not match" in str(resp.content)
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

    def test_no_one_can_see_detailed_result_when_visualization_is_false(self):
        self.comp.enable_detailed_results = False
        self.comp.save()
        url = reverse('submission-get-detail-result', args=(self.existing_submission.pk,))

        # Competition creator cannot see detail result
        self.client.force_login(self.creator)
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Collaborator cannot see detail result
        self.client.force_login(self.collaborator)
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Superuser cannot see detail result
        self.client.force_login(self.superuser)
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Actual user cannot see their submission detail result
        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Regular user cannot see submission detail result
        self.client.force_login(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == 404

    def test_who_can_see_detailed_result_when_visualization_is_true(self):
        self.comp.enable_detailed_results = True
        self.comp.save()
        url = reverse('submission-get-detail-result', args=(self.existing_submission.pk,))

        # Competition creator can see detail result
        self.client.force_login(self.creator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Collaborator can see detail result
        self.client.force_login(self.collaborator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Superuser can see detail result
        self.client.force_login(self.superuser)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # approved user can see submission detail result
        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # pending user cannot see submission detail result
        self.client.force_login(self.pending_participant)
        resp = self.client.get(url)
        assert resp.status_code == 403

        # denied user cannot see submission detail result
        self.client.force_login(self.denied_participant)
        resp = self.client.get(url)
        assert resp.status_code == 403

        # Regular user cannot see submission detail result
        self.client.force_login(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == 403


class SubmissionUpdateTest(APITestCase):
    def setUp(self):
        self.user = UserFactory(username='test')
        self.task1 = TaskFactory(created_by=self.user)
        self.task2 = TaskFactory(created_by=self.user)
        self.competition = CompetitionFactory(created_by=self.user)
        self.phase = PhaseFactory(competition=self.competition, tasks=[self.task1])
        self.secret = '7df3600c-1234-5678-bbc8-bbe91f42d875'
        self.submission = SubmissionFactory(
            task=self.task1,
            phase=self.phase,
            status=Submission.FINISHED,
            secret=self.secret
        )

    def test_submission_task_update(self):
        url = reverse('submission-detail', args=(self.submission.pk,))

        # Update task
        resp = self.client.patch(url, {
            "task": self.task2.id,
            "secret": self.secret
        })
        assert resp.status_code == 403
        assert resp.data["detail"] == "Submission task cannot be updated"
        assert self.submission.task.id == self.task1.id  # task not updated


class OrganizationSubmissionTests(APITestCase):
    def setUp(self):
        # Competition and creator
        self.creator = UserFactory()
        self.comp = CompetitionFactory(created_by=self.creator)
        self.phase = PhaseFactory(competition=self.comp)

        self.org_participant = UserFactory()
        CompetitionParticipantFactory(user=self.org_participant, competition=self.comp, status=CompetitionParticipant.APPROVED)
        self.non_member = UserFactory()
        CompetitionParticipantFactory(user=self.non_member, competition=self.comp, status=CompetitionParticipant.APPROVED)

        self.organization = OrganizationFactory()
        self.organization.users.add(self.org_participant)
        self.organization.membership_set.filter(user=self.org_participant).update(group=Membership.PARTICIPANT)

        self.dataset = DataFactory(type='Submission')

        # urls
        self.url_submission = reverse('submission-list')

    def test_org_participant_can_make_submission_as_organization(self):
        self.client.force_login(user=self.org_participant)
        data = {
            'phase': self.phase.id,
            'data': self.dataset.key,
            'organization': self.organization.id
        }
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            resp = self.client.post(self.url_submission, data=data)
            assert resp.status_code == 201

    def test_non_org_participant_cannot_make_submission_as_organization(self):
        self.client.force_login(user=self.non_member)
        data = {
            'phase': self.phase.id,
            'data': self.dataset.key,
            'organization': self.organization.id
        }
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            resp = self.client.post(self.url_submission, data=data)
            assert resp.status_code == 400


class BotUserSubmissionTests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.bot_user = UserFactory(username='bot_user', password='other', is_bot=True)
        self.non_bot_user = UserFactory(username='non_bot', password='other')
        self.bot_comp = CompetitionFactory(created_by=self.creator, allow_robot_submissions=True)
        self.bot_phase = PhaseFactory(competition=self.bot_comp)
        self.bot_phase_day_limited = PhaseFactory(competition=self.bot_comp, has_max_submissions=True, max_submissions_per_day=1)
        self.bot_phase_person_limited = PhaseFactory(competition=self.bot_comp, has_max_submissions=True, max_submissions_per_person=1)
        CompetitionParticipant(user=self.non_bot_user, competition=self.bot_comp, status=CompetitionParticipant.APPROVED).save()

    def test_bot_users_are_automatically_added_to_participants_on_submission(self):
        self.client.login(username="bot_user", password="other")

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase.pk,)))

        assert resp.status_code == 200
        assert resp.data["can"]

    def test_bots_can_exceed_max_submissions_per_day(self):
        self.client.login(username='bot_user', password='other')

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase_day_limited.pk,)))

        assert resp.status_code == 200
        assert resp.data['can']

        for _ in range(2):
            SubmissionFactory(
                phase=self.bot_phase_day_limited,
                owner=self.bot_user,
                status=Submission.SUBMITTED,
                secret='7df3600c-1234-5678-bbc8-bbe91f42d875'
            )

        assert Submission.objects.filter(owner=self.bot_user, phase=self.bot_phase_day_limited).count() > self.bot_phase_day_limited.max_submissions_per_day

    def test_bots_can_exceed_max_submissions_per_person(self):
        self.client.login(username='bot_user', password='other')

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase_person_limited.pk,)))

        assert resp.status_code == 200
        assert resp.data['can']

        for _ in range(2):
            SubmissionFactory(
                phase=self.bot_phase_person_limited,
                owner=self.bot_user,
                status=Submission.SUBMITTED,
                secret='7df3600c-1234-5678-bbc8-bbe91f42d875'
            )

        assert Submission.objects.filter(owner=self.bot_user, phase=self.bot_phase_person_limited).count() > self.bot_phase_person_limited.max_submissions_per_person

    def test_non_bot_users_cannot_exceed_max_submissions_per_day(self):
        self.client.login(username='non_bot', password='other')

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase_day_limited.pk,)))

        assert resp.status_code == 200
        assert resp.data['can']

        SubmissionFactory(
            phase=self.bot_phase_day_limited,
            owner=self.non_bot_user,
            status=Submission.SUBMITTED,
            secret='7df3600c-1234-5678-bbc8-bbe91f42d875',
            created_when=now(),
        )

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase_day_limited.pk,)))

        assert resp.status_code == 200
        assert not resp.data['can']

    def test_non_bot_users_cannot_exceed_max_submissions_per_person(self):
        self.client.login(username='non_bot', password='other')

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase_person_limited.pk,)))

        assert resp.status_code == 200
        assert resp.data['can']

        SubmissionFactory(
            phase=self.bot_phase_person_limited,
            owner=self.non_bot_user,
            status=Submission.SUBMITTED,
            secret='7df3600c-1234-5678-bbc8-bbe91f42d875'
        )

        resp = self.client.get(reverse("can_make_submission", args=(self.bot_phase_person_limited.pk,)))

        assert resp.status_code == 200
        assert not resp.data['can']


class TaskSelectionTests(APITestCase):
    def setUp(self):
        # Competition and creator
        self.creator = UserFactory(username='creator', password='creator')
        self.comp = CompetitionFactory(created_by=self.creator)
        self.phase = PhaseFactory(competition=self.comp)
        for _ in range(2):
            self.phase.tasks.add(TaskFactory.create())

        # Extra phase for testing tasks can't be run on the wrong phase
        self.other_phase = PhaseFactory(competition=self.comp)
        self.data = Data.objects.create(created_by=self.creator, type=Data.SUBMISSION)

        # URL and data for making submissions
        self.submission_url = reverse('submission-list')
        self.submission_data = {
            'phase': self.phase.id,
            'data': self.data.key,
            'tasks': random.sample(list(self.phase.tasks.all().values_list('id', flat=True)), 2)
        }
        self.sorted_tasks = sorted(self.submission_data['tasks'])

    def test_can_select_tasks_when_making_submissions(self):
        self.client.login(username="creator", password="creator")

        # Mock _send_to_compute_worker so submissions don't actually run
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            resp = self.client.post(self.submission_url, self.submission_data)
            # Check that the submission was created
            assert resp.status_code == 201
            # Make sure only the selected tasks are run
            assert list(self.phase.submissions.get(id=resp.json().get('id')).children.all().order_by('task__pk').values_list('task', flat=True)) == self.sorted_tasks

    def test_cannot_select_tasks_on_wrong_phase(self):
        self.client.login(username="creator", password="creator")

        # Add a task from another phase to the task list
        submission_data = self.submission_data
        submission_data['tasks'] = [*self.submission_data['tasks'], self.other_phase.tasks.first().pk]

        # Mock _send_to_compute_worker so submissions don't actually run
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            resp = self.client.post(self.submission_url, submission_data)
            # Don't run any tasks if any task isn't a part of the phase
            assert resp.status_code == 400
            assert resp.json() == {'non_field_errors': ['All tasks must be part of the current phase.']}

    def test_can_re_run_submissions_with_multiple_tasks(self):
        self.client.login(username="creator", password="creator")

        # Mock _send_to_compute_worker so submissions don't actually run
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            resp = self.client.post(self.submission_url, self.submission_data)

            sub = Submission.objects.get(id=resp.json().get('id'))
            sub.re_run()

            sub_copy = Submission.objects.filter(has_children=True).order_by('created_when').last()
            # Check sub_copy is a new submission
            assert sub.pk != sub_copy.pk
            # Make sure the selected tasks were run in the duplicate submission's children
            assert list(sub_copy.children.all().order_by('task__pk').values_list('task', flat=True)) == self.sorted_tasks

    def test_can_re_run_submissions_with_specific_task_with_bot_user_without_original_submission_secret(self):
        bot_user = UserFactory(username="botman", password="botman", is_bot=True)
        self.client.login(username=bot_user.username, password="botman")

        pre_existing_sub = Submission.objects.create(**{
            'phase': self.phase,
            'owner': self.creator,
            'task': self.phase.tasks.first(),
            'data': self.data,
            'status': Submission.FINISHED,
        })

        new_task = TaskFactory()

        query_params = f'task_key={new_task.key}&private=true'
        url = f"{reverse('submission-re-run-submission', args=(pre_existing_sub.pk,))}?{query_params}"

        self.creator.is_bot = True
        self.creator.save()

        assert not Submission.objects.filter(task=new_task).exists()

        # Mock _send_to_compute_worker so submissions don't actually run
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            self.client.post(url)
            sub = Submission.objects.get(task=new_task)
            assert sub.owner == self.creator
            assert sub.phase == self.phase
            assert sub.data == self.data
            assert sub.is_specific_task_re_run

    def test_cannot_re_run_submissions_with_specific_task_without_bot_user(self):
        non_bot_user = UserFactory(username="nonbotman", password="nonbotman")
        self.client.login(username=non_bot_user.username, password="nonbotman")

        pre_existing_sub = Submission.objects.create(**{
            'phase': self.phase,
            'owner': self.creator,
            'task': self.phase.tasks.first(),
            'data': self.data,
        })

        new_task = TaskFactory()

        url = f"{reverse('submission-re-run-submission', args=(pre_existing_sub.pk,))}?task_key={new_task.key}"

        # Mock _send_to_compute_worker so submissions don't actually run
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            resp = self.client.post(url)
            assert resp.status_code == 403
            assert resp.data["detail"] == "You do not have permission to re-run submissions"


class SubmissionSoftDeletionTest(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.participant = UserFactory(username='participant', password='participant')

        self.leaderboard = LeaderboardFactory()
        self.comp = CompetitionFactory(created_by=self.creator)
        self.phase = PhaseFactory(competition=self.comp)

        # Approved participant
        CompetitionParticipantFactory(user=self.participant, competition=self.comp, status=CompetitionParticipant.APPROVED)

        # Submissions
        self.submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
            is_soft_deleted=False,
            leaderboard=None
        )

        self.leaderboard_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
            is_soft_deleted=False,
            leaderboard=self.leaderboard
        )

        self.running_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.SUBMITTED,
            is_soft_deleted=False,
            leaderboard=None
        )

        self.soft_deleted_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
            is_soft_deleted=True,
            leaderboard=None
        )

    def test_cannot_delete_submission_if_not_owner(self):
        """Ensure that a non-owner cannot soft delete a submission."""
        self.client.login(username="other_user", password="other")
        url = reverse("submission-soft-delete", args=[self.submission.pk])
        resp = self.client.delete(url)

        assert resp.status_code == 403
        assert resp.data["error"] == "You are not allowed to delete this submission"

    def test_cannot_delete_leaderboard_submission(self):
        """Ensure that a leaderboard submission cannot be deleted."""
        self.client.login(username="participant", password="participant")
        url = reverse("submission-soft-delete", args=[self.leaderboard_submission.pk])
        resp = self.client.delete(url)

        assert resp.status_code == 403
        assert resp.data["error"] == "You are not allowed to delete a leaderboard submission"

    def test_cannot_delete_running_submission(self):
        """Ensure that a running submission cannot be deleted."""
        self.client.login(username="participant", password="participant")
        url = reverse("submission-soft-delete", args=[self.running_submission.pk])
        resp = self.client.delete(url)

        assert resp.status_code == 403
        assert resp.data["error"] == "You are not allowed to delete a running submission"

    def test_cannot_delete_already_soft_deleted_submission(self):
        """Ensure that an already soft-deleted submission cannot be deleted again."""
        self.client.login(username="participant", password="participant")
        url = reverse("submission-soft-delete", args=[self.soft_deleted_submission.pk])
        resp = self.client.delete(url)

        assert resp.status_code == 400
        assert resp.data["error"] == "Submission already deleted"

    def test_can_soft_delete_submission_successfully(self):
        """Ensure a valid submission can be soft deleted successfully by its owner."""
        self.client.login(username="participant", password="participant")
        url = reverse("submission-soft-delete", args=[self.submission.pk])
        resp = self.client.delete(url)

        assert resp.status_code == 200
        assert resp.data["message"] == "Submission deleted successfully"

        # Refresh from DB to verify
        self.submission.refresh_from_db()
        assert self.submission.is_soft_deleted is True
