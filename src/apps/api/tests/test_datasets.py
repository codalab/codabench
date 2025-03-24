from django.urls import reverse
from faker import Factory
from rest_framework.test import APITestCase
from datasets.models import Data
from factories import UserFactory, DataFactory
from utils.data import pretty_bytes, gb_to_bytes


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
