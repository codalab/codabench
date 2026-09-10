from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from factories import CompetitionFactory, UserFactory

# SimpleRateThrottle subclasses (AnonRateThrottle/UserRateThrottle/ScopedRateThrottle and
# their AnonBurstRateThrottle/UserBurstRateThrottle counterparts in api/throttling.py) read
# REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] once at import time into this shared class
# attribute, so @override_settings(REST_FRAMEWORK=...) does not reach it. Tests patch it
# directly to get small, fast limits instead of waiting out the real ones.
#
# Every scope referenced by an active throttle class must be present in the patched dict
# (missing keys raise ImproperlyConfigured), so tests start from generous defaults for all
# scopes and only tighten the one(s) under test.
PUBLIC_URL = "/api/competitions/public/"
LIST_URL = "/api/competitions/"

GENEROUS_RATES = {
    "anon": "1000/day",
    "user": "1000/day",
    "anon_burst": "1000/min",
    "user_burst": "1000/min",
    "competitions_public": "1000/day",
}


@override_settings(CACHES={
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "throttle-test-cache",
    },
})
class ThrottlingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        CompetitionFactory(published=True)

    def tearDown(self):
        cache.clear()

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "competitions_public": "2/min"})
    def test_public_action_throttles_after_scope_limit(self):
        for _ in range(2):
            response = self.client.get(PUBLIC_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(PUBLIC_URL)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Retry-After", response)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "competitions_public": "1/min"})
    def test_public_action_throttle_is_independent_of_global_anon_throttle(self):
        # Exhaust the competitions_public scope only.
        self.assertEqual(self.client.get(PUBLIC_URL).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(PUBLIC_URL).status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # The global 'anon' bucket (used by list/retrieve) is untouched.
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "anon": "2/min"})
    def test_list_action_uses_global_anon_throttle(self):
        for _ in range(2):
            response = self.client.get(LIST_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "user": "2/min"})
    def test_list_action_uses_global_user_throttle_for_authenticated_requests(self):
        self.client.force_authenticate(user=UserFactory(username="throttled-user"))

        for _ in range(2):
            response = self.client.get(LIST_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "competitions_public": "1/min"})
    def test_public_action_counts_anonymous_and_authenticated_requests_separately(self):
        # Anonymous identity (keyed by IP) exhausts its own bucket.
        self.assertEqual(self.client.get(PUBLIC_URL).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(PUBLIC_URL).status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # A different, authenticated identity (keyed by user id) has its own separate bucket.
        self.client.force_authenticate(user=UserFactory(username="another-user"))
        self.assertEqual(self.client.get(PUBLIC_URL).status_code, status.HTTP_200_OK)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "anon_burst": "2/min"})
    def test_list_action_uses_global_anon_burst_throttle(self):
        for _ in range(2):
            response = self.client.get(LIST_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "user_burst": "2/min"})
    def test_list_action_uses_global_user_burst_throttle_for_authenticated_requests(self):
        self.client.force_authenticate(user=UserFactory(username="burst-user"))

        for _ in range(2):
            response = self.client.get(LIST_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "anon_burst": "2/min"})
    def test_public_action_throttled_by_anon_burst_even_with_generous_daily_scope(self):
        # competitions_public (daily) has plenty of room; the burst throttle stacked
        # onto the `public` action (api/views/competitions.py) should still trip.
        for _ in range(2):
            response = self.client.get(PUBLIC_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(PUBLIC_URL)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch.object(SimpleRateThrottle, "THROTTLE_RATES", {**GENEROUS_RATES, "user_burst": "2/min"})
    def test_public_action_throttled_by_user_burst_even_with_generous_daily_scope(self):
        self.client.force_authenticate(user=UserFactory(username="public-burst-user"))

        for _ in range(2):
            response = self.client.get(PUBLIC_URL)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(PUBLIC_URL)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
