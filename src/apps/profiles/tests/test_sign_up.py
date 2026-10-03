import smtplib
from unittest import mock

from django.conf import settings
from django.contrib.messages import get_messages
from django.core import mail
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from factories import UserFactory
from profiles.forms import SignUpForm
from profiles.models import User, DeletedUser

PASSWORD = 'Xyz12345!long'


class SignUpFormTests(TestCase):
    """Tests for the email validation in SignUpForm."""

    def setUp(self):
        self.existing_user = UserFactory(username='existing', email='existing@example.com')

    def make_form(self, email='newuser@example.com', username='newuser', password2=PASSWORD):
        return SignUpForm(data={
            'username': username,
            'email': email,
            'password1': PASSWORD,
            'password2': password2,
        })

    def test_valid_data_is_accepted(self):
        """A form with a new username, a new email and matching passwords is valid."""
        form = self.make_form()

        assert form.is_valid()

    def test_username_with_invalid_characters_is_rejected(self):
        """Usernames with capitals, spaces or other symbols are rejected; only lowercase letters, numbers, '-' and '_' are allowed."""
        for username in ['NewUser', 'new user', 'new.user', 'new@user']:
            form = self.make_form(username=username)

            assert not form.is_valid(), username
            assert 'username' in form.errors, username

    def test_username_with_allowed_characters_is_accepted(self):
        """A username made of lowercase letters, numbers, '-' and '_' is valid."""
        form = self.make_form(username='new_user-01')

        assert form.is_valid()

    def test_username_shorter_than_5_characters_is_rejected(self):
        """A username with fewer than 5 characters is rejected."""
        form = self.make_form(username='abcd')

        assert not form.is_valid()
        assert form.errors['username'] == ['Username must have at least 5 characters and at most 50 characters']

    def test_username_longer_than_50_characters_is_rejected(self):
        """A username with more than 50 characters is rejected by the field's max length (50 in the User model)."""
        form = self.make_form(username='a' * 51)

        assert not form.is_valid()
        assert form.errors['username'] == ['Ensure this value has at most 50 characters (it has 51).']

    def test_existing_username_is_rejected(self):
        """A username that already belongs to an account is rejected."""
        form = self.make_form(username='existing')

        assert not form.is_valid()
        assert 'username' in form.errors

    def test_email_with_asterisk_is_rejected(self):
        """An email containing '*' is rejected."""
        form = self.make_form(email='new*user@example.com')

        assert not form.is_valid()
        assert 'email' in form.errors

    def test_mismatched_passwords_are_rejected(self):
        """Different values in the two password fields make the form invalid."""
        form = self.make_form(password2='Different12345!long')

        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_existing_email_with_different_capitals_is_rejected(self):
        """An email that matches an existing account apart from capitals makes the form invalid with an 'already exists' error."""
        form = self.make_form(email='Existing@Example.com')

        assert not form.is_valid()
        assert form.errors['email'] == ['An account with this email already exists.']

    def test_new_email_is_accepted_and_lowercased(self):
        """A new email with capitals is valid and is cleaned to lowercase."""
        form = self.make_form(email='NewUser@Example.com')

        assert form.is_valid()
        assert form.cleaned_data['email'] == 'newuser@example.com'

    def test_email_longer_than_200_characters_is_rejected(self):
        """An email longer than the 200 characters the database allows makes the form invalid."""
        long_email = 'a' * 64 + '@' + 'b' * 63 + '.' + 'c' * 63 + '.dddd.com'  # 201 characters
        form = self.make_form(email=long_email)

        assert len(long_email) == 201
        assert not form.is_valid()
        assert 'email' in form.errors


class SignUpViewTests(TestCase):
    """Tests for the sign_up view, including the cases that used to return a 500."""

    def setUp(self):
        self.sign_up_url = reverse('accounts:signup')

    def sign_up(self, email='newuser@example.com', username='newuser', password2=PASSWORD):
        return self.client.post(self.sign_up_url, data={
            'username': username,
            'email': email,
            'password1': PASSWORD,
            'password2': password2,
        })

    def get_message_texts(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_sign_up_page_shows_form(self):
        """Opening the sign-up page returns 200 with the sign-up form."""
        resp = self.client.get(self.sign_up_url)

        assert resp.status_code == 200
        assert isinstance(resp.context['form'], SignUpForm)

    @override_settings(ENABLE_SIGN_UP=False)
    def test_sign_up_redirects_to_login_when_disabled(self):
        """When sign-up is disabled, both opening and submitting the sign-up page redirect to login and create no user."""
        get_resp = self.client.get(self.sign_up_url)
        post_resp = self.sign_up()

        assert get_resp.status_code == 302
        assert get_resp.url == reverse('accounts:login')
        assert post_resp.status_code == 302
        assert post_resp.url == reverse('accounts:login')
        assert not User.objects.filter(username='newuser').exists()

    def test_sign_up_sends_activation_email(self):
        """A valid sign-up sends one activation email to the user's address with an activation link, and shows a success message."""
        resp = self.sign_up()

        user = User.objects.get(username='newuser')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['newuser@example.com']
        assert f'/profiles/activate/{uid}/' in mail.outbox[0].body
        message_texts = self.get_message_texts(response=resp)
        assert len(message_texts) == 1
        assert 'please go to your email newuser@example.com inbox' in message_texts[0]

    def test_sign_up_with_deleted_email_is_rejected(self):
        """Signing up with the email of a deleted account shows an error message, creates no user and sends no email."""
        DeletedUser.objects.create(username='olduser', email='newuser@example.com')

        resp = self.sign_up()

        assert resp.status_code == 200
        assert 'This email has been previously deleted and cannot be used.' in self.get_message_texts(response=resp)
        assert not User.objects.filter(username='newuser').exists()
        assert len(mail.outbox) == 0

    def test_sign_up_with_invalid_form_shows_errors(self):
        """Submitting an invalid form (mismatched passwords) shows the form again with errors, creates no user and sends no email."""
        resp = self.sign_up(password2='Different12345!long')

        assert resp.status_code == 200
        assert 'password2' in resp.context['form'].errors
        assert not User.objects.filter(username='newuser').exists()
        assert len(mail.outbox) == 0

    def test_sign_up_creates_inactive_user_with_lowercase_email(self):
        """A valid sign-up redirects to the home page and creates an inactive user with the email in lowercase."""
        resp = self.sign_up(email='NewUser@Example.com')

        assert resp.status_code == 302
        assert resp.url == reverse('pages:home')
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert not user.is_active

    def test_sign_up_with_existing_email_in_different_capitals_shows_form_error(self):
        """Signing up with an existing email in different capitals shows the form again instead of a 500, and creates no user."""
        UserFactory(username='existing', email='existing@example.com')

        resp = self.sign_up(email='Existing@Example.com')

        assert resp.status_code == 200
        assert 'An account with this email already exists.' in resp.content.decode()
        assert not User.objects.filter(username='newuser').exists()

    def test_sign_up_when_save_fails_shows_error_message(self):
        """When saving the user fails (e.g. a double submit created the account first), the form is shown again with an error instead of a 500."""
        with mock.patch.object(User, 'save', side_effect=IntegrityError('duplicate key')):
            resp = self.sign_up(email='newuser@example.com')

        assert resp.status_code == 200
        assert 'An account with this username or email already exists.' in self.get_message_texts(response=resp)
        assert not User.objects.filter(username='newuser').exists()

    def test_sign_up_when_activation_email_fails_shows_error_message(self):
        """When sending the activation email fails, the user is still created and redirected, with an error that links to resend activation and the contact email."""
        with mock.patch('profiles.views.EmailMessage.send', side_effect=smtplib.SMTPException('mail server down')):
            resp = self.sign_up(email='newuser@example.com')

        assert resp.status_code == 302
        assert User.objects.filter(username='newuser', is_active=False).exists()
        message_texts = self.get_message_texts(response=resp)
        assert len(message_texts) == 1
        assert 'We could not send the activation email to newuser@example.com.' in message_texts[0]
        assert reverse('accounts:resend_activation') in message_texts[0]
        assert settings.CONTACT_EMAIL in message_texts[0]
