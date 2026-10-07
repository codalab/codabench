import json
import random
import csv
import uuid
from zipfile import ZipFile
from io import StringIO, BytesIO
from unittest import mock
from urllib.parse import urlencode
from django.urls import reverse
from rest_framework.test import APITestCase

from api.serializers.competitions import CompetitionSerializer, CompetitionDetailSerializer
from competitions.models import CompetitionParticipant, Submission, Competition, CompetitionCreationTaskStatus, \
    CompetitionDump, SubmissionDetails, Phase, PhaseTaskInstance, Page, CompetitionWhiteListEmail
from datasets.models import Data
from django.contrib.auth.models import Group
from forums.models import Forum, Thread, Post
from leaderboards.models import Leaderboard, Column, SubmissionScore
from profiles.models import CustomGroup, User
from tasks.models import Task, Solution
from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory, PhaseFactory, LeaderboardFactory, \
    ColumnFactory, SubmissionFactory, SubmissionScoreFactory, TaskFactory, QueueFactory, DataFactory, SolutionFactory


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

    def test_delete_own_competition(self):
        self.client.login(username='creator', password='creator')
        url = reverse('competition-detail', kwargs={"pk": self.comp.pk})
        resp = self.client.delete(url)
        assert resp.status_code == 204
        assert not Competition.objects.filter(pk=self.comp.pk).exists()


class CompetitionDeleteTestBase(APITestCase):
    """
    Shared setup for the competition delete and delete preview tests: a competition with everything the delete
    touches - a logo, two phases sharing a task with its four datasets and a solution, phase datasets,
    a leaderboard, a bundle, a dump, a parent and a child submission with result files, logs and a score,
    a zip uploaded without a submission, a participant, a participant group, a page, a forum with a thread
    and a post, and a whitelist email.
    """

    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.other_user = UserFactory(username='other_user', password='other')
        self.collaborator = UserFactory(username='collab', password='collab')
        self.superuser = UserFactory(username='admin', password='admin', super_user=True)
        self.comp = CompetitionFactory(created_by=self.creator, collaborators=[self.collaborator])

        self.leaderboard = LeaderboardFactory()
        self.column = ColumnFactory(leaderboard=self.leaderboard)

        self.task = TaskFactory(
            created_by=self.creator,
            ingestion_program=self._data(Data.INGESTION_PROGRAM),
            scoring_program=self._data(Data.SCORING_PROGRAM),
            input_data=self._data(Data.INPUT_DATA),
            reference_data=self._data(Data.REFERENCE_DATA),
        )
        self.solution = SolutionFactory(data=self._data(Data.SOLUTION))
        self.solution.tasks.add(self.task)

        self.public_data = self._data(Data.PUBLIC_DATA)
        self.starting_kit = self._data(Data.STARTING_KIT)
        self.phase = PhaseFactory(
            competition=self.comp,
            leaderboard=self.leaderboard,
            tasks=[self.task],
            public_data=self.public_data,
            starting_kit=self.starting_kit,
        )
        # A second phase using the same task, as in a bundle where a task runs in several phases
        self.phase_2 = PhaseFactory(competition=self.comp, leaderboard=self.leaderboard, tasks=[self.task])

        self.bundle = self._data(Data.COMPETITION_BUNDLE)
        CompetitionCreationTaskStatus.objects.create(
            dataset=self.bundle, resulting_competition=self.comp, status=CompetitionCreationTaskStatus.FINISHED,
        )
        self.dump_data = self._data(Data.COMPETITION_BUNDLE)
        self.dump = CompetitionDump.objects.create(competition=self.comp, dataset=self.dump_data)

        self.submission = SubmissionFactory(
            owner=self.creator,
            phase=self.phase,
            leaderboard=self.leaderboard,
            task=self.task,
            data=self._data(Data.SUBMISSION),
            prediction_result='prediction_result/prediction_result.zip',
            prediction_result_file_size=10,
            scoring_result='scoring_result/scoring_result.zip',
            scoring_result_file_size=10,
            detailed_result='detailed_result/detailed_results.html',
            detailed_result_file_size=10,
        )
        self.detail = SubmissionDetails.objects.create(
            submission=self.submission, name='prediction_stdout',
            data_file='submission_details/prediction_stdout.txt', file_size=10,
        )
        self.score = SubmissionScoreFactory(column=self.column, submissions=self.submission)
        # A child submission (the run of one task) shares the parent's zip and has its own result files and log
        self.child_submission = SubmissionFactory(
            owner=self.creator,
            phase=self.phase,
            parent=self.submission,
            leaderboard=None,
            task=self.task,
            data=self.submission.data,
            prediction_result='prediction_result/child_prediction_result.zip',
            prediction_result_file_size=10,
            scoring_result='scoring_result/child_scoring_result.zip',
            scoring_result_file_size=10,
            detailed_result='detailed_result/child_detailed_results.html',
            detailed_result_file_size=10,
        )
        self.child_detail = SubmissionDetails.objects.create(
            submission=self.child_submission, name='prediction_stdout',
            data_file='submission_details/child_prediction_stdout.txt', file_size=10,
        )
        # A zip uploaded through the competition's submit form whose submission was never created
        self.uploaded_zip = DataFactory(
            type=Data.SUBMISSION, created_by=self.other_user, competition=self.comp,
            data_file='dataset/uploaded_submission.zip', file_size=10,
        )

        self.participant = CompetitionParticipantFactory(
            user=self.other_user, competition=self.comp, status=CompetitionParticipant.APPROVED,
        )
        self.group = CustomGroup.objects.create(name='Delete test group')
        self.group.user_set.add(self.other_user)
        self.comp.participant_groups.add(self.group)
        self.page = Page.objects.create(competition=self.comp, title='Overview', content='Overview', index=0)
        self.forum = Forum.objects.create(competition=self.comp)
        self.thread = Thread.objects.create(forum=self.forum, started_by=self.other_user, title='Question')
        self.post = Post.objects.create(thread=self.thread, posted_by=self.other_user, content='Hello')
        self.whitelist_email = CompetitionWhiteListEmail.objects.create(
            competition=self.comp, email='invited@example.com',
        )

    def _data(self, data_type):
        """Creates a dataset whose file name is only stored, not uploaded"""
        return DataFactory(
            type=data_type, created_by=self.creator, data_file=f'dataset/{data_type}.zip', file_size=10,
        )

    def _other_phase(self, **kwargs):
        """Creates a phase in another competition, with no tasks unless given"""
        kwargs.setdefault('tasks', [])
        return PhaseFactory(competition=CompetitionFactory(), **kwargs)


class CompetitionDeleteTests(CompetitionDeleteTestBase):
    """Tests for deleting a competition: who can delete it, which records are deleted or kept and which files are queued"""

    def _delete(self, user=None, **params):
        """Deletes the competition as `user` and returns the response and the mocked file deletion task"""
        if user:
            self.client.force_login(user)
        url = reverse('competition-detail', kwargs={'pk': self.comp.pk})
        # The celery task is replaced by a mock: no file is deleted, and the mock records
        # the arguments it is called with, so tests can check which files would be deleted
        with mock.patch('competitions.deletion.delete_storage_files') as delete_files:
            # The delete queues the task with transaction.on_commit, which only runs after a real commit.
            # Tests run inside a transaction that is never committed (it is rolled back after each test),
            # so the callback would never run. captureOnCommitCallbacks(execute=True) runs it at the end
            # of this block, as if the transaction had been committed.
            with self.captureOnCommitCallbacks(execute=True):
                resp = self.client.delete(f'{url}?{urlencode(params)}')
        return resp, delete_files

    @staticmethod
    def _queued_file_names(delete_files, file_type=None):
        """
        Returns the names of the files passed to the file deletion task: of all file types,
        or only of `file_type` (e.g. 'task datasets') when given
        """
        files = delete_files.delay.call_args.kwargs['files']
        if file_type:
            return {file_name for _, _, file_name in files.get(file_type, [])}
        return {file_name for entries in files.values() for _, _, file_name in entries}

    def test_non_creators_cannot_delete_competition(self):
        """Other users, collaborators, superusers and anonymous users get 403 and the competition stays"""
        for user in [None, self.other_user, self.collaborator, self.superuser]:
            self.client.logout()
            resp, delete_files = self._delete(user=user)
            assert resp.status_code == 403
            # Checks that the file deletion task was never queued: a refused request must not touch storage.
            # If the mocked .delay was called even once, the assertion fails and so does the test.
            delete_files.delay.assert_not_called()
        assert Competition.objects.filter(pk=self.comp.pk).exists()

    def test_delete_removes_competition_records(self):
        """
        Deleting removes the competition records: phases, submissions with their logs and scores, leaderboard,
        columns, bundle, dump, submission zips, participants, participant group, page, forum and whitelist email.
        User accounts are kept.
        """
        resp, _ = self._delete(user=self.creator)
        assert resp.status_code == 204
        assert not Competition.objects.filter(pk=self.comp.pk).exists()
        assert not Phase.objects.filter(pk__in=[self.phase.pk, self.phase_2.pk]).exists()
        assert not PhaseTaskInstance.objects.filter(task=self.task).exists()
        assert not Submission.objects.filter(pk__in=[self.submission.pk, self.child_submission.pk]).exists()
        assert not SubmissionDetails.objects.filter(pk__in=[self.detail.pk, self.child_detail.pk]).exists()
        assert not SubmissionScore.objects.filter(pk=self.score.pk).exists()
        assert not Leaderboard.objects.filter(pk=self.leaderboard.pk).exists()
        assert not Column.objects.filter(pk=self.column.pk).exists()
        assert not CompetitionDump.objects.filter(pk=self.dump.pk).exists()
        assert not Data.objects.filter(
            pk__in=[self.bundle.pk, self.dump_data.pk, self.submission.data_id, self.uploaded_zip.pk]
        ).exists()
        assert not CompetitionParticipant.objects.filter(competition_id=self.comp.pk).exists()
        assert not CustomGroup.objects.filter(pk=self.group.pk).exists()
        assert not Group.objects.filter(pk=self.group.pk).exists()
        assert not Page.objects.filter(pk=self.page.pk).exists()
        assert not Forum.objects.filter(pk=self.forum.pk).exists()
        assert not Thread.objects.filter(pk=self.thread.pk).exists()
        assert not Post.objects.filter(pk=self.post.pk).exists()
        assert not CompetitionWhiteListEmail.objects.filter(pk=self.whitelist_email.pk).exists()
        assert User.objects.filter(pk__in=[self.other_user.pk, self.collaborator.pk]).count() == 2

    def test_delete_without_options_keeps_tasks_and_phase_datasets(self):
        """Without query params, tasks, their datasets, solutions and phase datasets are kept"""
        self._delete(user=self.creator)
        assert Task.objects.filter(pk=self.task.pk).exists()
        assert Solution.objects.filter(pk=self.solution.pk).exists()
        task_data_ids = [self.task.ingestion_program_id, self.task.scoring_program_id,
                         self.task.input_data_id, self.task.reference_data_id]
        assert Data.objects.filter(pk__in=task_data_ids).count() == 4
        assert Data.objects.filter(pk__in=[self.public_data.pk, self.starting_kit.pk]).count() == 2

    def test_delete_queues_files_of_deleted_records(self):
        """The logo, parent and child submission files and logs, bundle, dump and submission zips are queued for deletion"""
        competition_id, competition_title = self.comp.pk, self.comp.title
        _, delete_files = self._delete(user=self.creator)
        assert delete_files.delay.call_args.kwargs['competition_id'] == competition_id
        assert delete_files.delay.call_args.kwargs['competition_title'] == competition_title
        file_names = self._queued_file_names(delete_files)
        assert {
            self.comp.logo.name,
            self.comp.logo_icon.name,
            'prediction_result/prediction_result.zip',
            'scoring_result/scoring_result.zip',
            'detailed_result/detailed_results.html',
            'submission_details/prediction_stdout.txt',
            'prediction_result/child_prediction_result.zip',
            'scoring_result/child_scoring_result.zip',
            'detailed_result/child_detailed_results.html',
            'submission_details/child_prediction_stdout.txt',
            self.bundle.data_file.name,
            self.dump_data.data_file.name,
            self.submission.data.data_file.name,
            self.uploaded_zip.data_file.name,
        } == file_names

    def test_delete_tasks_deletes_tasks_solutions_and_task_datasets(self):
        """With delete_tasks=true, the task, its solution and its four datasets are deleted with their files"""
        task_data = [self.task.ingestion_program, self.task.scoring_program,
                     self.task.input_data, self.task.reference_data]
        solution_data = self.solution.data
        _, delete_files = self._delete(user=self.creator, delete_tasks='true')
        assert not Task.objects.filter(pk=self.task.pk).exists()
        assert not Solution.objects.filter(pk=self.solution.pk).exists()
        assert not Data.objects.filter(pk__in=[data.pk for data in task_data + [solution_data]]).exists()
        assert self._queued_file_names(delete_files, file_type='task datasets') == \
            {data.data_file.name for data in task_data}
        assert self._queued_file_names(delete_files, file_type='solution datasets') == {solution_data.data_file.name}

    def test_delete_tasks_keeps_task_used_by_other_competition(self):
        """With delete_tasks=true, a task also used by another competition is kept with its datasets"""
        self._other_phase(tasks=[self.task])
        self._delete(user=self.creator, delete_tasks='true')
        assert Task.objects.filter(pk=self.task.pk).exists()
        assert Solution.objects.filter(pk=self.solution.pk).exists()
        assert Data.objects.filter(pk=self.task.scoring_program_id).exists()

    def test_delete_tasks_keeps_dataset_used_by_other_task(self):
        """With delete_tasks=true, the task is deleted but a dataset also used by another task is kept"""
        TaskFactory(created_by=self.creator, scoring_program=self.task.scoring_program)
        _, delete_files = self._delete(user=self.creator, delete_tasks='true')
        assert not Task.objects.filter(pk=self.task.pk).exists()
        assert Data.objects.filter(pk=self.task.scoring_program_id).exists()
        assert not Data.objects.filter(pk=self.task.ingestion_program_id).exists()
        # Only the 3 datasets that no other task uses are queued
        assert self._queued_file_names(delete_files, file_type='task datasets') == {
            self.task.ingestion_program.data_file.name,
            self.task.input_data.data_file.name,
            self.task.reference_data.data_file.name,
        }

    def test_delete_phase_datasets_deletes_public_data_and_starting_kit(self):
        """With delete_phase_datasets=true, the public data and starting kit are deleted with their files"""
        _, delete_files = self._delete(user=self.creator, delete_phase_datasets='true')
        assert not Data.objects.filter(pk__in=[self.public_data.pk, self.starting_kit.pk]).exists()
        assert self._queued_file_names(delete_files, file_type='phase datasets') == \
            {self.public_data.data_file.name, self.starting_kit.data_file.name}

    def test_delete_phase_datasets_keeps_dataset_used_by_other_competition(self):
        """With delete_phase_datasets=true, a starting kit used by another competition's phase is kept"""
        self._other_phase(starting_kit=self.starting_kit)
        self._delete(user=self.creator, delete_phase_datasets='true')
        assert Data.objects.filter(pk=self.starting_kit.pk).exists()
        assert not Data.objects.filter(pk=self.public_data.pk).exists()


class CompetitionDeletePreviewTests(CompetitionDeleteTestBase):
    """Tests for the delete preview: who can see it and what it lists as deleted or kept"""

    def _preview(self, user=None):
        """Gets the delete preview of the competition as `user`"""
        if user:
            self.client.force_login(user)
        return self.client.get(reverse('competition-delete-preview', kwargs={'pk': self.comp.pk}))

    def test_only_creator_can_preview_delete(self):
        """Other users, collaborators, superusers and anonymous users get 403; the creator gets 200"""
        for user in [None, self.other_user, self.collaborator, self.superuser]:
            self.client.logout()
            assert self._preview(user=user).status_code == 403
        assert self._preview(user=self.creator).status_code == 200

    def test_preview_does_not_delete_anything(self):
        """Getting the preview leaves the competition, its submissions and tasks in place"""
        self._preview(user=self.creator)
        assert Competition.objects.filter(pk=self.comp.pk).exists()
        assert Submission.objects.filter(pk=self.submission.pk).exists()
        assert Task.objects.filter(pk=self.task.pk).exists()

    def test_preview_shows_what_will_be_deleted(self):
        """The preview lists the always-deleted items, and marks shared tasks and datasets as not deletable"""
        shared_task = TaskFactory(created_by=self.creator, scoring_program=self.task.scoring_program)
        self.phase.tasks.add(shared_task)
        self._other_phase(tasks=[shared_task], starting_kit=self.starting_kit)

        resp = self._preview(user=self.creator)
        assert resp.status_code == 200
        auto_delete = resp.data['auto_delete']
        # Files: 3 results and 1 log for the parent and for the child, plus the submission zip and the uploaded zip
        assert auto_delete['submissions'] == {
            'parent_count': 1, 'child_count': 1, 'file_count': 10, 'total_size': 100.0,
        }
        assert auto_delete['leaderboards'] == [{'title': self.leaderboard.title, 'columns': [self.column.title]}]
        assert auto_delete['phases'] == [self.phase.name, self.phase_2.name]
        assert auto_delete['pages'] == ['Overview']
        assert len(auto_delete['logo']) == 2
        assert [data['file_name'] for data in auto_delete['bundle']] == ['competition_bundle.zip']
        assert len(auto_delete['dumps']) == 1
        # The creator and the collaborator are added as participants automatically, plus the participant
        assert auto_delete['participants_count'] == 3
        assert auto_delete['participant_groups'] == [{'name': 'Delete test group', 'members_count': 1}]
        assert auto_delete['forum_threads_count'] == 1
        assert auto_delete['forum_posts_count'] == 1

        tasks = {task['name']: task for task in resp.data['tasks']}
        assert tasks[self.task.name]['can_delete'] is True
        assert tasks[shared_task.name]['can_delete'] is False
        task_datasets = {data['type']: data['can_delete'] for data in tasks[self.task.name]['datasets']}
        assert task_datasets == {
            'Ingestion Program': True, 'Scoring Program': False, 'Input Data': True, 'Reference Data': True,
        }
        assert tasks[self.task.name]['solutions'][0]['can_delete'] is True

        phase_datasets = {data['type']: data['can_delete'] for data in resp.data['phase_datasets']}
        assert phase_datasets == {'Public Data': True, 'Starting Kit': False}


class CompetitionDetailTests(APITestCase):
    """
    Tests for the competition detail API: who can access public and private competitions,
    which fields admins and non-admins see, and that the queue only includes its id and name.
    """
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.collaborator = UserFactory(username='collaborator', password='collaborator')
        self.participant = UserFactory(username='participant', password='participant')
        self.pending_participant = UserFactory(username='pending_participant', password='pending_participant')
        self.other_user = UserFactory(username='other_user', password='other_user')
        self.superuser = UserFactory(username='superuser', password='superuser', is_superuser=True, is_staff=True)
        self.queue_owner = UserFactory(username='queue_owner', password='queue_owner')
        # Mock RabbitMQ so saving the queue doesn't create a real vhost; return a fake vhost UUID instead
        with mock.patch('queues.models.rabbit.create_queue') as rabbit_create_queue:
            rabbit_create_queue.return_value = uuid.uuid4()
            self.queue = QueueFactory(owner=self.queue_owner, is_public=True)

        self.public_comp = CompetitionFactory(
            created_by=self.creator, collaborators=[self.collaborator], queue=self.queue, published=True
        )
        self.private_comp = CompetitionFactory(
            created_by=self.creator, collaborators=[self.collaborator], queue=self.queue, published=False
        )
        for comp in (self.public_comp, self.private_comp):
            CompetitionParticipantFactory(user=self.participant, competition=comp, status='approved')
            CompetitionParticipantFactory(user=self.pending_participant, competition=comp, status='pending')
        self.queue_owner_comp = CompetitionFactory(created_by=self.queue_owner, queue=self.queue, published=True)

        # One visible and one hidden leaderboard on the public competition
        self.visible_leaderboard = LeaderboardFactory(hidden=False)
        self.hidden_leaderboard = LeaderboardFactory(hidden=True)
        PhaseFactory(competition=self.public_comp, leaderboard=self.visible_leaderboard)
        PhaseFactory(competition=self.public_comp, leaderboard=self.hidden_leaderboard)

        # None means a logged-out user
        self.admins = [self.creator, self.collaborator, self.superuser]
        self.non_admins = [None, self.participant, self.pending_participant, self.other_user]

    def _get(self, competition, user=None, **params):
        """Request the detail API of `competition` as `user`, or logged out when `user` is None."""
        self.client.logout()
        if user:
            self.client.force_login(user)
        url = reverse('competition-detail', kwargs={"pk": competition.pk})
        return self.client.get(url, params)

    # ---------- Access ----------

    def test_anyone_can_access_public_competition(self):
        """
        Admins, participants, other users and logged-out users request a published competition.
        Expects a 200 response for all of them.
        """
        for user in self.admins + self.non_admins:
            assert self._get(self.public_comp, user).status_code == 200

    def test_organizers_approved_participants_and_superusers_can_access_private_competition(self):
        """
        The creator, a collaborator, an approved participant and a superuser request an unpublished competition.
        Expects a 200 response for all of them.
        """
        for user in [self.creator, self.collaborator, self.participant, self.superuser]:
            assert self._get(self.private_comp, user).status_code == 200

    def test_other_users_cannot_access_private_competition(self):
        """
        A logged-out user, an unrelated user and a pending participant request an unpublished competition
        without a secret key.
        Expects a 404 response for all of them.
        """
        for user in [None, self.other_user, self.pending_participant]:
            assert self._get(self.private_comp, user).status_code == 404

    def test_valid_secret_key_gives_access_to_private_competition(self):
        """
        A logged-out user, an unrelated user and a pending participant request an unpublished competition
        with its secret key.
        Expects a 200 response for all of them.
        """
        for user in [None, self.other_user, self.pending_participant]:
            resp = self._get(self.private_comp, user, secret_key=str(self.private_comp.secret_key))
            assert resp.status_code == 200

    def test_invalid_secret_key_does_not_give_access_to_private_competition(self):
        """
        A logged-out user and an unrelated user request an unpublished competition with a wrong secret key.
        Expects a 404 response for both.
        """
        for user in [None, self.other_user]:
            resp = self._get(self.private_comp, user, secret_key=str(uuid.uuid4()))
            assert resp.status_code == 404

    # ---------- Fields ----------

    def test_admins_see_all_fields(self):
        """
        The creator, a collaborator and a superuser request a published competition.
        Expects every field in the response.
        """
        for user in self.admins:
            resp = self._get(self.public_comp, user)
            assert resp.status_code == 200
            for field in CompetitionDetailSerializer.Meta.fields:
                assert field in resp.data, field

    def test_non_admins_do_not_see_admin_only_fields(self):
        """
        Participants, an unrelated user and a logged-out user request a published competition.
        Expects no admin-only field in the response.
        """
        for user in self.non_admins:
            resp = self._get(self.public_comp, user)
            assert resp.status_code == 200
            for field in CompetitionDetailSerializer.Meta.admin_fields:
                assert field not in resp.data, field

    def test_non_admins_see_fields_used_by_competition_page(self):
        """
        Participants, an unrelated user and a logged-out user request a published competition.
        Expects every field the competition page uses for non-admins in the response.
        """
        # Listed here instead of using Meta.public_fields, so moving one of them to admin_fields fails this test
        fields_used_by_competition_page = [
            'fact_sheet',
            'registration_auto_approve',
            'make_programs_available',
            'make_input_data_available',
            'enable_detailed_results',
            'show_detailed_results_in_submission_panel',
            'show_detailed_results_in_leaderboard',
            'forum',
            'forum_enabled',
        ]
        for user in self.non_admins:
            resp = self._get(self.public_comp, user)
            assert resp.status_code == 200
            for field in fields_used_by_competition_page:
                assert field in resp.data, field

    def test_non_admins_with_secret_key_do_not_see_admin_only_fields(self):
        """
        A logged-out user and an unrelated user open an unpublished competition with its secret key.
        Expects a 200 response without any admin-only field.
        """
        for user in [None, self.other_user]:
            resp = self._get(self.private_comp, user, secret_key=str(self.private_comp.secret_key))
            assert resp.status_code == 200
            for field in CompetitionDetailSerializer.Meta.admin_fields:
                assert field not in resp.data, field

    def test_admins_see_hidden_leaderboards(self):
        """
        The creator, a collaborator and a superuser request a competition with a visible and a hidden leaderboard.
        Expects both leaderboards in the response.
        """
        for user in self.admins:
            resp = self._get(self.public_comp, user)
            leaderboard_ids = {lb['id'] for lb in resp.data['leaderboards']}
            assert leaderboard_ids == {self.visible_leaderboard.id, self.hidden_leaderboard.id}

    def test_non_admins_do_not_see_hidden_leaderboards(self):
        """
        Participants, an unrelated user and a logged-out user request a competition
        with a visible and a hidden leaderboard.
        Expects only the visible leaderboard in the response.
        """
        for user in self.non_admins:
            resp = self._get(self.public_comp, user)
            leaderboard_ids = {lb['id'] for lb in resp.data['leaderboards']}
            assert leaderboard_ids == {self.visible_leaderboard.id}

    # ---------- Queue ----------

    def test_admins_see_only_queue_id_and_name(self):
        """
        The creator and a collaborator (neither owns the queue) and a superuser request a competition
        that uses someone else's queue.
        Expects the queue to have only id and name.
        """
        for user in self.admins:
            resp = self._get(self.public_comp, user)
            assert resp.status_code == 200
            assert resp.data['queue'] == {'id': self.queue.id, 'name': self.queue.name}

    def test_queue_owner_sees_only_queue_id_and_name_on_own_competition(self):
        """
        The queue owner requests the detail API of their own competition that uses their queue.
        Expects the queue to have only id and name.
        Queue owners can get the broker URL from the queues API instead.
        """
        resp = self._get(self.queue_owner_comp, self.queue_owner)
        assert resp.status_code == 200
        assert resp.data['queue'] == {'id': self.queue.id, 'name': self.queue.name}

    def test_non_admins_do_not_see_queue(self):
        """
        Participants, an unrelated user and a logged-out user request a competition that uses a queue.
        Expects no queue field in the response.
        """
        for user in self.non_admins:
            resp = self._get(self.public_comp, user)
            assert resp.status_code == 200
            assert 'queue' not in resp.data

    def test_admins_see_null_queue_when_competition_has_no_queue(self):
        """
        The creator requests a competition that doesn't use a custom queue.
        Expects the queue field to be None.
        """
        comp = CompetitionFactory(created_by=self.creator, queue=None, published=True)
        resp = self._get(comp, self.creator)
        assert resp.status_code == 200
        assert resp.data['queue'] is None


class CompetitionListTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(username='user', password='user')
        self.client.force_authenticate(user=self.user)

    def test_list_endpoint_is_paginated(self):
        # Create 3 competitions organized by the user
        for _ in range(3):
            CompetitionFactory(created_by=self.user)

        url = reverse('competition-list')
        response = self.client.get(url, {'mine': 'true', 'type': 'any', 'page_size': 2})

        assert response.status_code == 200
        assert set(response.data.keys()) == {'next', 'previous', 'count', 'page_size', 'results'}
        assert response.data['count'] == 3
        assert len(response.data['results']) == 2
        assert response.data['next'] is not None
        assert response.data['previous'] is None

    def test_participating_in_excludes_organized_competitions(self):
        # Competition the user organizes: they're auto-added as an approved participant
        # under the hood (see Competition.save()), but this should NOT show up as "participating"
        organized = CompetitionFactory(created_by=self.user)

        # Competition the user genuinely participates in
        other_creator = UserFactory(username='other_creator', password='other')
        participated = CompetitionFactory(created_by=other_creator, published=True)
        CompetitionParticipantFactory(user=self.user, competition=participated, status='approved')

        url = reverse('competition-list')
        response = self.client.get(url, {'participating_in': 'true'})

        assert response.status_code == 200
        returned_ids = [c['id'] for c in response.data['results']]
        assert participated.id in returned_ids
        assert organized.id not in returned_ids

    def test_mine_returns_organized_competitions(self):
        # Sanity check that the "organizing" filter is unaffected by the participating_in fix
        organized = CompetitionFactory(created_by=self.user)

        other_creator = UserFactory(username='other_creator', password='other')
        participated = CompetitionFactory(created_by=other_creator, published=True)
        CompetitionParticipantFactory(user=self.user, competition=participated, status='approved')

        url = reverse('competition-list')
        response = self.client.get(url, {'mine': 'true', 'type': 'any'})

        assert response.status_code == 200
        returned_ids = [c['id'] for c in response.data['results']]
        assert organized.id in returned_ids
        assert participated.id not in returned_ids


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
            SubmissionFactory(owner=self.creator, phase=self.phase_1, status=Submission.FINISHED, leaderboard=self.leaderboard)
        assert self.phase_1.submissions.count() == 5
        assert self.phase_2.submissions.count() == 0

        # call "migrate" from phase 1 -> 2
        with mock.patch("competitions.tasks.run_submission") as run_submission_mock:
            url = reverse('phases-manually_migrate', kwargs={"pk": self.phase_1.pk})
            resp = self.client.post(url)
            assert resp.status_code == 200
            assert run_submission_mock.call_count == 5

        self.phase_2.refresh_from_db()
        # check phase 2 has the 5 submissions
        assert self.phase_1.submissions.count() == 5
        assert self.phase_2.submissions.count() == 5

    def test_manual_migration_makes_submissions_out_of_only_parents_not_children(self):
        self.client.login(username='creator', password='creator')

        # make 1 submission with 4 children
        parent = SubmissionFactory(owner=self.creator, phase=self.phase_1, has_children=True, status=Submission.FINISHED, leaderboard=self.leaderboard)
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
        for i in range(2):
            self.phases.append(PhaseFactory(leaderboard=self.leaderboard, leaderboard_id=self.leaderboard.id,
                                            competition=self.comp, index=0))
        self.column_title_to_id = {}

        self.users = [self.creator]
        for standard_users in range(3):
            user = UserFactory()
            self.users.append(user)

        self.user_keys = set()
        self.columns = []
        self.tasks = []
        for i in range(2):
            column = ColumnFactory(leaderboard=self.leaderboard, index=i)
            self.columns.append(column)
            self.column_title_to_id.update({column.title: column.id})
            task = TaskFactory()
            self.tasks.append(task)
        for user in self.users:
            for phase in self.phases:
                parent_sub = SubmissionFactory(owner=user, phase=phase, leaderboard=self.leaderboard)
                self.user_keys.add(f'{user.username}-{parent_sub.id}')
                for task in self.tasks:
                    phase.tasks.add(task)
                    submission = SubmissionFactory(parent=parent_sub, task=task)
                    for col in self.columns:
                        submission.scores.add(SubmissionScoreFactory(column=col))

    def test_get_competition_leaderboard_as_json(self):
        # gets makes sure to get JSON response and that it has all leaderboards and users
        url = reverse('competition-results', kwargs={"pk": self.comp.id})[0:-1] + '.json'
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)

        response_titles = set()
        response_users = set()
        for key in content.keys():
            title, id = key.rsplit("(", 1)
            response_titles.add(title)
            for user in content[key].keys():
                response_users.add(user)
        assert self.user_keys == response_users

        response_title = str(list(response_titles)[0]).split(' ')[0]
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


class TestCompetitionFactSheets(APITestCase):
    def setUp(self):
        self.leaderboard = LeaderboardFactory()
        self.phase = PhaseFactory()
        self.phase.leaderboard = self.leaderboard
        self.phase.save()
        self.competition = CompetitionFactory()
        self.competition.phases.add(self.phase)
        self.competition.save()
        self.competition_data = CompetitionSerializer(self.competition).data
        self.competition_data['logo'] = None
        self.competition_fact_sheet = {
            "bool_question": {
                "key": "bool_question",
                "type": "checkbox",
                "title": "boolean",
                "selection": [True, False],
                "is_required": "false",
                "is_on_leaderboard": "false"
            },
            "text_question": {
                "key": "text_question",
                "type": "text",
                "title": "text",
                "selection": "",
                "is_required": "false",
                "is_on_leaderboard": "false"
            },
            "text_required": {
                "key": "text_required",
                "type": "text",
                "title": "text",
                "selection": "",
                "is_required": "true",
                "is_on_leaderboard": "false"
            },
            "selection": {
                "key": "selection",
                "type": "select",
                "title": "selection",
                "selection": ["", "v1", "v2", "v3"],
                "is_required": "false",
                "is_on_leaderboard": "true"
            }
        }

    def test_competition_fact_sheet_working(self):
        new_comp_data = self.competition_data
        new_comp_data['fact_sheet'] = self.competition_fact_sheet
        competition_serializer = CompetitionSerializer(instance=self.competition, data=new_comp_data)
        assert competition_serializer.is_valid(raise_exception=True)
        comp = competition_serializer.save()
        assert comp.fact_sheet == self.competition_fact_sheet

    def test_competition_fact_sheet_with_missing_values(self):
        new_comp_data = self.competition_data
        new_comp_data['fact_sheet'] = {
            "boolean": {
                "key": "boolean",
                "type": "checkbox",
                "title": "boolean",
                "selection": [True, False],
                "is_required": "false",
            }
        }
        competition_serializer = CompetitionSerializer(data=new_comp_data)
        assert not competition_serializer.is_valid()

    def test_competition_fact_sheet_with_mismatched_keys(self):
        new_comp_data = self.competition_data
        new_comp_data['fact_sheet'] = {
            "key_value1": {
                "key": "different_key_value",
                "type": "checkbox",
                "title": "boolean",
                "selection": [True, False],
                "is_required": "false",
                "is_on_leaderboard": "false"
            }
        }
        competition_serializer = CompetitionSerializer(data=new_comp_data)
        assert not competition_serializer.is_valid()

    def test_competition_fact_sheet_bad_question_type(self):
        new_comp_data = self.competition_data
        new_comp_data['fact_sheet'] = {
            "text_required": {
                "key": "text_required",
                "type": "invalid_question",
                "title": "text",
                "selection": "",
                "is_required": "true",
                "is_on_leaderboard": "false"
            },
        }
        competition_serializer = CompetitionSerializer(data=new_comp_data)
        assert not competition_serializer.is_valid()
