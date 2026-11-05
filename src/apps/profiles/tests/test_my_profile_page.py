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


class MyProfilePageTests(TestCase):
    """Tests for the my profile page at /profile/."""

    def test_owner_receives_own_private_data(self):
        """
        Logs in and opens the my profile page.
        Expects the email and notification settings in the page data, and edit rights.
        """
        user = UserFactory(email="the.owner@example.com")
        self.client.force_login(user)

        response = self.client.get(reverse('users:my_profile'))

        page_data = json.loads(response.context['serialized_user'])
        assert page_data['email'] == "the.owner@example.com"
        assert 'organizer_direct_message_updates' in page_data
        assert 'allow_forum_notifications' in page_data
        assert 'allow_organization_invite_emails' in page_data
        assert "const can_edit = true" in response.content.decode()

    def test_organizations_and_competitions_are_not_sent(self):
        """
        Logs in and opens the my profile page.
        Expects no organizations and no organized competitions in the page data.
        """
        self.client.force_login(UserFactory())

        content = self.client.get(reverse('users:my_profile')).content.decode()

        assert "competitions_organized" not in content
        assert "organizations" not in content.split('const selected_user')[1].split('const can_edit')[0]

    def test_logged_out_visitor_is_sent_to_login(self):
        """
        Opens the my profile page without logging in.
        Expects a redirect to the login page.
        """
        response = self.client.get(reverse('users:my_profile'))

        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_script_in_user_data_is_not_run_by_the_page(self):
        """
        Saves a bio and a location that try to close the script block and start a new one.
        Opens the my profile page as the owner.
        Expects the attack text to be escaped, so the browser cannot run it.
        Why: the user data is written inside a script tag on this page.
        """
        attack = '</script><script>alert("attack")</script>'
        self.client.force_login(UserFactory(biography=attack, location=attack))

        content = self.client.get(reverse('users:my_profile')).content.decode()

        assert 'alert("attack")' not in content
        assert '<script>alert' not in content


class MyProfileUpdateTests(TestCase):
    """Tests for saving my profile, as the Edit Profile form does."""

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

    def test_update_returns_my_profile_url(self):
        """
        Logs in and updates the user's own profile.
        Expects the my profile url back, because the page goes there after saving.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.update_profile(user=user, data={'title': "Researcher"})

        assert response.json() == reverse('users:my_profile')

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


class MyProfilePhotoTests(TestCase):
    """Tests for changing the photo on my profile."""

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
