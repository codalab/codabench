import os
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from factories import UserFactory, DataFactory

# Removed this test because of the changes of this PR : https://github.com/codalab/codabench/pull/1963
# class TestTasks(APITestCase):
#    def test_task_shown_as_validated_properly(self):
#        user = UserFactory(username='test')
#        solution = SolutionFactory(md5="12345")
#        task = TaskFactory(created_by=user, solutions=[solution])
#        competition = CompetitionFactory(created_by=user)
#        phase = PhaseFactory(competition=competition, tasks=[task])
#        submission = SubmissionFactory(md5="12345", phase=phase, status=Submission.FINISHED)
#        url = reverse('task-detail', kwargs={'pk': task.id})
#        self.client.login(username=user.username, password='test')

#        # task should be validated because we have a successful submission matching
#        # our solution
#        resp = self.client.get(url)
#        assert resp.status_code == 200
#        assert resp.data["validated"]

#        # make submission anything but Submission.FINISHED, task -> invalidated
#        submission.status = Submission.FAILED
#        submission.save()
#        resp = self.client.get(url)
#        assert resp.status_code == 200
#        assert not resp.data["validated"]

#        # make submission Submission.Finished, task -> re-validated
#        submission.status = Submission.FINISHED
#        submission.save()
#        resp = self.client.get(url)
#        assert resp.status_code == 200
#        assert resp.data["validated"]

#        # delete submission, task -> re-invalidated
#        submission.delete()
#        resp = self.client.get(url)
#        assert resp.status_code == 200
#        assert not resp.data["validated"]

#        # make submission with different Sha -> still invalid
#        SubmissionFactory(md5="different", phase=phase, status=Submission.FINISHED)
#        resp = self.client.get(url)
#        assert resp.status_code == 200
#        assert not resp.data["validated"]


class TestUploadTask(APITestCase):
    def setUp(self):
        self.user = UserFactory(username='user', password='password')
        self.user_low_quota = UserFactory(username='user_low_quota', password='password_low_quota', quota=0)
        self.user2 = UserFactory(username='user2', password='password2')

        uuid1 = "96187a93-94ea-40a1-b394-af2e7e3edb2e"
        uuid2 = "a0f80316-8c46-4c04-a5d4-6184904bdb69"
        uuid3 = "6c3e6dde-d0fa-4c22-af66-030187dbfd4f"
        uuid4 = "c4179c3f-498c-486a-8ac5-1e194036a3ed"
        uuid5 = "f861a11c-36cb-4907-9f82-4aa609b4e822"

        self.ingestion_program = DataFactory(created_by=self.user, type='ingestion_program', key=uuid1)
        self.scoring_program = DataFactory(created_by=self.user, type='scoring_program', key=uuid2)
        self.input_data = DataFactory(created_by=self.user, type='input_data', key=uuid3)
        self.reference_data = DataFactory(created_by=self.user, type='reference_data', key=uuid4)

        self.ingestion_program_from_user2 = DataFactory(created_by=self.user2, type='ingestion_program', key=uuid5)

    def test_file_not_uploaded(self):
        self.client.login(username=self.user.username, password='password')

        response = self.client.post(reverse('tasks:upload_task'), {}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No attached file found, please try again!" == response.data['error']

    def test_quota_not_enough(self):
        self.client.login(username=self.user_low_quota.username, password='password_low_quota')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'valid_task_with_files.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_507_INSUFFICIENT_STORAGE
        assert "Insufficient space! Please free up some space and try again. You can manage your files in the Resources page." == response.data['error']

    def test_yaml_not_found_in_zip(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'no_yaml.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "task.yaml not found in the zip file" == response.data['error']

    def test_yaml_cannot_be_parsed(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'invalid_yaml.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Error parsing task.yaml:" in response.data['error']

    def test_yaml_missing_name(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'missing_name.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing: name, task must have a name" == response.data['error']

    def test_yaml_missing_description(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'missing_description.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing: description, task must have a description" == response.data['error']

    def test_yaml_missing_scoring_program(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'missing_scoring_program.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing: scoring_program, task must have a scoring_program" == response.data['error']

    def test_dataset_not_belongs_to_user(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'invalid_ingestion_key.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ingestion_program with key 'f861a11c-36cb-4907-9f82-4aa609b4e822' not found." == response.data['error']

    def test_missing_key_and_zip_for_scoring_program(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'scoring_program_missing_key_and_zip.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "scoring_program must have either a key or zip" == response.data['error']

    def test_dataset_file_missing_in_zip(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'missing_ingestion_zip.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Dataset file 'iris-ingestion-program.zip' not found in the uploaded zip file." == response.data['error']

    def test_dataset_file_not_zip(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'invalid_ingestion_zip.zip')
        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Dataset file 'iris-ingestion-program.txt' should be a zip file." == response.data['error']

    def test_task_created_successfully_with_keys(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'valid_task_with_keys.zip')

        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert "Task 'Iris Task' created successfully!" == response.data['message']

    def test_task_created_successfully_with_zips(self):
        self.client.login(username=self.user.username, password='password')

        file_path = os.path.join(os.path.dirname(__file__), 'upload_task_test_files', 'valid_task_with_files.zip')

        with open(file_path, 'rb') as zip_file:
            response = self.client.post(reverse('tasks:upload_task'), {'file': zip_file}, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert "Task 'Iris Task' created successfully!" == response.data['message']
