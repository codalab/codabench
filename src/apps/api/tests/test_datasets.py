from django.urls import reverse
from faker import Factory
from django.test import TestCase
from rest_framework.test import APITestCase
from datasets.models import Data
from factories import UserFactory, DataFactory
from utils.data import pretty_bytes, gb_to_bytes
from unittest.mock import patch


faker = Factory.create()


class DatasetAPITests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')
        self.existing_dataset = DataFactory(created_by=self.creator, name="Test!", file_size=1000)

    def test_dataset_api_checks_duplicate_names_for_same_user(self):
        self.client.login(username='creator', password='creator')

        # Make a dataset that conflicts with existing dataset name
        resp = self.client.post(reverse("data-list"), {
            'name': 'Test!',
            'type': Data.COMPETITION_BUNDLE,
            'request_sassy_file_name': faker.file_name(),
            'file_name': faker.file_name(),
            'file_size': 1000,
        })

        assert resp.status_code == 400
        assert resp.data["non_field_errors"][0] == 'You already have a dataset by this name, please delete that dataset or rename this one'

        # Update existing dataset, shouldn't conflict with itself
        resp = self.client.put(reverse("data-detail", args=(self.existing_dataset.pk,)), {
            'name': 'Test!',
            'type': Data.COMPETITION_BUNDLE,
            'request_sassy_file_name': faker.file_name(),
            'file_size': 1000,
        })
        assert resp.status_code == 200

    def test_dataset_api_checks_for_authentication(self):
        self.client.logout()
        resp = self.client.post(reverse("data-list"), {
            'name': 'Test!',
            'type': Data.COMPETITION_BUNDLE,
            'request_sassy_file_name': faker.file_name(extension='.zip'),
        })
        assert resp.status_code == 403

    def test_dataset_api_check_quota(self):
        self.client.login(username='creator', password='creator')

        # User quota is in GB
        quota = float(self.creator.quota)
        # Convert to bytes to compute available space
        quota = gb_to_bytes(quota)
        # Used storage is in bytes
        storage_used = float(self.creator.get_used_storage_space())

        available_space = quota - storage_used

        # 1 GB = 1,000,000,000 Bytes
        # 1 TB = 1,000 GB = 1,000,000,000,000 Bytes
        # Using a big file size of 1 TB to run the test
        file_size = 1000 * 1000 * 1000 * 1000

        # Fake upload a very big dataset
        resp = self.client.post(reverse("data-list"), {
            'name': 'new-file-test',
            'type': Data.COMPETITION_BUNDLE,
            'request_sassy_file_name': faker.file_name(),
            'file_name': faker.file_name(),
            'file_size': file_size,
        })

        assert resp.status_code == 400
        assert resp.data["data_file"][0] == f'Insufficient space. Your available space is {pretty_bytes(available_space)}. The file size is {pretty_bytes(file_size)}. Please free up some space and try again. You can manage your files in the Resources page.'

        # Fake upload a small file
        file_size = available_space - 1000
        resp = self.client.post(reverse("data-list"), {
            'name': 'new-file-test',
            'type': Data.COMPETITION_BUNDLE,
            'request_sassy_file_name': faker.file_name(),
            'file_name': faker.file_name(),
            'file_size': file_size,
        })
        assert resp.status_code == 201


class DatasetDetailTests(TestCase):
    def setUp(self):
        self.owner = UserFactory(username="owner")
        self.other_user = UserFactory(username="other")
        self.client.force_login(self.owner)

        # Create datasets
        self.public_dataset = DataFactory(
            name="Public Dataset",
            is_public=True,
            created_by=self.owner,
            type=Data.PUBLIC_DATA
        )

        self.private_dataset = DataFactory(
            name="Private Dataset",
            is_public=False,
            created_by=self.owner,
            type=Data.INPUT_DATA
        )

        self.other_private_dataset = DataFactory(
            name="Other User's Private Dataset",
            is_public=False,
            created_by=self.other_user,
            type=Data.REFERENCE_DATA
        )

    def test_view_public_dataset(self):
        # Public dataset should be accessible by anyone
        self.client.logout()
        response = self.client.get(reverse("datasets:detail", args=[self.public_dataset.pk]))
        self.assertEqual(response.status_code, 200)

    def test_view_private_dataset_as_owner(self):
        # Owner should be able to access their own private dataset
        response = self.client.get(reverse("datasets:detail", args=[self.private_dataset.pk]))
        self.assertEqual(response.status_code, 200)

    def test_view_private_dataset_as_other_user(self):
        # Another user should not be able to access a private dataset
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("datasets:detail", args=[self.private_dataset.pk]))
        self.assertEqual(response.status_code, 404)

    def test_view_nonexistent_dataset(self):
        # Accessing a non-existent dataset should return 404
        response = self.client.get(reverse("datasets:detail", args=[99999]))
        self.assertEqual(response.status_code, 404)


class DatasetDownloadTests(TestCase):
    def setUp(self):
        self.owner = UserFactory(username="owner")
        self.other_user = UserFactory(username="other")
        self.client.force_login(self.owner)

        self.public_dataset = DataFactory(
            is_public=True,
            created_by=self.owner,
            downloads=5
        )

        self.private_dataset = DataFactory(
            is_public=False,
            created_by=self.owner,
            downloads=2
        )

    @patch("datasets.views.make_url_sassy")  # Replaces the real `make_url_sassy` function in this test only
    def test_download_public_dataset(self, mock_make_url_sassy):
        # Mock the URL that would normally be generated for the file
        # This avoids depending on actual file storage or signature logic
        mock_make_url_sassy.return_value = "http://codebench-storage/public_dataset.zip"

        response = self.client.get(reverse("datasets:download_by_pk", args=[self.public_dataset.pk]))

        # Should redirect to the URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://codebench-storage/public_dataset.zip")

        # Should increment download count
        self.public_dataset.refresh_from_db()
        self.assertEqual(self.public_dataset.downloads, 6)

    @patch("datasets.views.make_url_sassy")  # Replaces the real `make_url_sassy` function in this test only
    def test_download_private_dataset_as_owner(self, mock_make_url_sassy):
        # Mock the URL that would normally be generated for the file
        # This avoids depending on actual file storage or signature logic
        mock_make_url_sassy.return_value = "http://codebench-storage/private_dataset.zip"

        response = self.client.get(reverse("datasets:download_by_pk", args=[self.private_dataset.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://codebench-storage/private_dataset.zip")

        self.private_dataset.refresh_from_db()
        self.assertEqual(self.private_dataset.downloads, 3)

    def test_download_private_dataset_as_other_user(self):
        # Authenticate as a different user who is not the owner
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("datasets:download_by_pk", args=[self.private_dataset.pk]))

        # Should return 404 (access denied)
        self.assertEqual(response.status_code, 404)

    def test_download_nonexistent_dataset(self):
        response = self.client.get(reverse("datasets:download_by_pk", args=[99999]))

        # Should return 404 (access denied)
        self.assertEqual(response.status_code, 404)
