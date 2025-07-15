from rest_framework.test import APIClient
from django.test import TestCase
from factories import (
    UserFactory,
    CompetitionFactory,
    CompetitionParticipantFactory,
)


class PublicCompetitionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.user = UserFactory(username="user1")
        self.organizer = UserFactory(username="organizer")
        self.other_user = UserFactory(username="other")

        # Login the test client
        self.client.force_authenticate(user=self.user)

        # Competitions
        self.competition1 = CompetitionFactory(
            title="AI Challenge",
            published=True,
            created_by=self.organizer,
            reward="First prize: $5000"
        )
        self.competition2 = CompetitionFactory(
            title="Vision Contest",
            published=True
        )
        self.competition3 = CompetitionFactory(
            title="ML Challenge",
            published=True,
            created_by=self.other_user,
            reward="Trophy + certificate"
        )

        # Add collaborators
        self.competition1.collaborators.add(self.user)

        # Participating user
        CompetitionParticipantFactory(user=self.user, competition=self.competition2, status="approved")

        # Add submission counts and participants counts manually
        self.competition1.submissions_count = 10
        self.competition1.participants_count = 20
        self.competition1.save()

        self.competition2.submissions_count = 5
        self.competition2.participants_count = 15
        self.competition2.save()

        self.competition3.submissions_count = 0
        self.competition3.participants_count = 5
        self.competition3.save()

    def test_default_ordering(self):
        # Send GET request to the public competitions API without any ordering parameter
        # This should trigger the default ordering, which is by 'id' in descending order (most recent first)
        response = self.client.get("/api/competitions/public/")

        # Ensure the response status is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Extract competition IDs from the response data
        ids = [comp["id"] for comp in response.data["results"]]

        # Assert that the competition IDs are sorted in descending order
        # This confirms that the default ordering (-id) is correctly applied
        self.assertTrue(ids == sorted(ids, reverse=True))  # ordered by -id

    def test_ordering_by_participants_count(self):
        # Send GET request to the public competitions API with ordering set to 'popular'
        # This should return competitions ordered by participants_count in descending order
        response = self.client.get("/api/competitions/public/?ordering=popular")

        # Check that the response status is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Extract the list of competition results from the response
        results = response.data["results"]

        # Create a list of participants_count from the results
        participants_counts = [c["participants_count"] for c in results]

        # Verify that the participants_count list is sorted in descending order
        # This ensures the 'popular' ordering filter is applied correctly
        self.assertEqual(participants_counts, sorted(participants_counts, reverse=True))

    def test_ordering_by_submissions_count(self):
        # Send GET request to the public competitions API with ordering by 'with_most_submissions'
        # This should return competitions ordered by submissions_count in descending order
        response = self.client.get("/api/competitions/public/?ordering=with_most_submissions")

        # Ensure the response was successful
        self.assertEqual(response.status_code, 200)

        # Extract the results list from the response
        results = response.data["results"]

        # Get the list of submissions_count values from the returned competitions
        submissions_counts = [c["submissions_count"] for c in results]

        # Assert that the list is sorted in descending order
        # This ensures that the ordering filter by submissions count is working correctly
        self.assertEqual(submissions_counts, sorted(submissions_counts, reverse=True))

    def test_filter_by_title_search(self):
        # Send GET request to the public competitions API with the search query "vision"
        # This should return only competitions with "vision" in their title (case-insensitive)
        response = self.client.get("/api/competitions/public/?search=vision")

        # Ensure the response was successful
        self.assertEqual(response.status_code, 200)

        # Extract and lowercase all returned competition titles
        titles = [comp["title"].lower() for comp in response.data["results"]]

        # Assert that every returned title contains the word "vision"
        # This verifies that the search filter is working correctly
        self.assertTrue(all("vision" in title for title in titles))

    def test_filter_by_participating_in(self):
        # Send GET request to the public competitions API with the filter: participating_in=true
        # This should return competitions where the user is an approved participant
        response = self.client.get("/api/competitions/public/?participating_in=true")

        # Ensure the response was successful
        self.assertEqual(response.status_code, 200)

        # Extract the list of competition IDs from the response
        returned_ids = [comp["id"] for comp in response.data["results"]]

        # Check that the competition the user is participating in (self.competition2) is included
        self.assertIn(self.competition2.id, returned_ids)

        # Check that the competition the user is NOT participating in (self.competition1) is excluded
        self.assertNotIn(self.competition3.id, returned_ids)  # Not participating in this

    def test_filter_by_organizing(self):
        # Send GET request to the public competitions API with the filter: organizing=true
        # This should return competitions where the request user is the creator or a collaborator
        response = self.client.get("/api/competitions/public/?organizing=true")

        # Ensure the response is successful
        self.assertEqual(response.status_code, 200)

        # Extract all returned competition IDs from the response
        returned_ids = [comp["id"] for comp in response.data["results"]]

        # Verify that the competition created by the user (self.competition1) is present in the results
        self.assertIn(self.competition1.id, returned_ids)

        # Verify that a competition the user is not organizing (self.competition2) is not included
        self.assertNotIn(self.competition2.id, returned_ids)  # Not organizing

    def test_combined_filters(self):
        # Send GET request to the public competitions API
        # with both filters: participating_in=true and search="vision"
        response = self.client.get("/api/competitions/public/?participating_in=true&search=vision")

        # Ensure the response is successful
        self.assertEqual(response.status_code, 200)

        # Extract the results from the paginated response
        results = response.data["results"]

        # Expect only one competition to match both filters
        self.assertEqual(len(results), 1)

        # Confirm that the returned competition is the one the user is participating in,
        # and whose title includes the word "vision"
        self.assertEqual(results[0]["id"], self.competition2.id)

    def test_auth_required_for_participating_in_filter(self):
        # Log out the currently authenticated user to simulate an anonymous request
        self.client.force_authenticate(user=None)

        # Send GET request to the public competitions API with participating_in=true
        # Expect this to fail because the user is not authenticated
        response = self.client.get("/api/competitions/public/?participating_in=true")

        # Ensure the response has status code 401 (Unauthorized)
        self.assertEqual(response.status_code, 401)

        # Confirm that the error message is included in the response
        self.assertIn("detail", response.data)

        # Confirm the error message explicitly states the reason
        self.assertEqual(
            response.data["detail"],
            "Authentication required for filtering by participating in or organizing."
        )

    def test_auth_required_for_organizing_filter(self):
        # Log out the currently authenticated user to simulate an anonymous request
        self.client.force_authenticate(user=None)

        # Send GET request to the public competitions API with organizing=true
        # Expect this to fail because the user is not authenticated
        response = self.client.get("/api/competitions/public/?organizing=true")

        # Ensure the response has status code 401 (Unauthorized)
        self.assertEqual(response.status_code, 401)

        # Confirm that the error message is included in the response
        self.assertIn("detail", response.data)

        # Confirm the error message explicitly states the reason
        self.assertEqual(
            response.data["detail"],
            "Authentication required for filtering by participating in or organizing."
        )

    def test_filter_by_has_reward(self):
        # Send a GET request to filter competitions that have a reward
        response = self.client.get("/api/competitions/public/?has_reward=true")

        # Ensure the response is successful with 200 OK status
        self.assertEqual(response.status_code, 200)

        # Extract the competition IDs returned in the response
        returned_ids = [comp["id"] for comp in response.data["results"]]

        # Check that competitions with rewards are returned
        self.assertIn(self.competition1.id, returned_ids)
        self.assertIn(self.competition3.id, returned_ids)

        # Check that competition without a reward is not included
        self.assertNotIn(self.competition2.id, returned_ids)
