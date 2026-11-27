from unittest import mock

from django.test import RequestFactory, TestCase
from django.utils.text import slugify

from factories import UserFactory
from oidc_configurations.views import register_and_authenticate_user
from profiles.forms import SignUpForm
from profiles.models import User
from profiles.pipeline import get_username
from profiles.usernames import generate_unique_username


class SignUpUsernameTests(TestCase):

    def form_for(self, username):
        """The sign up form, filled with this username and valid other fields."""
        return SignUpForm(data={
            'username': username,
            'email': f'{username}@example.com',
            'password1': 'a-long-test-password-123',
            'password2': 'a-long-test-password-123',
        })

    def test_username_that_is_its_own_slug_is_accepted(self):
        for username in ['hello_world', 'hello-world', 'hello__world', 'h3ll0', 'a-_-b_c']:
            with self.subTest(username=username):
                assert self.form_for(username).is_valid(), self.form_for(username).errors

    def test_username_that_slugify_would_change_is_refused(self):
        """
        Usernames with '-' or '_' at the start or the end, or with '--'.
        Why: their slug differs from the username, see profiles/usernames.py
        """
        for username in ['hello_world__', '_hello_world', 'hello-world-', '-hello', 'hello--world', '_____']:
            with self.subTest(username=username):
                form = self.form_for(username)
                assert not form.is_valid()
                assert 'start and end with a letter or a number' in form.errors['username'][0]

    def test_username_used_as_slug_by_another_user_is_refused(self):
        """
        An older user 'hello_world__' has the slug 'hello_world'. Signing up as 'hello_world' gave a server error.
        Now the form shows an error instead.
        """
        UserFactory(username='hello_world__')

        form = self.form_for('hello_world')

        assert not form.is_valid()
        assert form.errors['username'] == ['A user with that username already exists.']

    def test_username_of_a_deleted_user_is_refused(self):
        """A deleted user keeps the username, so it cannot be used again."""
        UserFactory(username='deleted_user_1', is_deleted=True)

        assert not self.form_for('deleted_user_1').is_valid()


class GenerateUniqueUsernameTests(TestCase):

    def test_name_from_another_site_becomes_its_own_slug(self):
        assert generate_unique_username('John.Doe') == 'johndoe'
        assert generate_unique_username('_Jane_Doe__') == 'jane_doe'
        assert generate_unique_username('jane--doe') == 'jane-doe'
        assert generate_unique_username('José') == 'jose'

    def test_taken_username_gets_a_number(self):
        UserFactory(username='johndoe')
        UserFactory(username='johndoe_1')

        assert generate_unique_username('John.Doe') == 'johndoe_2'

    def test_username_taken_as_slug_gets_a_number(self):
        """'johndoe__' has the slug 'johndoe', so 'johndoe' cannot be saved."""
        UserFactory(username='johndoe__')

        assert generate_unique_username('johndoe') == 'johndoe_1'

    def test_name_with_nothing_usable_gives_the_fallback(self):
        assert generate_unique_username('!!!') == 'user'
        assert generate_unique_username('') == 'user'

    def test_long_name_is_cut_to_the_max_length(self):
        max_length = User._meta.get_field('username').max_length
        name = 'a' * (max_length - 1) + '_b'
        UserFactory(username='a' * (max_length - 1))

        username = generate_unique_username(name)

        assert len(username) <= max_length
        assert username == slugify(username)
        assert not User.objects.filter(username=username).exists()


class GithubUsernameTests(TestCase):

    def test_new_github_user_gets_a_username_that_is_its_own_slug(self):
        UserFactory(username='alice')

        assert get_username(details={'username': 'Alice', 'email': 'alice@example.com'}) == {'username': 'alice_1'}

    def test_github_user_without_login_gets_a_username_from_the_email(self):
        assert get_username(details={'username': '', 'email': 'Bob.Smith@example.com'}) == {'username': 'bobsmith'}

    def test_existing_user_keeps_the_username(self):
        user = UserFactory(username='Old.Github.Login')

        assert get_username(details={'username': 'Old.Github.Login'}, user=user) is None


class OidcUsernameTests(TestCase):

    def register(self, email, nickname):
        """Create the user as the OIDC login does, without the real login."""
        with mock.patch('oidc_configurations.views.login'):
            register_and_authenticate_user(RequestFactory().get('/'), email, nickname, organization=None)
        return User.objects.get(email=email)

    def test_new_oidc_user_gets_a_username_that_is_its_own_slug(self):
        UserFactory(username='jane_doe__')

        user = self.register('jane@example.com', 'Jane_Doe')

        assert user.username == 'jane_doe_1'
        assert user.slug == user.username

    def test_oidc_user_without_nickname_gets_a_username_from_the_email(self):
        user = self.register('john.doe@example.com', None)

        assert user.username == 'johndoe'
