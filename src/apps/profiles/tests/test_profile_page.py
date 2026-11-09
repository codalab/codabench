import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from factories import UserFactory

# A valid image of 1 by 1 pixels
SMALL_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


class ProfilePagePrivateDataTests(TestCase):

    def get_profile_response_for(self, user):
        """Open the profile page of this user."""
        return self.client.get(reverse('profiles:user_profile', kwargs={'username': user.username}))

    def test_other_user_does_not_receive_private_data(self):
        """
        Logs in and opens the profile page of another user.
        Expects the private fields not to be in the page, and no edit rights.
        """
        other_user = UserFactory(email="other.user@example.com")
        self.client.force_login(UserFactory())

        response = self.get_profile_response_for(other_user)

        page_data = json.loads(response.context['serialized_user'])
        content = response.content.decode()
        assert 'email' not in page_data
        assert other_user.email not in content
        assert "allow_forum_notifications" not in content
        assert "const can_edit = false" in content

    def test_owner_receives_own_private_data(self):
        """
        Logs in and opens the user's own profile page.
        Expects the email and notification settings in the page data, and edit rights.
        """
        user = UserFactory(email="the.owner@example.com")
        self.client.force_login(user)

        response = self.get_profile_response_for(user)

        page_data = json.loads(response.context['serialized_user'])
        assert page_data['email'] == "the.owner@example.com"
        assert 'organizer_direct_message_updates' in page_data
        assert 'allow_forum_notifications' in page_data
        assert 'allow_organization_invite_emails' in page_data
        assert "const can_edit = true" in response.content.decode()

    def test_superuser_cannot_edit_another_user_on_this_page(self):
        """
        Logs in as a superuser and opens the profile page of another user.
        Expects no edit rights and no private fields, because superusers use Django admin.
        """
        other_user = UserFactory(email="other.user@example.com")
        self.client.force_login(UserFactory(super_user=True))

        content = self.get_profile_response_for(other_user).content.decode()

        assert "const can_edit = false" in content
        assert other_user.email not in content

    def test_other_user_does_not_receive_notification_settings(self):
        """
        Logs in and opens the profile page of another user.
        Expects none of the three notification settings in the page.
        """
        other_user = UserFactory()
        self.client.force_login(UserFactory())

        content = self.get_profile_response_for(other_user).content.decode()

        assert "organizer_direct_message_updates" not in content
        assert "allow_forum_notifications" not in content
        assert "allow_organization_invite_emails" not in content

    def test_other_user_receives_public_details(self):
        """
        Logs in and opens the profile page of a user with public details.
        Expects the name, job title, location and bio in the page.
        """
        other_user = UserFactory(
            first_name="Jane",
            last_name="Doe",
            title="Researcher",
            location="Paris",
            biography="Works on vision",
        )
        self.client.force_login(UserFactory())

        content = self.get_profile_response_for(other_user).content.decode()

        for public_value in ["Jane", "Doe", "Researcher", "Paris", "Works on vision"]:
            assert public_value in content

    def test_logged_out_visitor_is_sent_to_login(self):
        """
        Opens a profile page without logging in.
        Expects a redirect to the login page.
        """
        response = self.get_profile_response_for(UserFactory())

        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_page_receives_display_name_and_links(self):
        """
        Logs in and opens a profile page of a user with a display name and a link.
        Expects both in the data for the page.
        """
        user = UserFactory(display_name="janedoe", github_url="https://github.com/janedoe")
        self.client.force_login(UserFactory())

        response = self.get_profile_response_for(user)

        page_data = json.loads(response.context['serialized_user'])
        assert page_data['display_name'] == "janedoe"
        assert page_data['github_url'] == "https://github.com/janedoe"


class ProfileEditPermissionTests(TestCase):

    def update_profile(self, user, data):
        """Send the update request that the Edit Profile form sends."""
        return self.client.patch(f'/api/users/{user.id}/', data=data, content_type='application/json')

    def test_user_can_update_own_profile(self):
        """
        Logs in and updates the user's own profile.
        Expects the changes to be saved.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.update_profile(user=user, data={'title': "Researcher", 'location': "Paris"})

        user.refresh_from_db()
        assert response.status_code == 200
        assert user.title == "Researcher"
        assert user.location == "Paris"

    def test_update_returns_profile_url(self):
        """
        Logs in and updates the user's own profile.
        Expects the profile url back, because the page goes there after saving.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.update_profile(user=user, data={'title': "Researcher"})

        assert response.json() == reverse('profiles:user_profile', args=[user.username])

    def test_user_cannot_update_another_user(self):
        """
        Logs in and updates the profile of another user.
        Expects a 403, and nothing saved.
        """
        other_user = UserFactory(title="Original")
        self.client.force_login(UserFactory())

        response = self.update_profile(user=other_user, data={'title': "Changed"})

        other_user.refresh_from_db()
        assert response.status_code == 403
        assert other_user.title == "Original"

    def test_superuser_cannot_update_another_user(self):
        """
        Logs in as a superuser and updates the profile of another user.
        Expects a 403, and nothing saved, because superusers use Django admin.
        """
        other_user = UserFactory(title="Original")
        self.client.force_login(UserFactory(super_user=True))

        response = self.update_profile(user=other_user, data={'title': "Changed"})

        other_user.refresh_from_db()
        assert response.status_code == 403
        assert other_user.title == "Original"

    def test_logged_out_visitor_cannot_update_a_profile(self):
        """
        Updates a profile without logging in.
        Expects the request to be refused, and nothing saved.
        """
        user = UserFactory(title="Original")

        response = self.update_profile(user=user, data={'title': "Changed"})

        user.refresh_from_db()
        assert response.status_code in [401, 403]
        assert user.title == "Original"


class ProfilePhotoTests(TestCase):

    def setUp(self):
        """Replace the photo storage. Why: tests must not write real files."""
        storage = get_user_model()._meta.get_field('photo').storage
        for method, value in [('save', 'photos/me.png'), ('url', '/photos/me.png')]:
            patcher = mock.patch.object(storage, method, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.user = UserFactory()
        self.client.force_login(self.user)

    def update_photo(self, photo):
        """Send a photo update like the Edit Profile form."""
        return self.client.patch(
            f'/api/users/{self.user.id}/',
            data={'photo': photo},
            content_type='application/json',
        )

    def test_valid_photo_is_saved(self):
        """
        Sends a small valid image as the new photo.
        Expects success, and the photo saved on the user.
        """
        photo = json.dumps({'file_name': "me.png", 'data': SMALL_PNG_BASE64})

        response = self.update_photo(photo=photo)

        self.user.refresh_from_db()
        assert response.status_code == 200
        assert self.user.photo.name == 'photos/me.png'

    def test_invalid_photo_is_refused(self):
        """
        Sends a value that is not a photo.
        Expects a 400, and no photo saved on the user.
        """
        response = self.update_photo(photo="this is not a photo")

        self.user.refresh_from_db()
        assert response.status_code == 400
        assert not self.user.photo


class ProfilePageContentTests(TestCase):

    def test_script_in_user_data_is_not_run_by_the_page(self):
        """
        Saves a bio and a location that try to close the script block and start a new one.
        Opens the page as the owner and as another user.
        Expects the attack text to be escaped for both, so the browser cannot run it.
        Why: the user data is written inside a script tag on this page.
        """
        attack = '</script><script>alert("attack")</script>'
        user = UserFactory(biography=attack, location=attack)
        profile_url = reverse('profiles:user_profile', kwargs={'username': user.username})

        for viewer in [user, UserFactory()]:
            self.client.force_login(viewer)

            content = self.client.get(profile_url).content.decode()

            assert 'alert("attack")' not in content
            assert '<script>alert' not in content

    def test_organizations_and_competitions_are_not_sent(self):
        """
        Logs in and opens the user's own profile page.
        Expects no organizations and no organized competitions in the page data.
        """
        user = UserFactory()
        self.client.force_login(user)

        content = self.client.get(reverse('profiles:user_profile', kwargs={'username': user.username})).content.decode()

        assert "competitions_organized" not in content
        assert "organizations" not in content.split('const selected_user')[1].split('const can_edit')[0]
