from django.test import TestCase

from factories import UserFactory


class UserUpdateProtectedFieldsTests(TestCase):

    def test_user_cannot_change_own_email_or_username(self):
        """
        Logs in and sends a new email, username and job title.
        Expects the job title to be saved, and the email and username to stay the same.
        Why: the request still returns 200 because read-only fields are ignored, so the saved values must be checked.
        """
        user = UserFactory(username="original_name", email="original@example.com")
        self.client.force_login(user)

        response = self.client.patch(
            f'/api/users/{user.id}/',
            data={'email': "changed@example.com", 'username': "changed_name", 'title': "Researcher"},
            content_type='application/json',
        )

        user.refresh_from_db()
        assert response.status_code == 200
        assert user.title == "Researcher"
        assert user.email == "original@example.com"
        assert user.username == "original_name"
