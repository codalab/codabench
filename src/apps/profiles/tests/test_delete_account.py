from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from factories import UserFactory
from profiles.tokens import account_deletion_token


class DeleteAccountTests(TestCase):

    def setUp(self):
        """Replace the mail sender. Why: tests must not send real emails."""
        patcher = mock.patch('profiles.views.codalab_send_mail')
        self.send_mail = patcher.start()
        self.addCleanup(patcher.stop)

    def request_account_deletion(self, username, password):
        """Send the delete request that the delete modal sends."""
        return self.client.delete(
            '/api/delete_account/',
            data={'username': username, 'password': password},
            content_type='application/json',
        )

    def get_delete_link_for(self, user, token=None):
        """Return the link from the confirmation email. A token can be given to build a wrong link."""
        return reverse('accounts:delete', kwargs={
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': token or account_deletion_token.make_token(user),
        })

    def test_correct_details_send_confirmation_email(self):
        """
        Logs in and sends the delete request with the right username and password.
        Expects success, one email to the user, and the account not deleted yet.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.request_account_deletion(username=user.username, password="test")

        user.refresh_from_db()
        assert response.json()["success"] is True
        self.send_mail.assert_called_once()
        assert self.send_mail.call_args.kwargs["to_email"] == [user.email]
        assert user.is_deleted is False

    def test_wrong_password_shows_wrong_password(self):
        """
        Logs in and sends the delete request with the wrong password.
        Expects the error Wrong password, and no email.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.request_account_deletion(username=user.username, password="wrong-password")

        assert response.json() == {"success": False, "error": "Wrong password"}
        self.send_mail.assert_not_called()

    def test_wrong_username_shows_wrong_username(self):
        """
        Logs in and sends the delete request with the wrong username.
        Expects the error Wrong username, and no email.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.request_account_deletion(username="someone-else", password="test")

        assert response.json() == {"success": False, "error": "Wrong username"}
        self.send_mail.assert_not_called()

    def test_email_link_deletes_account_and_logs_out(self):
        """
        Logs in and opens the link from the confirmation email.
        Expects the account deleted, the user logged out, and the home page with a success message.
        Why: this link used to end on a 405 error, because it redirected to the logout page.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(self.get_delete_link_for(user), follow=True)

        user.refresh_from_db()
        assert response.status_code == 200
        assert response.redirect_chain == [(reverse('pages:home'), 302)]
        assert user.is_deleted is True
        assert '_auth_user_id' not in self.client.session
        assert "Your account has been removed!" in [str(message) for message in response.context['messages']]

    def test_email_link_works_when_logged_out(self):
        """
        Opens the link from the confirmation email without logging in.
        Expects the account deleted and the home page.
        Why: people often open the email on another device.
        """
        user = UserFactory()

        response = self.client.get(self.get_delete_link_for(user), follow=True)

        user.refresh_from_db()
        assert response.status_code == 200
        assert user.is_deleted is True

    def test_invalid_email_link_keeps_account(self):
        """
        Logs in and opens a delete link with a wrong token.
        Expects the account kept, the user still logged in, and an error message.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(self.get_delete_link_for(user, token="wrong-token"), follow=True)

        user.refresh_from_db()
        assert user.is_deleted is False
        assert '_auth_user_id' in self.client.session
        assert "Confirmation link is invalid or expired." in [str(message) for message in response.context['messages']]
