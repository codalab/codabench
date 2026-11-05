from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from factories import UserFactory, OrganizationFactory, CompetitionFactory
from profiles.models import Membership

# The only user fields the public profile may show. Everything else is private.
PUBLIC_FIELDS = {
    'username',
    'date_joined',
    'photo',
    'display_name',
    'first_name',
    'last_name',
    'title',
    'location',
    'biography',
    'personal_url',
    'linkedin_url',
    'twitter_url',
    'github_url',
}

# User fields that must never be on the public profile
PRIVATE_FIELDS = {
    'id',
    'email',
    'password',
    'last_login',
    'is_active',
    'is_staff',
    'is_superuser',
    'is_deleted',
    'deleted_at',
    'is_banned',
    'quota',
    'organizer_direct_message_updates',
    'allow_forum_notifications',
    'allow_organization_invite_emails',
    'rabbitmq_queue_limit',
    'rabbitmq_username',
    'rabbitmq_password',
    'is_created_using_oidc',
    'oidc_organization',
    'github_uid',
    'github_info',
    'avatar_url',
    'url',
    'html_url',
    'name',
    'company',
    'bio',
}


class PublicProfilePageTests(TestCase):
    """Tests for the public profile page at /user/<username>/."""

    def get_public_profile_response_for(self, user):
        """Open the public profile page of this user."""
        return self.client.get(reverse('users:profile', kwargs={'username': user.username}))

    def test_other_user_receives_only_public_fields(self):
        """
        Logs in and opens the public profile page of another user.
        Expects only the public fields in the page data, none of the private fields, and not the email in the page.
        Why the exact list: any other field, now or added later, makes this test fail.
        """
        other_user = UserFactory(email="other.user@example.com")
        self.client.force_login(UserFactory())

        response = self.get_public_profile_response_for(other_user)

        page_fields = set(response.context['public_user'])
        assert page_fields == PUBLIC_FIELDS
        assert page_fields.isdisjoint(PRIVATE_FIELDS)
        assert other_user.email not in response.content.decode()

    def test_other_user_receives_public_details(self):
        """
        Logs in and opens the public profile page of a user with public details.
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

        content = self.get_public_profile_response_for(other_user).content.decode()

        for public_value in ["Jane", "Doe", "Researcher", "Paris", "Works on vision"]:
            assert public_value in content

    def test_owner_receives_only_public_data(self):
        """
        Logs in and opens the user's own public profile page.
        Expects only the public fields, because this page shows what others see.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.get_public_profile_response_for(user)

        assert set(response.context['public_user']) == PUBLIC_FIELDS

    def test_superuser_does_not_receive_private_data_of_another_user(self):
        """
        Logs in as a superuser and opens the public profile page of another user.
        Expects no private fields, because superusers use Django admin.
        """
        other_user = UserFactory(email="other.user@example.com")
        self.client.force_login(UserFactory(super_user=True))

        content = self.get_public_profile_response_for(other_user).content.decode()

        assert other_user.email not in content

    def test_page_receives_display_name_and_links(self):
        """
        Logs in and opens the public profile page of a user with a display name and all four links.
        Expects the display name and every link in the data for the page, and every link in the page.
        """
        links = {
            'personal_url': "https://janedoe.example.com",
            'github_url': "https://github.com/janedoe",
            'linkedin_url': "https://www.linkedin.com/in/janedoe",
            'twitter_url': "https://x.com/janedoe",
        }
        user = UserFactory(display_name="janedoe", **links)
        self.client.force_login(UserFactory())

        response = self.get_public_profile_response_for(user)

        page_data = response.context['public_user']
        content = response.content.decode()
        assert page_data['display_name'] == "janedoe"
        for field, link in links.items():
            assert page_data[field] == link
            assert f'href="{link}"' in content

    def test_logged_out_visitor_is_sent_to_login(self):
        """
        Opens a public profile page without logging in.
        Expects a redirect to the login page.
        """
        response = self.get_public_profile_response_for(UserFactory())

        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_deleted_user_has_no_public_profile(self):
        """
        Logs in and opens the public profile page of a deleted user.
        Expects a 404.
        """
        user = UserFactory(is_deleted=True)
        self.client.force_login(UserFactory())

        response = self.get_public_profile_response_for(user)

        assert response.status_code == 404

    def test_inactive_user_has_no_public_profile(self):
        """
        Logs in and opens the public profile page of an inactive user, for example one who did not confirm the email.
        Expects a 404.
        """
        user = UserFactory(is_active=False)
        self.client.force_login(UserFactory())

        response = self.get_public_profile_response_for(user)

        assert response.status_code == 404

    def test_banned_user_has_no_public_profile(self):
        """
        Logs in and opens the public profile page of a banned user.
        Expects a 404.
        """
        user = UserFactory(is_banned=True)
        self.client.force_login(UserFactory())

        response = self.get_public_profile_response_for(user)

        assert response.status_code == 404

    def test_script_in_user_data_is_not_run_by_the_page(self):
        """
        Saves a bio and a location that try to close a script block and start a new one.
        Opens the public profile page as another user.
        Expects the attack text to be escaped, so the browser cannot run it.
        Why: the bio and the location are written into the page.
        """
        attack = '</script><script>alert("attack")</script>'
        user = UserFactory(biography=attack, location=attack)
        self.client.force_login(UserFactory())

        content = self.get_public_profile_response_for(user).content.decode()

        assert 'alert("attack")' not in content
        assert '<script>alert' not in content


class PublicProfileHeadingTests(TestCase):
    """Tests for the top section of the public profile: the heading, the username and Member since."""

    def open_public_profile_of(self, user):
        """Log in as another user and open the public profile page of this user."""
        self.client.force_login(UserFactory())
        return self.client.get(reverse('users:profile', kwargs={'username': user.username}))

    def test_username_is_the_heading_when_user_has_no_name(self):
        """
        Opens the public profile of a user without a full name or display name.
        Expects the username as the heading, and not shown a second time below it.
        """
        user = UserFactory(first_name=None, last_name=None, display_name=None)

        response = self.open_public_profile_of(user)

        assert response.context['profile_name'] == user.username
        assert response.context['show_username'] is False

    def test_full_name_is_the_heading_with_display_name_in_brackets(self):
        """
        Opens the public profile of a user with a full name and a display name.
        Expects the full name as the heading, the display name in brackets, and the username below.
        """
        user = UserFactory(first_name="Jane", last_name="Doe", display_name="jdoe")

        response = self.open_public_profile_of(user)

        assert response.context['profile_name'] == "Jane Doe"
        assert response.context['display_name'] == "jdoe"
        assert response.context['show_username'] is True

    def test_member_since_shows_month_and_year(self):
        """
        Opens the public profile of a user who joined in March 2024.
        Expects Member since March 2024 in the page.
        """
        user = UserFactory(date_joined=datetime(2024, 3, 15, tzinfo=timezone.utc))

        content = self.open_public_profile_of(user).content.decode()

        assert "Member since March 2024" in content


class PublicProfileOrganizationsTests(TestCase):
    """Tests for the Organizations section of the public profile."""

    def open_public_profile_of(self, user):
        """Log in as another user and open the public profile page of this user."""
        self.client.force_login(UserFactory())
        return self.client.get(reverse('users:profile', kwargs={'username': user.username}))

    def test_organizations_of_owners_managers_participants_and_members_are_shown(self):
        """
        Adds the user to four organizations as owner, manager, participant and member.
        Expects all four organizations in the page.
        """
        user = UserFactory()
        organizations = []
        for group in [Membership.OWNER, Membership.MANAGER, Membership.PARTICIPANT, Membership.MEMBER]:
            organization = OrganizationFactory(name=f"Org of {group}")
            Membership.objects.create(organization=organization, user=user, group=group)
            organizations.append(organization)

        response = self.open_public_profile_of(user)

        content = response.content.decode()
        shown_names = {organization['name'] for organization in response.context['organizations']}
        assert shown_names == {organization.name for organization in organizations}
        for organization in organizations:
            assert organization.name in content

    def test_pending_invites_are_not_shown(self):
        """
        Invites the user to an organization, but the user has not accepted yet.
        Expects the organization not to be in the page.
        """
        user = UserFactory()
        organization = OrganizationFactory(name="Invite Only Org")
        Membership.objects.create(organization=organization, user=user, group=Membership.INVITED)

        response = self.open_public_profile_of(user)

        assert list(response.context['organizations']) == []
        assert "Invite Only Org" not in response.content.decode()

    def test_organization_email_is_not_shown(self):
        """
        Adds the user to an organization that has an email.
        Expects the organization name in the page, but not its email.
        """
        user = UserFactory()
        organization = OrganizationFactory(name="Vision Lab", email="private.lab@example.com")
        Membership.objects.create(organization=organization, user=user, group=Membership.MEMBER)

        content = self.open_public_profile_of(user).content.decode()

        assert "Vision Lab" in content
        assert "private.lab@example.com" not in content


class PublicProfileCompetitionsTests(TestCase):
    """Tests for the Competitions section of the public profile."""

    def open_public_profile_of(self, user):
        """Log in as another user and open the public profile page of this user."""
        self.client.force_login(UserFactory())
        return self.client.get(reverse('users:profile', kwargs={'username': user.username}))

    def test_created_and_co_organized_competitions_are_shown(self):
        """
        Creates a competition by the user, and one by someone else with the user as co-organizer.
        Expects both competitions in the page.
        """
        user = UserFactory()
        created = CompetitionFactory(title="Created Competition", created_by=user, published=True, logo=None)
        co_organized = CompetitionFactory(title="Co Organized Competition", published=True, logo=None, collaborators=[user])

        response = self.open_public_profile_of(user)

        shown_ids = {competition['id'] for competition in response.context['competitions']}
        content = response.content.decode()
        assert shown_ids == {created.id, co_organized.id}
        assert "Created Competition" in content
        assert "Co Organized Competition" in content

    def test_unpublished_competitions_are_not_shown(self):
        """
        Creates an unpublished competition by the user.
        Expects the competition not to be in the page.
        """
        user = UserFactory()
        CompetitionFactory(title="Draft Competition", created_by=user, published=False, logo=None)

        response = self.open_public_profile_of(user)

        assert list(response.context['competitions']) == []
        assert "Draft Competition" not in response.content.decode()

    def test_competition_private_details_are_not_shown(self):
        """
        Creates a published competition by the user with a contact email.
        Expects the competition in the page, but not its contact email or secret key.
        """
        user = UserFactory()
        competition = CompetitionFactory(
            title="Public Competition",
            created_by=user,
            published=True,
            logo=None,
            contact_email="organizer.private@example.com",
        )

        content = self.open_public_profile_of(user).content.decode()

        assert "Public Competition" in content
        assert "organizer.private@example.com" not in content
        assert str(competition.secret_key) not in content
