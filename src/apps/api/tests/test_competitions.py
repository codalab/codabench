import json
from unittest import mock

from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import CompetitionParticipant
from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionFactory


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

    def test_automigration_checks_permissions_must_be_collaborator_to_migrate(self):
        self.client.login(username='other_user', password='other')

        url = reverse('phases-manually_migrate', kwargs={"pk": self.phase_1.pk})
        resp = self.client.post(url)
        assert resp.status_code == 403
        assert resp.data["detail"] == "You do not have administrative permissions for this competition"

        # add user as a collaborator and check they can do it
        self.comp.collaborators.add(self.other_user)
        resp = self.client.post(url)
        assert resp.status_code == 200

    def test_automigration_makes_submissions_from_one_phase_in_another(self):
        self.client.login(username='creator', password='creator')

        # make 5 submissions in phase 1
        for _ in range(5):
            SubmissionFactory(owner=self.creator, phase=self.phase_1)
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
