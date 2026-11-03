from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from factories import UserFactory
from profiles.models import User, DeletedUser

PASSWORD = 'Xyz12345!long'


class DeletedUserTests(TestCase):
    """Tests that a deleted account (User.delete) cannot be used to sign up, log in, reset the password or resend activation."""

    def setUp(self):
        self.user = UserFactory(username='deleteduser', email='deleteduser@example.com', password='test')
        self.deleted_username = f'deleted_user_{self.user.pk}'
        self.user.delete()
        # Deleting a user sends notice emails, clear them so tests only see emails sent afterwards
        mail.outbox.clear()

    def get_message_texts(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def is_logged_in(self):
        return '_auth_user_id' in self.client.session

    def test_delete_anonymizes_account_and_keeps_record(self):
        """Deleting a user renames the account, removes its email, deactivates it and stores the old username and email in DeletedUser."""
        self.user.refresh_from_db()

        assert self.user.username == self.deleted_username
        assert self.user.email is None
        assert self.user.is_deleted
        assert not self.user.is_active
        assert DeletedUser.objects.filter(
            user_id=self.user.pk,
            username='deleteduser',
            email='deleteduser@example.com',
        ).exists()

    def test_sign_up_with_deleted_email_is_rejected(self):
        """Signing up again with a deleted account's email shows an error and creates no user."""
        resp = self.client.post(reverse('accounts:signup'), data={
            'username': 'newuser',
            'email': 'deleteduser@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })

        assert resp.status_code == 200
        assert 'This email has been previously deleted and cannot be used.' in self.get_message_texts(response=resp)
        assert not User.objects.filter(username='newuser').exists()

    def test_login_with_deleted_account_is_rejected(self):
        """Logging in with the old username, the old email or the anonymized username is rejected with 'Invalid login/password'."""
        for username in ['deleteduser', 'deleteduser@example.com', self.deleted_username]:
            resp = self.client.post(reverse('accounts:login'), data={'username': username, 'password': 'test'})

            assert resp.status_code == 200, username
            assert 'Invalid login/password' in self.get_message_texts(response=resp), username
            assert not self.is_logged_in(), username

    def test_password_reset_for_deleted_email_sends_nothing(self):
        """Requesting a password reset for a deleted account's email shows the 'done' page and sends no email."""
        resp = self.client.post(reverse('accounts:password_reset'), data={'email': 'deleteduser@example.com'})

        assert resp.status_code == 302
        assert resp.url == reverse('accounts:password_reset_done')
        assert len(mail.outbox) == 0

    def test_resend_activation_for_deleted_email_finds_no_account(self):
        """Resending activation for a deleted account's email shows 'No account found' and sends no email."""
        resp = self.client.post(reverse('accounts:resend_activation'), data={'email': 'deleteduser@example.com'})

        assert resp.status_code == 200
        assert 'No account found with this email.' in self.get_message_texts(response=resp)
        assert len(mail.outbox) == 0
