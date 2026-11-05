from django.test import TestCase
from django.urls import reverse

from factories import UserFactory


class SettingsPagesAccessTests(TestCase):

    def setUp(self):
        self.settings_urls = [
            reverse('settings:notifications'),
            reverse('settings:change_password'),
            reverse('settings:delete_account'),
        ]

    def test_user_can_open_settings_pages(self):
        """
        Logs in and opens the three settings pages.
        Expects each page to load.
        """
        self.client.force_login(UserFactory())

        for url in self.settings_urls:
            assert self.client.get(url).status_code == 200

    def test_logged_out_visitor_is_sent_to_login(self):
        """
        Opens the three settings pages without logging in.
        Expects a redirect to the login page on each page.
        """
        for url in self.settings_urls:
            response = self.client.get(url)

            assert response.status_code == 302
            assert reverse('accounts:login') in response.url

    def test_settings_url_opens_notifications(self):
        """
        Logs in and opens /settings/.
        Expects a redirect to the notifications page.
        """
        self.client.force_login(UserFactory())

        response = self.client.get('/settings/')

        assert response.status_code == 302
        assert response.url == reverse('settings:notifications')

    def test_delete_account_page_uses_the_logged_in_user(self):
        """
        Logs in and opens the delete account page.
        Expects the data of the logged-in user in the page.
        """
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse('settings:delete_account'))

        assert f'"username": "{user.username}"' in response.context['serialized_user']


class SettingsNavigationTests(TestCase):

    def test_settings_pages_share_the_navigation(self):
        """
        Opens the three settings pages.
        Expects each page to link to all three sections and to mark its own section as active.
        """
        self.client.force_login(UserFactory())
        settings_urls = [
            reverse('settings:notifications'),
            reverse('settings:change_password'),
            reverse('settings:delete_account'),
        ]

        for url in settings_urls:
            content = self.client.get(url).content.decode()

            assert f'side-nav-link-active" href="{url}"' in content
            assert content.count('side-nav-link-active') == 1
            for other_url in settings_urls:
                assert f'href="{other_url}"' in content

    def test_change_password_page_links_to_password_reset(self):
        """
        Opens the change password section.
        Expects a link to the page that emails the password reset link.
        """
        self.client.force_login(UserFactory())

        content = self.client.get(reverse('settings:change_password')).content.decode()

        assert f'href="{reverse("accounts:password_reset")}"' in content
