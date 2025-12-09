from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class BlockBannedUsersMiddlewareTests(TestCase):

    def setUp(self):
        self.client = Client()

        # Normal user (not banned)
        self.user = User.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password="password123",
            is_banned=False
        )

        # Banned user
        self.banned_user = User.objects.create_user(
            username="banneduser",
            email="banned@example.com",
            password="password123",
            is_banned=True
        )

    def test_banned_user_sees_banned_page(self):
        """Banned user visiting a normal page should see banned.html"""
        self.client.login(username="banneduser", password="password123")
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "banned.html")
        self.assertContains(response, "You are banned", status_code=403)

    def test_normal_user_can_access_page(self):
        """Normal user should access pages normally"""
        self.client.login(username="normaluser", password="password123")
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "You are banned")

    def test_banned_user_api_request_returns_json(self):
        """Banned user hitting API should get JSON error, not HTML page"""
        self.client.login(username="banneduser", password="password123")
        response = self.client.get(reverse("user_quota"))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertJSONEqual(
            response.content,
            {"error": "You are banned from using Codabench"}
        )

    def test_normal_user_api_access(self):
        """Normal user should get valid API response"""
        self.client.login(username="normaluser", password="password123")
        response = self.client.get(reverse("user_quota"))

        self.assertNotEqual(response.status_code, 403)
        self.assertEqual(response.status_code, 200)
