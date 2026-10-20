from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from factories import UserFactory
from profiles.forms import LoginForm
from profiles.models import User


class LoginViewTests(TestCase):
    """Tests for the log_in view, logging in with a username or an email."""

    def setUp(self):
        self.login_url = reverse('accounts:login')
        self.user = UserFactory(username='loginuser', email='loginuser@example.com', password='test')

    def log_in(self, username, password='test', url=None):
        return self.client.post(url or self.login_url, data={'username': username, 'password': password})

    def get_message_texts(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def is_logged_in(self):
        return '_auth_user_id' in self.client.session

    def test_login_page_shows_form(self):
        """Opening the login page returns 200 with the login form."""
        resp = self.client.get(self.login_url)

        assert resp.status_code == 200
        assert isinstance(resp.context['form'], LoginForm)

    def test_login_with_username(self):
        """Logging in with the username and correct password logs the user in and redirects to the home page."""
        resp = self.log_in(username='loginuser')

        assert resp.status_code == 302
        assert resp.url == reverse('pages:home')
        assert self.is_logged_in()

    def test_login_with_email(self):
        """Logging in with the email and correct password logs the user in and redirects to the home page."""
        resp = self.log_in(username='loginuser@example.com')

        assert resp.status_code == 302
        assert resp.url == reverse('pages:home')
        assert self.is_logged_in()

    def test_login_with_capitals_in_username_or_email(self):
        """The username or email is lowercased before lookup, so typing it with capitals still logs the user in."""
        for username in ['LoginUser', 'LoginUser@Example.com']:
            self.client.logout()

            resp = self.log_in(username=username)

            assert resp.status_code == 302, username
            assert self.is_logged_in(), username

    def test_login_redirects_to_next_page(self):
        """When the login page has a 'next' parameter, a successful login redirects to that page."""
        resp = self.log_in(username='loginuser', url=f'{self.login_url}?next=/competitions/')

        assert resp.status_code == 302
        assert resp.url == '/competitions/'

    def test_login_with_wrong_password_is_rejected(self):
        """A wrong password shows 'Invalid login/password' and does not log the user in."""
        resp = self.log_in(username='loginuser', password='wrong-password')

        assert resp.status_code == 200
        assert 'Invalid login/password' in self.get_message_texts(response=resp)
        assert not self.is_logged_in()

    def test_login_with_unknown_user_is_rejected(self):
        """A username that has no account shows 'Invalid login/password' and does not log anyone in."""
        resp = self.log_in(username='nobody')

        assert resp.status_code == 200
        assert 'Invalid login/password' in self.get_message_texts(response=resp)
        assert not self.is_logged_in()

    def test_login_with_inactive_account_shows_activation_error(self):
        """An account that is not activated yet is not logged in and the page shows the activation error."""
        UserFactory(username='inactiveuser', email='inactiveuser@example.com', password='test', is_active=False)

        resp = self.log_in(username='inactiveuser')

        assert resp.status_code == 200
        assert resp.context['activation_error'] == \
            'Your account is not activated. Please check your email for the activation link'
        assert not self.is_logged_in()

    def test_login_with_banned_account_is_rejected(self):
        """A banned account with the correct password is not logged in and the page shows the banned message."""
        UserFactory(username='banneduser', email='banneduser@example.com', password='test', is_banned=True)

        resp = self.log_in(username='banneduser')

        assert resp.status_code == 200
        assert 'You are banned from using Codabench' in self.get_message_texts(response=resp)
        assert not self.is_logged_in()

    def test_login_with_deleted_account_is_rejected(self):
        """An account marked as deleted cannot log in and shows 'Invalid login/password'."""
        User.objects.filter(pk=self.user.pk).update(is_deleted=True)

        resp = self.log_in(username='loginuser')

        assert resp.status_code == 200
        assert 'Invalid login/password' in self.get_message_texts(response=resp)
        assert not self.is_logged_in()
