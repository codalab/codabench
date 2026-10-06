import json
import os
import tempfile
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from factories import UserFactory


class HeaderTests(TestCase):

    def test_header_on_every_page(self):
        """
        Loads the home page and the public datasets page.
        Expects both to have the header with the Codabench logo and tagline.
        """
        for url in [reverse('pages:home'), reverse('datasets:public')]:
            content = self.client.get(url).content.decode()

            assert 'id="header"' in content
            assert 'id="header-logo"' in content
            assert "Open-source platform for AI benchmarks and competitions" in content

    def test_supported_by_banner_only_on_home_page(self):
        """
        Loads the home page and the public datasets page.
        Expects the "Supported by" banner only on the home page.
        """
        home = self.client.get(reverse('pages:home')).content.decode()
        datasets = self.client.get(reverse('datasets:public')).content.decode()

        assert 'class="supported-by-banner"' in home
        assert 'class="supported-by-banner"' not in datasets

    def test_version_tag_from_version_file(self):
        """
        Points the version file to a temporary file with tag v9.99.
        Expects the header version tag to show v9.99 and link to its release page.
        """
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as version_file:
            json.dump({"tag_name": "v9.99", "html_url": "https://example.com/v9.99"}, version_file)
        self.addCleanup(os.remove, version_file.name)

        with mock.patch('utils.context_processors.VERSION_FILE_PATH', version_file.name):
            content = self.client.get(reverse('pages:home')).content.decode()

        assert 'class="header-version" href="https://example.com/v9.99"' in content
        assert ">v9.99</a>" in content

    def test_version_tag_hidden_without_version_file(self):
        """
        Points the version file to a path that does not exist.
        Expects no version tag in the header.
        """
        with mock.patch('utils.context_processors.VERSION_FILE_PATH', '/does/not/exist.json'):
            content = self.client.get(reverse('pages:home')).content.decode()

        assert 'class="header-version"' not in content


class MobileMenuTests(TestCase):

    def get_mobile_menu(self):
        """Load the home page and return only the mobile menu part."""
        content = self.client.get(reverse('pages:home')).content.decode()
        return content.split('id="mobile_menu"')[1].split('class="pusher"')[0]

    def test_logged_out_shows_login(self):
        """
        Loads the home page without logging in.
        Expects the mobile menu to have the main links and Login, and no Logout.
        """
        menu = self.get_mobile_menu()

        assert reverse('competitions:public') in menu
        assert reverse('datasets:public') in menu
        assert reverse('accounts:login') in menu
        assert "Logout" not in menu

    def test_logged_in_shows_user_menu(self):
        """
        Logs in and loads the home page.
        Expects the mobile menu to show the username and the user menu with Logout, and no Login.
        """
        user = UserFactory()
        self.client.force_login(user)

        menu = self.get_mobile_menu()

        assert user.username in menu
        assert "Logout" in menu
        assert reverse('accounts:login') not in menu

    def test_single_logout_form(self):
        """
        Logs in and loads the home page (the user menu is in the header and the mobile menu).
        Expects the logout form only once on the page.
        """
        self.client.force_login(UserFactory())

        content = self.client.get(reverse('pages:home')).content.decode()

        assert content.count('id="logout-form"') == 1


class FooterTests(TestCase):

    def test_footer_columns_and_copyright(self):
        """
        Loads the home page.
        Expects the footer with its three link columns and the copyright line.
        """
        content = self.client.get(reverse('pages:home')).content.decode()
        footer = content.split('id="footer"')[1]

        for title in ["Quick links", "Resources", "Legal &amp; About"]:
            assert f'<h4 class="footer-title">{title}</h4>' in footer
        assert 'class="footer-bottom"' in footer
        assert "Codabench" in footer.split('class="footer-bottom"')[1]

    def test_footer_contact_email(self):
        """
        Sets the contact email and loads the home page.
        Expects the footer to link to it.
        """
        with self.settings(CONTACT_EMAIL="team@example.com"):
            content = self.client.get(reverse('pages:home')).content.decode()

        assert 'href="mailto:team@example.com"' in content.split('id="footer"')[1]
