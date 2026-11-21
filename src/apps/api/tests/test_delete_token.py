from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from factories import UserFactory


class DeleteTokenTests(APITestCase):
    """Tests for the delete_token endpoint that lets a user delete their own API token."""

    def setUp(self):
        self.user = UserFactory(username='token_owner')
        self.user.set_password('token_owner_password')
        self.user.save()
        self.other_user = UserFactory(username='other_user')
        self.token = Token.objects.create(user=self.user)
        self.other_token = Token.objects.create(user=self.other_user)
        self.url = reverse('delete_token')

    def test_logged_in_user_deletes_own_token_only(self):
        """Logs in with a session and deletes the token. Expects the user's token gone and the other user's token untouched."""
        self.client.force_login(self.user)
        resp = self.client.delete(self.url)

        assert resp.status_code == 200
        assert resp.json()['success'] is True
        assert not Token.objects.filter(user=self.user).exists()
        assert Token.objects.filter(key=self.other_token.key, user=self.other_user).exists()

    def test_token_authenticated_request_deletes_that_token(self):
        """Authenticates with the token itself and deletes it. Expects the token gone and the same key rejected afterwards."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        resp = self.client.delete(self.url)

        assert resp.status_code == 200
        assert not Token.objects.filter(key=self.token.key).exists()

        resp = self.client.delete(self.url)
        assert resp.status_code in (401, 403)

    def test_anonymous_request_is_rejected(self):
        """Sends the request without logging in. Expects it rejected and no token deleted."""
        resp = self.client.delete(self.url)

        assert resp.status_code in (401, 403)
        assert Token.objects.count() == 2

    def test_delete_when_no_token_exists_succeeds(self):
        """Logs in as a user without a token. Expects success and the other user's token untouched."""
        self.token.delete()
        self.client.force_login(self.user)
        resp = self.client.delete(self.url)

        assert resp.status_code == 200
        assert resp.json()['success'] is True
        assert Token.objects.filter(key=self.other_token.key).exists()

    def test_get_and_post_are_not_allowed(self):
        """Logs in and sends GET and POST. Expects 405 for both and the token kept."""
        self.client.force_login(self.user)

        assert self.client.get(self.url).status_code == 405
        assert self.client.post(self.url).status_code == 405
        assert Token.objects.filter(key=self.token.key).exists()

    def test_new_token_issued_after_deletion(self):
        """Deletes the token, then requests one from api-token-auth/. Expects a new key different from the deleted one."""
        self.client.force_login(self.user)
        self.client.delete(self.url)
        self.client.logout()

        resp = self.client.post('/api/api-token-auth/', {'username': 'token_owner', 'password': 'token_owner_password'})

        assert resp.status_code == 200
        assert resp.json()['token'] != self.token.key
        assert Token.objects.get(user=self.user).key == resp.json()['token']
