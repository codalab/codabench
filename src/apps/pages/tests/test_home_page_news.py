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

    def test_view_all_and_read_more_links(self):
        """
        Creates a post with a link and a long text.
        Expects the "View all news" link and a "Read more" link to the post's link.
        """
        NewsPost.objects.create(title="Release", link="https://example.com/release", text="word " * 200)

        content = self.get_home().content.decode()

        assert 'href="/news/"' in content
        assert 'class="news-card-link" href="https://example.com/release"' in content

    def test_read_more_goes_to_news_page_without_link(self):
        """
        Creates a post without a link.
        Expects its "Read more" link to point to the news page.
        """
        NewsPost.objects.create(title="No link", text="text")

        assert 'class="news-card-link" href="/news/"' in self.get_home().content.decode()

    def test_date_shown_as_pill_text(self):
        """
        Creates a post dated Sep 3, 2026 and loads the home page.
        Expects the date pill to show "Sep 3, 2026".
        """
        NewsPost.objects.create(title="Dated", text="text", created_when=datetime(2026, 9, 3, 12, tzinfo=timezone.utc))

        assert '<div class="news-card-date">Sep 3, 2026</div>' in self.get_home().content.decode()
