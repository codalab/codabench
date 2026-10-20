from datetime import datetime, timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from factories import UserFactory
from profiles.models import User

NEW_PASSWORD = 'NewXyz12345!long'


def get_reset_link(user, token=None):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token or default_token_generator.make_token(user)
    return reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})


def set_new_password(client, reset_link):
    # Django redirects the link to a set-password URL and keeps the token in the session
    link_resp = client.get(reset_link)
    set_password_resp = client.post(link_resp.url, data={
        'new_password1': NEW_PASSWORD,
        'new_password2': NEW_PASSWORD,
    })
    return link_resp, set_password_resp


class PasswordResetRequestTests(TestCase):
    """Tests for requesting a password reset email (CustomPasswordResetView)."""

    def setUp(self):
        self.reset_url = reverse('accounts:password_reset')
        self.user = UserFactory(username='resetuser', email='resetuser@example.com', password='test')

    def request_reset(self, email):
        return self.client.post(self.reset_url, data={'email': email})

    def test_password_reset_page_shows_form(self):
        """Opening the password reset page returns 200."""
        resp = self.client.get(self.reset_url)

        assert resp.status_code == 200

    def test_reset_request_sends_email_with_reset_link(self):
        """Requesting a reset for a registered email redirects to the 'done' page and sends one email with a reset link."""
        resp = self.request_reset(email='resetuser@example.com')

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        assert resp.status_code == 302
        assert resp.url == reverse('accounts:password_reset_done')
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['resetuser@example.com']
        assert f'/accounts/reset/{uid}/' in mail.outbox[0].body

    def test_reset_request_accepts_email_with_capitals(self):
        """An email typed with capitals still finds the account and sends the reset email."""
        resp = self.request_reset(email='ResetUser@Example.com')

        assert resp.status_code == 302
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['resetuser@example.com']

    def test_reset_request_for_unknown_email_sends_nothing(self):
        """For an email with no account, the user still sees the 'done' page (no hint whether the email exists) and no email is sent."""
        resp = self.request_reset(email='nobody@example.com')

        assert resp.status_code == 302
        assert resp.url == reverse('accounts:password_reset_done')
        assert len(mail.outbox) == 0

    def test_reset_request_for_inactive_account_sends_nothing(self):
        """Inactive (not yet activated) accounts do not get a reset email."""
        UserFactory(username='inactiveuser', email='inactiveuser@example.com', is_active=False)

        resp = self.request_reset(email='inactiveuser@example.com')

        assert resp.status_code == 302
        assert resp.url == reverse('accounts:password_reset_done')
        assert len(mail.outbox) == 0

    def test_reset_request_for_banned_account_sends_nothing(self):
        """Banned accounts do not get a reset email; the user still sees the 'done' page."""
        UserFactory(username='banneduser', email='banneduser@example.com', is_banned=True)

        resp = self.request_reset(email='banneduser@example.com')

        assert resp.status_code == 302
        assert resp.url == reverse('accounts:password_reset_done')
        assert len(mail.outbox) == 0


class PasswordResetLoggedInTests(TestCase):
    """Tests for the 'Change Password' menu item, which uses the same reset flow while the user is logged in."""

    def setUp(self):
        self.user = UserFactory(username='resetuser', email='resetuser@example.com', password='test')
        self.client.login(username='resetuser', password='test')
        # Logging in updates last_login, which is part of the reset token, so reload the user before building links
        self.user.refresh_from_db()

    def test_logged_in_user_can_request_reset_email(self):
        """A logged-in user requesting a reset is redirected to the 'done' page and gets one reset email."""
        resp = self.client.post(reverse('accounts:password_reset'), data={'email': 'resetuser@example.com'})

        assert resp.status_code == 302
        assert resp.url == reverse('accounts:password_reset_done')
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['resetuser@example.com']

    def test_setting_new_password_logs_user_out(self):
        """After a logged-in user sets a new password, their current session is no longer logged in and they must log in again."""
        set_new_password(client=self.client, reset_link=get_reset_link(user=self.user))

        resp = self.client.get(reverse('pages:home'))

        self.user.refresh_from_db()
        assert self.user.check_password(NEW_PASSWORD)
        assert not resp.wsgi_request.user.is_authenticated


class PasswordResetConfirmTests(TestCase):
    """Tests for the reset link page (CustomPasswordResetConfirmView): a valid link sets a new password,
    invalid, already used, banned user's and expired links are refused."""

    def setUp(self):
        self.user = UserFactory(username='resetuser', email='resetuser@example.com', password='test')

    def assert_link_refused(self, response):
        assert response.status_code == 200
        assert response.context['validlink'] is False

    def test_valid_link_sets_new_password(self):
        """Opening a valid reset link and submitting a new password changes the password and redirects to the 'complete' page."""
        link_resp, set_password_resp = set_new_password(client=self.client, reset_link=get_reset_link(user=self.user))

        self.user.refresh_from_db()
        assert link_resp.status_code == 302
        assert set_password_resp.status_code == 302
        assert set_password_resp.url == reverse('accounts:password_reset_complete')
        assert self.user.check_password(NEW_PASSWORD)

    def test_invalid_token_is_refused(self):
        """A reset link with a wrong token shows the page as invalid and the password stays the same."""
        resp = self.client.get(get_reset_link(user=self.user, token='invalid-token'))

        self.user.refresh_from_db()
        self.assert_link_refused(response=resp)
        assert self.user.check_password('test')

    def test_used_link_cannot_be_reused(self):
        """After a password is reset, opening the same link again shows it as invalid."""
        reset_link = get_reset_link(user=self.user)
        set_new_password(client=self.client, reset_link=reset_link)

        resp = self.client.get(reset_link, follow=True)

        self.assert_link_refused(response=resp)

    def test_link_of_banned_user_is_refused(self):
        """A reset link that was created before the user was banned shows as invalid and the password stays the same."""
        reset_link = get_reset_link(user=self.user)
        User.objects.filter(pk=self.user.pk).update(is_banned=True)

        resp = self.client.get(reset_link)

        self.user.refresh_from_db()
        self.assert_link_refused(response=resp)
        assert self.user.check_password('test')

    def test_expired_link_is_refused(self):
        """A reset link created longer ago than PASSWORD_RESET_TIMEOUT shows as invalid and the password stays the same."""
        created_at = datetime.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 60)
        with mock.patch.object(default_token_generator, '_now', return_value=created_at):
            expired_token = default_token_generator.make_token(self.user)

        resp = self.client.get(get_reset_link(user=self.user, token=expired_token))

        self.user.refresh_from_db()
        self.assert_link_refused(response=resp)
        assert self.user.check_password('test')
