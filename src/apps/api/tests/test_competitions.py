import json
import random
import csv
from zipfile import ZipFile
from io import StringIO, BytesIO
from unittest import mock
from django.urls import reverse
from rest_framework.test import APITestCase

from competitions.models import CompetitionParticipant, Submission
from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionFactory, SubmissionScoreFactory, TaskFactory


class CompetitionTests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.other_user = UserFactory(username='other_user', password='other')
        self.comp = CompetitionFactory(created_by=self.creator)
        self.leaderboard = LeaderboardFactory()
        PhaseFactory(competition=self.comp, leaderboard=self.leaderboard)
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
        self.leaderboard = LeaderboardFactory()
        self.phase_1 = PhaseFactory(competition=self.comp, leaderboard=self.leaderboard, index=0)
        self.phase_2 = PhaseFactory(competition=self.comp, leaderboard=self.leaderboard, index=1)
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
        self.client.login(username='creator2', password='creator2')
        self.comp = CompetitionFactory(created_by=self.creator)
        self.leaderboard = LeaderboardFactory(primary_index=0)
        self.phases = []
        for i in range(3):
           self.phases.append(PhaseFactory(leaderboard=self.leaderboard, leaderboard_id=self.leaderboard.id,  competition=self.comp, index=0))
        self.usernames = set()
        self.column_title_to_id = {}

        self.usernames.add(self.creator.username)
        self.users = [self.creator]
        for standard_users in range(5):
            user = UserFactory()
            self.users.append(user)
            self.usernames.add(user.username)

        self.columns = []
        self.tasks = []
        for i in range(4):
            column = ColumnFactory(leaderboard=self.leaderboard, index=i)
            self.columns.append(column)
            self.column_title_to_id.update({column.title: column.id})
            task = TaskFactory()
            self.tasks.append(task)
        for user in self.users:
            for phase in self.phases:
                for task in self.tasks:
                    phase.tasks.add(task)
                    submission = SubmissionFactory(owner=user, phase=phase, leaderboard=self.leaderboard, task=task)
                    for col in self.columns:
                        submission.scores.add(SubmissionScoreFactory(column=col))

    def test_get_competition_leaderboard_as_json(self):
        # gets makes sure to get JSON response and that it has all leaderboards and users
        url = reverse('competition-results', kwargs={"pk": self.comp.id})[0:-1] + '.json'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)

        self.response_titles = set()
        for key in content.keys():
            response_users = set()
            title, id = key.rsplit("(", 1)
            self.response_titles.add(title)
            for user in content[key].keys():
                response_users.add(user)
            print(f'{key} : {self.usernames} == {response_users}')
            assert self.usernames == response_users

        response_title = str(list(self.response_titles)[0]).split(' ')[0]
        assert self.leaderboard.title in response_title

    def test_get_competition_leaderboard_by_id_as_json(self):
        # Make sure when getting leaderboard by id you get exactly one leaderboard with matching title
        phase_choice = random.choice(self.phases)
        url = reverse('competition-results', kwargs={"pk": self.comp.id})[0:-1] + f'.json?phase={phase_choice.id}'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)

        response_title = list(content.keys())
        assert len(response_title) == 1
        assert response_title[0] == f'{self.leaderboard.title} - {phase_choice.name}({phase_choice.id})'

    def test_get_competition_leaderboard_by_id_as_csv(self):
        phase_choice = random.choice(self.phases).id
        url = reverse('competition-results', kwargs={"pk": self.comp.id})[0:-1] + f'.csv?phase={phase_choice}'
        response = self.client.get(url, HTTP_ACCEPT='text/csv')
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        csv_reader = csv.reader(StringIO(content))
        csv_header = list(csv_reader)[0]
        csv_header.pop(0)

        for task in self.tasks:
            for column in self.columns:
                assert f'{task.name}({task.id})-{column.title}' in csv_header

    def test_get_competition_leaderboard_as_zip(self):
        url = reverse('competition-results', kwargs={"pk": self.comp.id})[0:-1] + '.zip'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        assert response['content-type'] == 'application/x-zip-compressed'
        assert response['Content-Disposition'] == f'attachment; filename={self.comp.title}.zip'

        with BytesIO(response.content) as file:
            zipped_file = ZipFile(file, 'r')
            self.assertIsNone(zipped_file.testzip())
            for phase in self.phases:
                self.assertIn(f'{self.leaderboard.title} - {phase.name}({phase.id}).csv', zipped_file.namelist())
