from django.test import TestCase
from django.urls import reverse

from factories import UserFactory


class LogoutViewTests(TestCase):
    """Tests for the logout view, which the site calls with a POST form."""

    def setUp(self):
        self.logout_url = reverse('accounts:logout')
        self.user = UserFactory(username='logoutuser', password='test')
        self.client.login(username='logoutuser', password='test')

    def is_logged_in(self):
        return '_auth_user_id' in self.client.session

    def test_logout_logs_user_out_and_redirects_home(self):
        """A POST to logout ends the session and redirects to the home page (LOGOUT_REDIRECT_URL)."""
        assert self.is_logged_in()

        resp = self.client.post(self.logout_url)

        assert resp.status_code == 302
        assert resp.url == '/'
        assert not self.is_logged_in()

    def test_logout_with_get_is_not_allowed(self):
        """A GET to logout is refused with 405 and the user stays logged in."""
        resp = self.client.get(self.logout_url)

        assert resp.status_code == 405
        assert self.is_logged_in()
