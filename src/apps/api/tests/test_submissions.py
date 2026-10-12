import random
from datetime import timedelta
from unittest import mock

from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from competitions.models import Submission, CompetitionParticipant
from factories import UserFactory, CompetitionFactory, PhaseFactory, CompetitionParticipantFactory, SubmissionFactory, \
    TaskFactory, OrganizationFactory, DataFactory, LeaderboardFactory, ColumnFactory, SubmissionScoreFactory

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
        self.leaderboard = LeaderboardFactory()

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
            secret='7df3600c-1234-5678-bbc8-bbe91f42d875',
            leaderboard=None
        )

        # add submission with that is on the leaderboard (leaderboard submissions should always be finished)
        self.leaderboard_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
            leaderboard=self.leaderboard
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
        assert resp.data["detail"] == "You do not have permission to delete this submission!"

        # As regular user
        self.client.force_login(self.other_user)
        resp = self.client.delete(url)
        assert resp.status_code == 403
        assert resp.data["detail"] == "You do not have permission to delete this submission!"

    def test_can_delete_submission_you_created(self):
        url = reverse('submission-detail', args=(self.existing_submission.pk,))
        # As user who made submission
        self.client.force_login(self.participant)
        resp = self.client.delete(url)
        assert resp.status_code == 204
        assert not Submission.objects.filter(pk=self.existing_submission.pk).exists()

    def test_super_user_can_delete_submission_you_created(self):
        url = reverse('submission-detail', args=(self.existing_submission.pk,))

        self.client.force_login(self.superuser)
        resp = self.client.delete(url)
        assert resp.status_code == 204
        assert not Submission.objects.filter(pk=self.existing_submission.pk).exists()

    def test_super_user_can_delete_leaderboard_submission_you_created(self):
        url = reverse('submission-detail', args=(self.leaderboard_submission.pk,))

        self.client.force_login(self.superuser)
        resp = self.client.delete(url)
        assert resp.status_code == 204
        assert not Submission.objects.filter(pk=self.leaderboard_submission.pk).exists()

    def test_cannot_delete_leaderboard_submission_you_created(self):
        url = reverse('submission-detail', args=(self.leaderboard_submission.pk,))

        self.client.force_login(self.participant)
        resp = self.client.delete(url)

        assert resp.status_code == 403
        assert resp.data["detail"] == "You cannot delete a leaderboard submission!"

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

    def test_who_can_see_detailed_result_when_visualization_is_true_and_competition_is_private(self):
        self.comp.enable_detailed_results = True
        self.comp.published = False
        self.comp.save()

        url = reverse("submission-get-detail-result", args=(self.existing_submission.pk,))

        # Anonymous user cannot see submission detail result
        resp = self.client.get(url)
        assert resp.status_code == 403

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

        # Approved user can see submission detail result
        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Pending user cannot see submission detail result
        self.client.force_login(self.pending_participant)
        resp = self.client.get(url)
        assert resp.status_code == 403

        # Denied user cannot see submission detail result
        self.client.force_login(self.denied_participant)
        resp = self.client.get(url)
        assert resp.status_code == 403

        # Regular user cannot see submission detail result
        self.client.force_login(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == 403

    def test_who_can_see_detailed_result_when_visualization_is_true_and_competition_is_public(self):
        self.comp.enable_detailed_results = True
        self.comp.published = True
        self.comp.save()

        url = reverse("submission-get-detail-result", args=(self.existing_submission.pk,))

        # Detailed results are publicly available
        resp = self.client.get(url)
        assert resp.status_code == 200

        self.client.force_login(self.creator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        self.client.force_login(self.collaborator)
        resp = self.client.get(url)
        assert resp.status_code == 200

        self.client.force_login(self.superuser)
        resp = self.client.get(url)
        assert resp.status_code == 200

        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 200

        self.client.force_login(self.pending_participant)
        resp = self.client.get(url)
        assert resp.status_code == 200

        self.client.force_login(self.denied_participant)
        resp = self.client.get(url)
        assert resp.status_code == 200

        self.client.force_login(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == 200

    def test_anonymous_cannot_list_or_retrieve_submissions(self):
        """
        SubmissionViewSet's general list/retrieve endpoints must not leak submission
        data to anonymous users, even for a finished submission on a leaderboard.
        Public leaderboard data is meant to be served only through
        PhaseViewSet.get_leaderboard, which uses a restricted serializer.
        """
        # List: the leaderboard submission must not appear
        resp = self.client.get(reverse('submission-list'))
        assert resp.status_code == 200
        results = resp.data.get('results', resp.data)
        assert all(item['id'] != self.leaderboard_submission.pk for item in results)

        # Retrieve: must 404, not leak the record
        url = reverse('submission-detail', args=(self.leaderboard_submission.pk,))
        resp = self.client.get(url)
        assert resp.status_code == 404


class SubmissionGetDetailsAPITests(APITestCase):
    def setUp(self):
        self.superuser = UserFactory(is_superuser=True, is_staff=True)

        # Competition and creator
        self.creator = UserFactory(username='creator', password='creator')
        self.collaborator = UserFactory(username='collab', password='collab')
        self.comp = CompetitionFactory(created_by=self.creator, collaborators=[self.collaborator])
        self.phase = PhaseFactory(competition=self.comp)
        self.leaderboard = LeaderboardFactory()

        # Extra dummy user to test permissions, they shouldn't have access to many things
        self.other_user = UserFactory(username='other_user', password='other')

        # Make participant
        self.participant = UserFactory(username='participant_approved', password='other')
        CompetitionParticipantFactory(user=self.participant, competition=self.comp, status=CompetitionParticipant.APPROVED)

        # add submission with owner = approved participant
        self.existing_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.SUBMITTED,
            secret='7df3600c-1234-5678-bbc8-bbe91f42d875',
            leaderboard=None
        )

        # add submission with that is on the leaderboard
        self.leaderboard_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
            leaderboard=self.leaderboard
        )

    def test_cannot_get_details_of_submission_unless_creator_collab_or_superuser(self):
        """
        Uses a submission that is NOT on a leaderboard.
        Expect only the owner, creator, collaborator, or superuser to get details; everyone else gets 404.
        """
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
        """
        Uses a submission that is NOT on a leaderboard, with phase.hide_output set.
        Expect hide_output to block even the owner, while admins still get through.
        """
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

    def test_anonymous_cannot_get_details_of_finished_leaderboard_submission(self):
        """
        Unlike the two tests above, uses a finished submission that IS on a leaderboard.
        Being on a leaderboard must not make submission details reachable by anonymous users.

        SubmissionViewSet.get_queryset() in src/apps/api/views/submissions.py returns an
        empty queryset for unauthenticated GET requests, so get_details' super().get_object()
        never finds the submission and we get a 404 (rather than a 403 confirming it exists).
        Public leaderboard data is served separately by PhaseViewSet.get_leaderboard.
        """
        url = reverse('submission-get-details', args=(self.leaderboard_submission.pk,))

        # Anonymous: filtered out at the queryset level, existence is not leaked
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Non-owner, non-admin authenticated user: filtered out at the queryset level
        self.client.force_login(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == 404

        # Owner can still see it (hide_output is False)
        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 200

        # Admin (competition creator) can still see it
        self.client.force_login(self.creator)
        resp = self.client.get(url)
        assert resp.status_code == 200

    def test_get_details_returns_detailed_result_when_detailed_results_enabled(self):
        """
        Uses a submission that has a detailed result file, with enable_detailed_results set.
        Expect the detailed result url in the response.
        """
        self.comp.enable_detailed_results = True
        self.comp.save()
        Submission.objects.filter(pk=self.existing_submission.pk).update(detailed_result='detailed_result/test.html')
        url = reverse('submission-get-details', args=(self.existing_submission.pk,))

        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data['detailed_result'] is not None

    def test_get_details_does_not_return_detailed_result_when_detailed_results_disabled(self):
        """
        Uses a submission that has a detailed result file, with enable_detailed_results not set.
        Expect no detailed result url in the response.
        """
        self.comp.enable_detailed_results = False
        self.comp.save()
        Submission.objects.filter(pk=self.existing_submission.pk).update(detailed_result='detailed_result/test.html')
        url = reverse('submission-get-details', args=(self.existing_submission.pk,))

        self.client.force_login(self.participant)
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data['detailed_result'] is None


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

    def test_cannot_re_run_submissions_with_specific_task_without_permission(self):
        other_user = UserFactory(username="otheruser", password="otheruser")
        self.client.login(username=other_user.username, password="otheruser")

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
        self.organization = OrganizationFactory()

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

        self.organization_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
            is_soft_deleted=False,
            leaderboard=None,
            organization=self.organization
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

    def test_organization_is_removed_from_soft_deleted_submission(self):
        """Ensure a organization reference is removed from soft-deleted submission"""
        self.client.login(username="participant", password="participant")
        url = reverse("submission-soft-delete", args=[self.organization_submission.pk])
        resp = self.client.delete(url)

        assert resp.status_code == 200
        assert resp.data["message"] == "Submission deleted successfully"

        # Refresh from DB to verify
        self.organization_submission.refresh_from_db()
        assert self.organization_submission.is_soft_deleted is True
        assert self.organization_submission.organization is None


class PhaseActiveSubmissionTests(APITestCase):
    """a submission must only be creatable while its phase is active
    (has started and, if it has an end date, has not ended)."""

    def setUp(self):
        self.creator = UserFactory()
        self.comp = CompetitionFactory(created_by=self.creator)
        self.participant = UserFactory()
        CompetitionParticipantFactory(user=self.participant, competition=self.comp, status=CompetitionParticipant.APPROVED)
        self.dataset = DataFactory(type='submission', created_by=self.participant)
        self.url_submission = reverse('submission-list')

    def post_submission(self, phase):
        self.client.force_login(user=self.participant)
        data = {'phase': phase.id, 'data': self.dataset.key}
        # Mock _send_to_compute_worker so submissions don't actually run
        with mock.patch('competitions.tasks._send_to_compute_worker'):
            return self.client.post(self.url_submission, data=data)

    def test_cannot_submit_before_phase_starts(self):
        phase = PhaseFactory(competition=self.comp, start=now() + timedelta(days=1), end=None)
        resp = self.post_submission(phase)
        assert resp.status_code == 400
        assert "This phase is not currently accepting submissions." in str(resp.data)

    def test_cannot_submit_before_phase_starts_even_with_end_date_set(self):
        phase = PhaseFactory(
            competition=self.comp,
            start=now() + timedelta(days=1),
            end=now() + timedelta(days=2),
        )
        resp = self.post_submission(phase)
        assert resp.status_code == 400
        assert "This phase is not currently accepting submissions." in str(resp.data)

    def test_cannot_submit_after_phase_ends(self):
        phase = PhaseFactory(
            competition=self.comp,
            start=now() - timedelta(days=2),
            end=now() - timedelta(days=1),
        )
        resp = self.post_submission(phase)
        assert resp.status_code == 400
        assert "This phase is not currently accepting submissions." in str(resp.data)

    def test_can_submit_during_active_phase_with_no_end_date(self):
        phase = PhaseFactory(competition=self.comp, start=now() - timedelta(days=1), end=None)
        resp = self.post_submission(phase)
        assert resp.status_code == 201

    def test_can_submit_during_active_phase_with_future_end_date(self):
        phase = PhaseFactory(
            competition=self.comp,
            start=now() - timedelta(days=1),
            end=now() + timedelta(days=1),
        )
        resp = self.post_submission(phase)
        assert resp.status_code == 201


def fake_make_url_sassy(path):
    return f"https://storage/{path}"


@mock.patch('api.serializers.submissions.make_url_sassy', fake_make_url_sassy)
class SubmissionBulkDownloadTests(APITestCase):
    """
    Tests for the bulk download endpoints of SubmissionViewSet:
    download_many_submissions, download_many_prediction_results and download_many_scoring_results.
    make_url_sassy is mocked so that each URL is predictable and contains the file path.
    """

    def setUp(self):
        self.superuser = UserFactory(is_superuser=True, is_staff=True)
        self.creator = UserFactory(username='creator')
        self.collaborator = UserFactory(username='collab')
        self.participant = UserFactory(username='participant')
        self.other_user = UserFactory(username='other_user')

        self.comp = CompetitionFactory(created_by=self.creator, collaborators=[self.collaborator])
        self.phase = PhaseFactory(competition=self.comp)

        # Result files are only referenced by path, they don't exist in the storage.
        # File sizes are set so that Submission.save() doesn't try to read them from the storage.
        # Finished submission with both result files
        self.finished_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
            prediction_result='prediction_result/finished_prediction.zip',
            prediction_result_file_size=1,
            scoring_result='scoring_result/finished_scoring.zip',
            scoring_result_file_size=1,
        )
        # Failed submission with result files, which must not be included in results downloads
        self.failed_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FAILED,
            prediction_result='prediction_result/failed_prediction.zip',
            prediction_result_file_size=1,
            scoring_result='scoring_result/failed_scoring.zip',
            scoring_result_file_size=1,
        )
        # Finished submission without any result files
        self.no_results_submission = SubmissionFactory(
            phase=self.phase,
            owner=self.participant,
            status=Submission.FINISHED,
        )
        # Submission of another user in another competition
        self.other_submission = SubmissionFactory(owner=self.other_user, status=Submission.FINISHED)

        self.participant_pks = [
            self.finished_submission.pk,
            self.failed_submission.pk,
            self.no_results_submission.pk,
        ]

        self.submissions_url = reverse('submission-download-many-submissions')
        self.prediction_results_url = reverse('submission-download-many-prediction-results')
        self.scoring_results_url = reverse('submission-download-many-scoring-results')
        self.all_urls = [self.submissions_url, self.prediction_results_url, self.scoring_results_url]

    def download(self, url, pks):
        return self.client.post(url, {'pks': pks}, format='json')

    # ------------------------------------------------------------------
    # Validation and permissions (shared by all three endpoints)
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_download(self):
        """Anonymous user calls all three bulk download endpoints. Expect 403 from each."""
        for url in self.all_urls:
            resp = self.download(url=url, pks=self.participant_pks)
            assert resp.status_code == 403

    def test_pks_is_required(self):
        """Request with an empty `pks` list. Expect 400 with a "`pks` field is required" error."""
        self.client.force_login(self.participant)
        resp = self.download(url=self.submissions_url, pks=[])
        assert resp.status_code == 400
        assert resp.data['error'] == '`pks` field is required'

    def test_pks_must_be_a_list(self):
        """Request with a single id instead of a list. Expect 400 with a "`pks` must be a list" error."""
        self.client.force_login(self.participant)
        resp = self.download(url=self.submissions_url, pks=self.finished_submission.pk)
        assert resp.status_code == 400
        assert resp.data['error'] == '`pks` must be a list'

    def test_invalid_submission_id_returns_404(self):
        """Request with one valid and one non-existent submission id. Expect 404."""
        self.client.force_login(self.participant)
        resp = self.download(url=self.submissions_url, pks=[self.finished_submission.pk, 999999])
        assert resp.status_code == 404

    def test_owner_creator_collaborator_and_superuser_can_download(self):
        """Submission owner, competition creator, collaborator and superuser download submissions. Expect 200 for each."""
        for user in [self.participant, self.creator, self.collaborator, self.superuser]:
            self.client.force_login(user)
            resp = self.download(url=self.submissions_url, pks=self.participant_pks)
            assert resp.status_code == 200

    def test_other_user_cannot_download(self):
        """User who is neither owner nor organizer calls all three endpoints. Expect 403 from each."""
        self.client.force_login(self.other_user)
        for url in self.all_urls:
            resp = self.download(url=url, pks=self.participant_pks)
            assert resp.status_code == 403

    def test_cannot_download_if_any_submission_is_not_allowed(self):
        """Participant requests their own submission together with another user's. Expect 403 for the whole request."""
        self.client.force_login(self.participant)
        resp = self.download(
            url=self.submissions_url,
            pks=[self.finished_submission.pk, self.other_submission.pk],
        )
        assert resp.status_code == 403

    def test_organizer_cannot_download_files_of_another_competition(self):
        """Competition creator calls all three endpoints for a submission from a competition they don't organize. Expect 403 from each."""
        self.client.force_login(self.creator)
        for url in self.all_urls:
            resp = self.download(url=url, pks=[self.other_submission.pk])
            assert resp.status_code == 403

    # ------------------------------------------------------------------
    # Downloaded files
    # ------------------------------------------------------------------

    def test_download_submissions_includes_all_statuses(self):
        """
        Participant downloads finished, failed and result-less submissions.
        Expect all 3 submission files, each named with the `sub_` prefix and pointing to its data file.
        """
        self.client.force_login(self.participant)
        resp = self.download(url=self.submissions_url, pks=self.participant_pks)
        assert resp.status_code == 200
        assert len(resp.data) == 3

        files_by_id = {int(f['name'].split('_')[1]): f for f in resp.data}
        assert set(files_by_id) == set(self.participant_pks)
        for sub in [self.finished_submission, self.failed_submission, self.no_results_submission]:
            file = files_by_id[sub.pk]
            assert file['name'].startswith(f"sub_{sub.pk}_")
            assert file['url'] == f"https://storage/{sub.data.data_file.name}"

    def test_download_prediction_results_only_includes_finished_submissions_with_a_file(self):
        """
        Participant downloads prediction results of finished, failed and result-less submissions.
        Expect only the finished submission's prediction result, named with the `pred_res_` prefix.
        """
        self.client.force_login(self.participant)
        resp = self.download(url=self.prediction_results_url, pks=self.participant_pks)
        assert resp.status_code == 200
        assert len(resp.data) == 1

        file = resp.data[0]
        assert file['name'].startswith(f"pred_res_{self.finished_submission.pk}_")
        assert file['name'].endswith('finished_prediction.zip')
        assert file['url'] == 'https://storage/prediction_result/finished_prediction.zip'

    def test_download_scoring_results_only_includes_finished_submissions_with_a_file(self):
        """
        Participant downloads scoring results of finished, failed and result-less submissions.
        Expect only the finished submission's scoring result, named with the `sco_res_` prefix.
        """
        self.client.force_login(self.participant)
        resp = self.download(url=self.scoring_results_url, pks=self.participant_pks)
        assert resp.status_code == 200
        assert len(resp.data) == 1

        file = resp.data[0]
        assert file['name'].startswith(f"sco_res_{self.finished_submission.pk}_")
        assert file['name'].endswith('finished_scoring.zip')
        assert file['url'] == 'https://storage/scoring_result/finished_scoring.zip'

    # ------------------------------------------------------------------
    # Phase output visibility
    # ------------------------------------------------------------------

    def test_hide_output_hides_results_from_participant_but_not_submissions(self):
        """
        Phase has hide_output set and the participant downloads all three file types.
        Expect empty lists for prediction and scoring results, but all 3 submission files.
        """
        self.phase.hide_output = True
        self.phase.save()
        self.client.force_login(self.participant)

        resp = self.download(url=self.prediction_results_url, pks=self.participant_pks)
        assert resp.status_code == 200
        assert resp.data == []

        resp = self.download(url=self.scoring_results_url, pks=self.participant_pks)
        assert resp.status_code == 200
        assert resp.data == []

        # The submitted files themselves are never hidden from their owner
        resp = self.download(url=self.submissions_url, pks=self.participant_pks)
        assert resp.status_code == 200
        assert len(resp.data) == 3

    def test_hide_output_does_not_hide_results_from_organizers(self):
        """
        Phase has hide_output set and creator, collaborator and superuser download results.
        Expect each of them to still get the finished submission's prediction and scoring result.
        """
        self.phase.hide_output = True
        self.phase.save()

        for user in [self.creator, self.collaborator, self.superuser]:
            self.client.force_login(user)
            resp = self.download(url=self.prediction_results_url, pks=self.participant_pks)
            assert len(resp.data) == 1
            resp = self.download(url=self.scoring_results_url, pks=self.participant_pks)
            assert len(resp.data) == 1

    def test_hide_prediction_output_only_hides_prediction_results(self):
        """
        Phase has hide_prediction_output set and the participant downloads results.
        Expect no prediction results, but the scoring result is still returned.
        """
        self.phase.hide_prediction_output = True
        self.phase.save()
        self.client.force_login(self.participant)

        resp = self.download(url=self.prediction_results_url, pks=self.participant_pks)
        assert resp.data == []

        resp = self.download(url=self.scoring_results_url, pks=self.participant_pks)
        assert len(resp.data) == 1

    def test_hide_score_output_only_hides_scoring_results(self):
        """
        Phase has hide_score_output set and the participant downloads results.
        Expect no scoring results, but the prediction result is still returned.
        """
        self.phase.hide_score_output = True
        self.phase.save()
        self.client.force_login(self.participant)

        resp = self.download(url=self.scoring_results_url, pks=self.participant_pks)
        assert resp.data == []

        resp = self.download(url=self.prediction_results_url, pks=self.participant_pks)
        assert len(resp.data) == 1


class HiddenColumnSubmissionScoreTests(APITestCase):
    """
    Column.hidden is meant to hide a score from everyone
    (e.g. so participants can't tune submissions against it), so a hidden
    column's score must never appear in the submission-list
    (`/api/submissions/?phase=<id>`) or submission-detail
    (`/api/submissions/<pk>/`) responses, for any viewer - the submission's
    own owner, or organizer/admin alike - consistent with how hidden columns
    are already excluded from leaderboard column metadata.
    (Previously SubmissionSerializer.scores serialized every SubmissionScore
    row with no awareness of Column.hidden, so hidden-column values leaked
    to anyone who could see the submission at all.)

    Anonymous viewers aren't covered here: SubmissionViewSet.get_queryset
    returns nothing at all to them, tested separately by
    test_anonymous_cannot_list_or_retrieve_submissions.
    """

    def setUp(self):
        self.creator = UserFactory(username='hcss_creator', password='test')
        self.superuser = UserFactory(username='hcss_admin', password='test', is_superuser=True, is_staff=True)
        self.owner = UserFactory(username='hcss_owner', password='test')
        self.comp = CompetitionFactory(created_by=self.creator)
        self.leaderboard = LeaderboardFactory(primary_index=0)
        self.phase = PhaseFactory(competition=self.comp, leaderboard=self.leaderboard)

        CompetitionParticipantFactory(user=self.owner, competition=self.comp, status=CompetitionParticipant.APPROVED)

        self.visible_column = ColumnFactory(leaderboard=self.leaderboard, index=0, key='visible_col', hidden=False)
        self.hidden_column = ColumnFactory(leaderboard=self.leaderboard, index=1, key='hidden_col', hidden=True)

        # status=FINISHED and leaderboard=self.leaderboard put the submission in
        # its most-exposed state (on a leaderboard, done running); what must stay
        # hidden is the hidden column's score within it, not the submission itself.
        self.submission = SubmissionFactory(
            phase=self.phase,
            owner=self.owner,
            leaderboard=self.leaderboard,
            status=Submission.FINISHED,
        )
        SubmissionScoreFactory(submissions=[self.submission], column=self.visible_column)
        SubmissionScoreFactory(submissions=[self.submission], column=self.hidden_column)

    def score_column_keys_from_list(self, resp):
        body = resp.json()
        submissions = body.get('results', body)
        matching = [s for s in submissions if s['id'] == self.submission.id]
        assert len(matching) == 1
        return {score['column_key'] for score in matching[0]['scores']}

    def score_column_keys_from_detail(self, resp):
        return {score['column_key'] for score in resp.json()['scores']}

    def test_submission_owner_does_not_see_hidden_column_score_in_submission_list(self):
        """
        A GET on submission-list as the submission owner, filtered to the
        submission's phase, must not include the hidden column's score.
        Expected: only the visible column's score is present in the
        submission's scores array.
        """
        self.client.force_login(self.owner)
        url = reverse('submission-list')
        resp = self.client.get(url, {'phase': self.phase.id})
        assert resp.status_code == 200
        keys = self.score_column_keys_from_list(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys

    def test_submission_owner_does_not_see_hidden_column_score(self):
        """
        The submission owner is exactly the kind of participant an organizer
        wants to keep a hidden metric from, so even the owner viewing their
        own submission must not see the hidden column's score. Expected: only
        the visible column's score is present.
        """
        self.client.force_login(self.owner)
        url = reverse('submission-detail', args=(self.submission.pk,))
        resp = self.client.get(url)
        assert resp.status_code == 200
        keys = self.score_column_keys_from_detail(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys

    def test_competition_creator_does_not_see_hidden_column_score(self):
        """
        For consistency with how hidden columns are excluded from leaderboard
        column metadata for everyone, the competition creator must not see
        the hidden column's score via submission-detail either. Expected:
        only the visible column's score is present.
        """
        self.client.force_login(self.creator)
        url = reverse('submission-detail', args=(self.submission.pk,))
        resp = self.client.get(url)
        assert resp.status_code == 200
        keys = self.score_column_keys_from_detail(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys

    def test_superuser_does_not_see_hidden_column_score(self):
        """
        Even a superuser/site-admin must not see the hidden column's score
        via submission-detail, for the same consistency reason. Expected:
        only the visible column's score is present.
        """
        self.client.force_login(self.superuser)
        url = reverse('submission-detail', args=(self.submission.pk,))
        resp = self.client.get(url)
        assert resp.status_code == 200
        keys = self.score_column_keys_from_detail(resp)
        assert self.hidden_column.key not in keys
        assert self.visible_column.key in keys
