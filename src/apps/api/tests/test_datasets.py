from django.urls import reverse
from faker import Factory
from rest_framework.test import APITestCase

from datasets.models import Data
from factories import UserFactory, DataFactory


faker = Factory.create()


class DatasetAPITests(APITestCase):
    def setUp(self):
        self.creator = UserFactory(username='creator', password='creator')

        self.existing_dataset = DataFactory(created_by=self.creator, name="Test!")

    def test_dataset_api_checks_duplicate_names_for_same_user(self):
        self.client.login(username='creator', password='creator')

        # Make a dataset that conflicts with existing dataset name
        resp = self.client.post(reverse("data-list"), {
            'name': 'Test!',
            'type': Data.COMPETITION_BUNDLE,
            'request_sassy_file_name': faker.file_name(),
        })

        assert resp.status_code == 400
        assert resp.data["non_field_errors"][0] == 'You already have a dataset by this name, please delete that dataset or rename this one'

        # Update existing dataset, shouldn't conflict with itself
        resp = self.client.put(reverse("data-detail", args=(self.existing_dataset.pk,)), {
            'name': 'Test!',
            'type': Data.COMPETITION_BUNDLE,
            'request_sassy_file_name': faker.file_name(),
        })
        assert resp.status_code == 200

    # todo: test non logged in user can't create data
