# tests/test_banned_user.py

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
        """Banned user should see banned.html page"""
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
