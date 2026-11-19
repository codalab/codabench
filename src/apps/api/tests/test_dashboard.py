from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from factories import CompetitionFactory, UserFactory, TagFactory


class DashboardCompetitionsApiTests(APITestCase):
    def setUp(self):
        self.url = reverse('dashboard_api')

        self.regular_user = UserFactory(username='regular_user')
        self.admin = UserFactory(username='admin', is_staff=True, is_superuser=True)

        self.tag = TagFactory(name='NLP')

        self.public_comp = CompetitionFactory(
            title='Public Benchmark',
            published=True,
            created_by=self.admin
        )
        self.public_comp.tags.add(self.tag)

        self.private_comp = CompetitionFactory(
            title='Private Competition',
            published=False,
            created_by=self.regular_user
        )

    def test_default_returns_only_public_competitions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.public_comp.id)
        self.assertTrue(data[0]['published'])

    def test_response_contains_only_required_lightweight_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.json()[0]

        # Verify required lightweight fields exist
        expected_fields = {
            'id', 'title', 'created_by', 'created_when',
            'published', 'participants_count', 'submissions_count',
            'competition_type', 'reward', 'tags'
        }
        self.assertEqual(set(item.keys()), expected_fields)

        # Verify heavy fields are NOT present
        self.assertNotIn('description', item)
        self.assertNotIn('logo', item)
        self.assertNotIn('contact_email', item)

        # Verify tags structure
        self.assertEqual(len(item['tags']), 1)
        self.assertEqual(item['tags'][0]['name'], 'NLP')

    def test_non_admin_cannot_access_private_competitions(self):
        # Anonymous user
        response = self.client.get(f"{self.url}?visibility=private")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Regular authenticated user
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.url}?visibility=private")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(f"{self.url}?visibility=all")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_private_competitions(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?visibility=private")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.private_comp.id)
        self.assertFalse(data[0]['published'])

    def test_admin_can_access_all_competitions(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?visibility=all")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)

    def test_invalid_visibility_raises_validation_error(self):
        response = self.client.get(f"{self.url}?visibility=invalid_visibility")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
