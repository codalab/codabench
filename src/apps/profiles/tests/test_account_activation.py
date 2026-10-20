from datetime import datetime, timedelta
from unittest import mock

from django.conf import settings
from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from factories import UserFactory
from profiles.forms import ActivationForm
from profiles.tokens import account_activation_token


def get_message_texts(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


def get_activation_url(user, token=None):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token or account_activation_token.make_token(user)
    return reverse('profiles:activate', kwargs={'uidb64': uid, 'token': token})


class ActivateAccountTests(TestCase):
    """Tests for the activate view that the link in the activation email opens."""

    def setUp(self):
        self.user = UserFactory(username='inactive', email='inactive@example.com', is_active=False)

    def test_valid_link_activates_account(self):
        """A valid activation link activates the account and redirects to login with a success message."""
        resp = self.client.get(get_activation_url(user=self.user))

        self.user.refresh_from_db()
        assert self.user.is_active
        assert resp.status_code == 302
        assert resp.url == reverse('accounts:login')
        assert 'Your account is fully setup! Please login.' in get_message_texts(response=resp)

    def test_link_for_unknown_user_redirects_to_sign_up(self):
        """A link for a user id that does not exist redirects to sign-up with an error."""
        uid = urlsafe_base64_encode(force_bytes(999999))

        resp = self.client.get(reverse('profiles:activate', kwargs={'uidb64': uid, 'token': 'any-token'}))

        assert resp.status_code == 302
        assert resp.url == reverse('accounts:signup')
        assert 'User not found. Please sign up again.' in get_message_texts(response=resp)


class ActivationLinkValidityTests(TestCase):
    """Tests that invalid, already used and expired activation links are refused."""

    def setUp(self):
        self.user = UserFactory(username='inactive', email='inactive@example.com', is_active=False)

    def assert_link_refused(self, response):
        self.user.refresh_from_db()
        assert response.status_code == 302
        assert response.url == reverse('accounts:resend_activation')
        assert 'Activation link is invalid or expired. Please double check your link.' in \
            get_message_texts(response=response)

    def test_invalid_token_is_refused(self):
        """A link with a wrong token leaves the account inactive and redirects to resend activation with an error."""
        resp = self.client.get(get_activation_url(user=self.user, token='invalid-token'))

        self.assert_link_refused(response=resp)
        assert not self.user.is_active

    def test_used_link_cannot_be_reused(self):
        """After an account is activated, opening the same link again is refused."""
        activation_url = get_activation_url(user=self.user)
        first_resp = self.client.get(activation_url)

        second_resp = self.client.get(activation_url)

        assert first_resp.url == reverse('accounts:login')
        self.assert_link_refused(response=second_resp)

    def test_expired_link_is_refused(self):
        """A link created longer ago than PASSWORD_RESET_TIMEOUT is refused and the account stays inactive."""
        created_at = datetime.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 60)
        with mock.patch.object(account_activation_token, '_now', return_value=created_at):
            expired_token = account_activation_token.make_token(self.user)

        resp = self.client.get(get_activation_url(user=self.user, token=expired_token))

        self.assert_link_refused(response=resp)
        assert not self.user.is_active


class ResendActivationTests(TestCase):
    """Tests for the resend_activation view that sends the activation email again."""

    def setUp(self):
        self.resend_url = reverse('accounts:resend_activation')
        self.inactive_user = UserFactory(username='inactive', email='inactive@example.com', is_active=False)
        self.active_user = UserFactory(username='active', email='active@example.com', is_active=True)

    def resend(self, email):
        return self.client.post(self.resend_url, data={'email': email})

    def test_resend_page_shows_form(self):
        """Opening the resend activation page returns 200 with the email form."""
        resp = self.client.get(self.resend_url)

        assert resp.status_code == 200
        assert isinstance(resp.context['form'], ActivationForm)

    def test_resend_sends_email_to_inactive_account(self):
        """For an inactive account, an activation email with a link is sent and the user is redirected to the home page."""
        resp = self.resend(email='inactive@example.com')

        uid = urlsafe_base64_encode(force_bytes(self.inactive_user.pk))
        assert resp.status_code == 302
        assert resp.url == reverse('pages:home')
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['inactive@example.com']
        assert f'/profiles/activate/{uid}/' in mail.outbox[0].body

    def test_resend_accepts_email_with_capitals(self):
        """An email typed with capitals still finds the inactive account and sends the activation email."""
        resp = self.resend(email='Inactive@Example.com')

        assert resp.status_code == 302
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['inactive@example.com']

    def test_resend_for_unknown_email_shows_error(self):
        """For an email with no account, an error message is shown and no email is sent."""
        resp = self.resend(email='nobody@example.com')

        assert resp.status_code == 200
        assert 'No account found with this email.' in get_message_texts(response=resp)
        assert len(mail.outbox) == 0

    def test_resend_for_active_account_shows_error(self):
        """For an account that is already active, an error message is shown and no email is sent."""
        resp = self.resend(email='active@example.com')

        assert resp.status_code == 200
        assert 'This account is already active.' in get_message_texts(response=resp)
        assert len(mail.outbox) == 0
