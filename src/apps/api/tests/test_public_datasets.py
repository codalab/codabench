from rest_framework.test import APIClient
from django.test import TestCase
from factories import UserFactory, DataFactory
from datasets.models import Data


class PublicDatasetsTests(TestCase):
    def setUp(self):
        # Set up test client and authenticate as a test user
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

        # Create public datasets with varying metadata to test filters and sorting
        self.dataset1 = DataFactory(
            name="Climate Data",
            description="Temperature and rainfall records",
            is_public=True,
            type=Data.PUBLIC_DATA,
            license="MIT",
            is_verified=True,
            downloads=10
        )

        self.dataset2 = DataFactory(
            name="Vision Dataset",
            description="Images for computer vision",
            is_public=True,
            type=Data.PUBLIC_DATA,
            license=None,
            is_verified=False,
            downloads=25
        )

        self.dataset3 = DataFactory(
            name="Unverified Text",
            description="NLP dataset",
            is_public=True,
            type=Data.PUBLIC_DATA,
            license="Apache 2.0",
            is_verified=False,
            downloads=5
        )

        self.dataset4 = DataFactory(
            name="Recent Genomics",
            description="DNA sequences",
            is_public=True,
            type=Data.PUBLIC_DATA,
            downloads=40,
            is_verified=True
        )

    def test_default_ordering_recently_added(self):
        # Test default ordering by ID in descending order (most recently created datasets first)
        response = self.client.get("/api/datasets/public/")
        self.assertEqual(response.status_code, 200)
        ids = [d["id"] for d in response.data["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))  # Default ordering by -id

    def test_ordering_by_most_downloaded(self):
        # Test ordering datasets by download count in descending order
        response = self.client.get("/api/datasets/public/?ordering=most_downloaded")
        self.assertEqual(response.status_code, 200)
        downloads = [d["downloads"] for d in response.data["results"]]
        self.assertEqual(downloads, sorted(downloads, reverse=True))

    def test_filter_by_search_term(self):
        # Test full-text search in dataset name and description
        response = self.client.get("/api/datasets/public/?search=vision")
        self.assertEqual(response.status_code, 200)
        names = [d["name"].lower() + d["description"].lower() for d in response.data["results"]]
        self.assertTrue(all("vision" in text for text in names))

    def test_filter_by_has_license_true(self):
        # Test filtering datasets that have a license field set
        response = self.client.get("/api/datasets/public/?has_license=true")
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertTrue(all(d["license"] is not None for d in results))

    def test_filter_by_is_verified_true(self):
        # Test filtering datasets that are verified (is_verified=True)
        response = self.client.get("/api/datasets/public/?is_verified=true")
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertTrue(all(d["is_verified"] is True for d in results))

    def test_combined_filter_verified_with_license(self):
        # Test filtering datasets that are both verified and have a license
        response = self.client.get("/api/datasets/public/?is_verified=true&has_license=true")
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        for d in results:
            self.assertTrue(d["is_verified"])
            self.assertIsNotNone(d["license"])

    def test_combined_search_and_filter(self):
        # Test applying both search and is_verified filters together
        response = self.client.get("/api/datasets/public/?search=genomics&is_verified=true")
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]

        # Expect exactly one match with the correct name
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Recent Genomics")
