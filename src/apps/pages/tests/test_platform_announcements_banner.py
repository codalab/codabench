from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from announcements.models import Announcement


class PlatformAnnouncementsBannerTests(TestCase):

    def test_platform_announcement_shown_above_header_on_home_page(self):
        """
        Creates an active platform announcement and loads the home page.
        Expects the banner with the announcement text to be rendered before the header.
        """
        Announcement.objects.create(text="platform text", placement=Announcement.PLACEMENT_PLATFORM)

        content = self.client.get(reverse('pages:home')).content.decode()

        assert 'class="platform-announcements-banner"' in content
        assert "platform text" in content
        assert content.index('class="platform-announcements-banner"') < content.index("<!-- Page Contents -->")

    def test_platform_announcement_shown_on_other_pages(self):
        """
        Creates an active platform announcement and loads the search page.
        Expects the banner with the announcement text to be rendered there too.
        """
        Announcement.objects.create(text="platform text", placement=Announcement.PLACEMENT_PLATFORM)

        content = self.client.get(reverse('pages:search')).content.decode()

        assert 'class="platform-announcements-banner"' in content
        assert "platform text" in content

    def test_home_page_announcement_not_shown_in_banner(self):
        """
        Creates only an active home page announcement and loads the search page.
        Expects no banner and no announcement text, since home page announcements
        are only shown on the home page.
        """
        Announcement.objects.create(text="home page text", placement=Announcement.PLACEMENT_HOME_PAGE)

        content = self.client.get(reverse('pages:search')).content.decode()

        assert 'class="platform-announcements-banner"' not in content
        assert "home page text" not in content

    def test_inactive_platform_announcement_not_shown(self):
        """
        Creates only an inactive platform announcement and loads the search page.
        Expects no banner and no announcement text.
        """
        Announcement.objects.create(text="inactive text", placement=Announcement.PLACEMENT_PLATFORM, is_active=False)

        content = self.client.get(reverse('pages:search')).content.decode()

        assert 'class="platform-announcements-banner"' not in content
        assert "inactive text" not in content

    def test_platform_announcements_ordered_by_priority_then_newest(self):
        """
        Creates two priority 0 platform announcements with different creation dates
        and one priority 5 platform announcement that is the newest of all.
        Expects the banner rows in the order: newer priority 0, older priority 0, priority 5.
        """
        current = now()
        Announcement.objects.create(
            text="low priority old",
            priority=0,
            created_when=current - timedelta(days=2),
            placement=Announcement.PLACEMENT_PLATFORM,
        )
        Announcement.objects.create(
            text="low priority new",
            priority=0,
            created_when=current,
            placement=Announcement.PLACEMENT_PLATFORM,
        )
        Announcement.objects.create(
            text="high priority",
            priority=5,
            created_when=current + timedelta(days=1),
            placement=Announcement.PLACEMENT_PLATFORM,
        )

        content = self.client.get(reverse('pages:search')).content.decode()

        assert content.index("low priority new") < content.index("low priority old") < content.index("high priority")

    def test_platform_announcement_levels_render_with_their_styles(self):
        """
        Creates one platform announcement of each level and loads the search page.
        Expects each row to have its level class, and the plain row to have no icon.
        """
        Announcement.objects.create(level=Announcement.LEVEL_CRITICAL, text="critical text", placement=Announcement.PLACEMENT_PLATFORM)
        Announcement.objects.create(level=Announcement.LEVEL_WARNING, text="warning text", placement=Announcement.PLACEMENT_PLATFORM)
        Announcement.objects.create(level=Announcement.LEVEL_INFO, text="info text", placement=Announcement.PLACEMENT_PLATFORM)
        Announcement.objects.create(level=Announcement.LEVEL_PLAIN, text="plain text", placement=Announcement.PLACEMENT_PLATFORM)

        content = self.client.get(reverse('pages:search')).content.decode()

        assert 'class="platform-announcement platform-announcement-critical"' in content
        assert 'class="platform-announcement platform-announcement-warning"' in content
        assert 'class="platform-announcement platform-announcement-info"' in content
        assert 'class="platform-announcement platform-announcement-plain"' in content
        # Plain announcements have no icon between their wrapper and content
        plain_block = content.split('class="platform-announcement platform-announcement-plain"')[1].split("plain text")[0]
        assert "platform-announcement-icon" not in plain_block

    def test_banner_hidden_without_platform_announcements(self):
        """
        Loads the search page with no announcements at all.
        Expects the banner wrapper not to be rendered.
        """
        content = self.client.get(reverse('pages:search')).content.decode()

        assert 'class="platform-announcements-banner"' not in content
