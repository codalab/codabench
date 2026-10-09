from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from announcements.models import NewsPost


class HomePageNewsTests(TestCase):

    def get_home(self):
        return self.client.get(reverse('pages:home'))

    def test_shows_three_newest_posts(self):
        """
        Creates 5 news posts and loads the home page.
        Expects only the 3 newest in the context, newest first, and the oldest
        title to be absent from the page.
        """
        for number in range(5):
            NewsPost.objects.create(title=f"Post {number}", text="text")

        resp = self.get_home()

        assert [post['title'] for post in resp.context['news_posts']] == ["Post 4", "Post 3", "Post 2"]
        assert "Post 0" not in resp.content.decode()

    def test_section_hidden_without_posts(self):
        """
        Loads the home page without any news posts.
        Expects the Latest News section not to be rendered.
        """
        assert 'class="news-section"' not in self.get_home().content.decode()

    def test_view_all_news_link(self):
        """
        Creates a post and loads the home page.
        Expects the "View all news" link to the news page.
        """
        NewsPost.objects.create(title="Post", text="text")

        assert 'class="news-view-all" href="/news/"' in self.get_home().content.decode()

    def test_open_link_only_for_posts_with_a_link(self):
        """
        Creates one post with a link and one without.
        Expects a single "Open link" to the post's link, opening in a new tab.
        """
        NewsPost.objects.create(title="With link", link="https://example.com/release", text="text")
        NewsPost.objects.create(title="Without link", text="text")

        content = self.get_home().content.decode()

        assert content.count('class="news-card-link"') == 1
        assert 'class="news-card-link" href="https://example.com/release" target="_blank"' in content

    def test_read_more_is_a_button_not_a_link(self):
        """
        Creates a post with text and loads the home page.
        Expects "Read more" to be a hidden button (shown by the page script only when the
        text is cut off) and not to link anywhere.
        """
        NewsPost.objects.create(title="Post", text="word " * 200)

        content = self.get_home().content.decode()

        assert '<button type="button" class="news-card-toggle" hidden>' in content
        assert 'href="/news/">Read more' not in content

    def test_date_shown_as_pill_text(self):
        """
        Creates a post dated Sep 3, 2026 and loads the home page.
        Expects the date pill to show "Sep 3, 2026".
        """
        NewsPost.objects.create(title="Dated", text="text", created_when=datetime(2026, 9, 3, 12, tzinfo=timezone.utc))

        assert '<div class="news-card-date">Sep 3, 2026</div>' in self.get_home().content.decode()
