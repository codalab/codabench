import json
from unittest import mock
import random
from django.urls import reverse
from django.test import Client
from rest_framework.test import APITestCase

from competitions.models import CompetitionParticipant, Submission
from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionFactory, SubmissionScoreFactory, TaskFactory


class CompetitionTests(APITestCase):
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


class CompetitionResultDatatypesTests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator2', password='creator2')
        self.comp = CompetitionFactory(created_by=self.creator)
        self.phase = PhaseFactory(competition=self.comp, index=0)

        self.leaderboard_titles = set()
        self.usernames = set()
        self.leaderboard_ids_to_titles = {}

        self.usernames.add(self.creator.username)
        self.users = [self.creator]
        for standard_users in range(5):
            user = UserFactory()
            self.users.append(user)
            self.usernames.add(user.username)


        for leaderboards in range(3):
            leaderboard = LeaderboardFactory(competition=self.comp)
            self.leaderboard_titles.add(leaderboard.title)
            self.leaderboard_ids_to_titles.update({leaderboard.id : leaderboard.title})
            self.columns = []
            for column in range(4):
                self.columns.append(ColumnFactory(leaderboard=leaderboard))
            for user in self.users:
                submission = SubmissionFactory(owner=user, phase=self.phase ,leaderboard=leaderboard)
                for col in self.columns:
                    submission.scores.add(SubmissionScoreFactory(column=col))


    def test_get_competition_leaderboard_as_json(self):
        # gets makes sure to get JSON response and that it has all leaderboards and users
        c = Client()
        c.login(username="creator2", password="creator2")
        response = json.loads(c.get(f'/api/competitions/{self.comp.id}/results.json', HTTP_ACCEPT='application/json').content)
        self.response_titles  = set()
        self.response_users = set()
        for key in response.keys():
            title, id = key.rsplit("(", 1)
            self.response_titles.add(title)
            for user in response[key].keys():
                self.response_users.add(user)
        assert self.leaderboard_titles == self.response_titles
        assert self.usernames == self.response_users

    def test_get_competition_leaderboard_by_title_as_json(self):
        # Makes sure the query returns a json that had a matching leaderboard title
        c = Client()
        c.login(username="creator2", password="creator2")
        leaderboard_choice = random.sample(self.leaderboard_titles, 1)[0]
        response = json.loads(c.get(f'/api/competitions/{self.comp.id}/results.json?title={leaderboard_choice}', HTTP_ACCEPT='application/json').content)
        for title in response.keys():
            assert leaderboard_choice in title

    def test_get_competition_leaderboard_by_id_as_json(self):
        # Make sure when getting leaderboard by id you get exactly one leaderboard with matching title
        c = Client()
        c.login(username="creator2", password="creator2")
        leaderboard_choice = random.choice(list(self.leaderboard_ids_to_titles.keys()))
        response = json.loads(c.get(f'/api/competitions/{self.comp.id}/results.json?id={leaderboard_choice}', HTTP_ACCEPT='application/json').content)
        response_title = list(response.keys())
        assert len(response_title) == 1
        assert response_title[0] == f'{self.leaderboard_ids_to_titles[leaderboard_choice]}({leaderboard_choice})'

    def test_get_competition_leaderboard_by_id_as_csv(self):
        c = Client()
        c.login(username="creator2", password="creator2")
        leaderboard_choice = random.choice(list(self.leaderboard_ids_to_titles.keys()))
        response = c.get(f'/api/competitions/{self.comp.id}/results.csv?id={leaderboard_choice}', HTTP_ACCEPT='text/csv')
        content = response.content.decode('utf-8')
        print(content)

        assert 0 == 1

    def test_get_competition_leaderboard_by_title_as_csv(self):
        return
