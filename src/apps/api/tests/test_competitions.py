import json
from unittest import mock

from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import CompetitionParticipant, Submission
from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionFactory, TaskFactory


class CompetitionParticipantTests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.other_user = UserFactory(username='other_user', password='other')
        self.comp = CompetitionFactory(created_by=self.creator)
        PhaseFactory(competition=self.comp)
        self.leaderboard = LeaderboardFactory(competition=self.comp)
        ColumnFactory(leaderboard=self.leaderboard)

    def _prepare_competition_data(self, url):
        resp = self.client.get(url)
        data = resp.data
        data.pop('id')

        # We don't want to post back the logo url, since it's expecting JSON data with
        # the base64 of the logo in it
        data["logo"] = None

        # Just get the key from the task and pass that instead of the object
        data["phases"][0]["tasks"] = [data["phases"][0]["tasks"][0]["key"]]
        return data

    # TODO: Do we have competition permissions tests?
    # def test_cant_edit_someone_elses_competition?

    def test_adding_organizer_creates_accepted_participant(self):
        self.client.login(username='creator', password='creator')
        url = reverse('competition-detail', kwargs={"pk": self.comp.pk})

        # Get comp data to work with
        data = self._prepare_competition_data(url)

        data["collaborators"] = [self.other_user.pk]
        resp = self.client.put(url, data=json.dumps(data), content_type="application/json")
        assert resp.status_code == 200
        assert CompetitionParticipant.objects.filter(
            user=self.other_user,
            competition=self.comp,
            status=CompetitionParticipant.APPROVED
        ).count() == 1

    def test_adding_organizer_accepts_them_if_they_were_existing_participant(self):
        CompetitionParticipantFactory(
            user=self.other_user,
            competition=self.comp,
            status=CompetitionParticipant.PENDING
        )
        self.client.login(username='creator', password='creator')
        url = reverse('competition-detail', kwargs={"pk": self.comp.pk})

        # Get comp data to work with
        data = self._prepare_competition_data(url)

        data["collaborators"] = [self.other_user.pk]
        resp = self.client.put(url, data=json.dumps(data), content_type="application/json")
        assert resp.status_code == 200
        assert CompetitionParticipant.objects.filter(
            user=self.other_user,
            competition=self.comp,
            status=CompetitionParticipant.APPROVED
        ).count() == 1


class PhaseMigrationTests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.other_user = UserFactory(username='other_user', password='other')
        self.comp = CompetitionFactory(created_by=self.creator)
        self.phase_1 = PhaseFactory(competition=self.comp, index=0)
        self.phase_2 = PhaseFactory(competition=self.comp, index=1)
        self.leaderboard = LeaderboardFactory(competition=self.comp)
        ColumnFactory(leaderboard=self.leaderboard)

    def test_manual_migration_checks_permissions_must_be_collaborator_to_migrate(self):
        self.client.login(username='other_user', password='other')

        url = reverse('phases-manually_migrate', kwargs={"pk": self.phase_1.pk})
        resp = self.client.post(url)
        assert resp.status_code == 403
        assert resp.data["detail"] == "You do not have administrative permissions for this competition"

        # add user as a collaborator and check they can do it
        self.comp.collaborators.add(self.other_user)
        resp = self.client.post(url)
        assert resp.status_code == 200

    def test_manual_migration_makes_submissions_from_one_phase_in_another(self):
        self.client.login(username='creator', password='creator')

        # make 5 submissions in phase 1
        for _ in range(5):
            SubmissionFactory(owner=self.creator, phase=self.phase_1, status=Submission.FINISHED)
        assert self.phase_1.submissions.count() == 5
        assert self.phase_2.submissions.count() == 0

        # call "migrate" from phase 1 -> 2
        with mock.patch("competitions.tasks.run_submission") as run_submission_mock:
            url = reverse('phases-manually_migrate', kwargs={"pk": self.phase_1.pk})
            resp = self.client.post(url)
            assert resp.status_code == 200
            assert run_submission_mock.call_count == 5

        # check phase 2 has the 5 submissions
        assert self.phase_1.submissions.count() == 5
        assert self.phase_2.submissions.count() == 5

    def test_manual_migration_makes_submissions_out_of_only_parents_not_children(self):
        self.client.login(username='creator', password='creator')

        # make 1 submission with 4 children
        parent = SubmissionFactory(owner=self.creator, phase=self.phase_1, has_children=True, status=Submission.FINISHED)
        for _ in range(4):
            # Make a submission _and_ new Task for phase 2
            self.phase_2.tasks.add(TaskFactory())
            SubmissionFactory(owner=self.creator, phase=self.phase_1, parent=parent, status=Submission.FINISHED)

        assert self.phase_1.submissions.count() == 5
        assert self.phase_2.submissions.count() == 0

        # call "migrate" from phase 1 -> 2
        with mock.patch("competitions.tasks.run_submission") as run_submission_mock:
            url = reverse('phases-manually_migrate', kwargs={"pk": self.phase_1.pk})
            resp = self.client.post(url)
            assert resp.status_code == 200
            # Only 1 run here because parent has to create children
            assert run_submission_mock.call_count == 1

        # check phase 2 has the 1 parent submission
        assert self.phase_1.submissions.count() == 5
        assert self.phase_2.submissions.count() == 1
