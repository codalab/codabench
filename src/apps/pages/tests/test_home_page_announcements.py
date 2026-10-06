from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from announcements.models import Announcement


class HomePageAnnouncementTests(TestCase):

    def get_home(self):
        return self.client.get(reverse('pages:home'))

    def test_only_active_announcements_are_shown(self):
        """
        Creates one active and one inactive announcement and loads the home page.
        Expects only the active announcement in the context and the inactive
        announcement's text to be absent from the rendered page.
        """
        Announcement.objects.create(title="Active", text="active text")
        Announcement.objects.create(title="Inactive", text="inactive text", is_active=False)

        resp = self.get_home()

        assert [a['title'] for a in resp.context['announcements']] == ["Active"]
        assert "inactive text" not in resp.content.decode()

    def test_announcements_ordered_by_priority_then_newest(self):
        """
        Creates two priority 0 announcements with different creation dates and
        one priority 5 announcement that is the newest of all.
        Expects the lower priority to come first, and within the same priority
        the newest to come first: [newer priority 0, older priority 0, priority 5].
        """
        current = now()
        Announcement.objects.create(title="Low priority old", priority=0, created_when=current - timedelta(days=2))
        Announcement.objects.create(title="Low priority new", priority=0, created_when=current)
        Announcement.objects.create(title="High priority", priority=5, created_when=current + timedelta(days=1))

        resp = self.get_home()

        assert [a['title'] for a in resp.context['announcements']] == [
            "Low priority new", "Low priority old", "High priority"
        ]

    def test_levels_render_with_their_styles(self):
        """
        Creates one announcement of each level and loads the home page.
        Expects each one to render as a card with its level class
        (announcement-critical, -warning, -info, -plain), and the plain
        announcement to have no icon.
        """
        Announcement.objects.create(level=Announcement.LEVEL_CRITICAL, text="critical text")
        Announcement.objects.create(level=Announcement.LEVEL_WARNING, text="warning text")
        Announcement.objects.create(level=Announcement.LEVEL_INFO, text="info text")
        Announcement.objects.create(level=Announcement.LEVEL_PLAIN, text="plain text")

        content = self.get_home().content.decode()

        assert 'class="announcement announcement-critical"' in content
        assert 'class="announcement announcement-warning"' in content
        assert 'class="announcement announcement-info"' in content
        assert 'class="announcement announcement-plain"' in content
        # Plain announcements have no icon between their wrapper and content
        plain_block = content.split('class="announcement announcement-plain"')[1].split("plain text")[0]
        assert "announcement-icon" not in plain_block

    def test_announcement_section_hidden_without_announcements(self):
        """
        Creates only an inactive announcement and loads the home page.
        Expects the announcements wrapper not to be rendered at all.
        """
        Announcement.objects.create(text="hidden", is_active=False)

        content = self.get_home().content.decode()

        assert 'class="announcements"' not in content
