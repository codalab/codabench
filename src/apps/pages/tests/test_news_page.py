from django.test import TestCase
from django.urls import reverse

from announcements.models import NewsPost


class NewsPageTests(TestCase):

    def test_shows_all_posts_newest_first(self):
        """
        Creates 5 news posts and loads the news page.
        Expects all 5 in the context, newest first.
        """
        for number in range(5):
            NewsPost.objects.create(title=f"Post {number}", text="text")

        resp = self.client.get(reverse('pages:news'))

        assert [post['title'] for post in resp.context['news_posts']] == ["Post 4", "Post 3", "Post 2", "Post 1", "Post 0"]

    def test_first_page_shows_twelve_newest_posts_and_next_button(self):
        """
        Creates 13 news posts and loads the news page.
        Expects the 12 newest posts, "Page 1 of 2" and only a Next button to page 2.
        """
        for number in range(13):
            NewsPost.objects.create(title=f"Post {number}", text="text")

        resp = self.client.get(reverse('pages:news'))
        content = resp.content.decode()

        assert [post['title'] for post in resp.context['news_posts']] == [f"Post {number}" for number in range(12, 0, -1)]
        assert 'Page 1 of 2' in content
        assert 'class="cb-pagination-button" href="?page=2" aria-label="Next page"><i class="arrow right icon"></i></a>' in content
        assert content.count('class="cb-pagination-button"') == 1

    def test_second_page_shows_oldest_post_and_previous_button(self):
        """
        Creates 13 news posts and loads page 2.
        Expects only the oldest post, "Page 2 of 2" and only a Previous button to page 1.
        """
        for number in range(13):
            NewsPost.objects.create(title=f"Post {number}", text="text")

        resp = self.client.get(reverse('pages:news'), {'page': 2})
        content = resp.content.decode()

        assert [post['title'] for post in resp.context['news_posts']] == ["Post 0"]
        assert 'Page 2 of 2' in content
        assert 'class="cb-pagination-button" href="?page=1" aria-label="Previous page"><i class="arrow left icon"></i></a>' in content
        assert content.count('class="cb-pagination-button"') == 1

    def test_no_pagination_when_posts_fit_on_one_page(self):
        """
        Creates 12 news posts and loads the news page.
        Expects all 12 posts and no pagination.
        """
        for number in range(12):
            NewsPost.objects.create(title=f"Post {number}", text="text")

        resp = self.client.get(reverse('pages:news'))

        assert len(resp.context['news_posts']) == 12
        assert 'class="cb-pagination"' not in resp.content.decode()

    def test_invalid_page_shows_first_page(self):
        """
        Creates 13 news posts and loads the page "abc".
        Expects the first page instead of an error.
        """
        for number in range(13):
            NewsPost.objects.create(title=f"Post {number}", text="text")

        resp = self.client.get(reverse('pages:news'), {'page': 'abc'})

        assert resp.status_code == 200
        assert 'Page 1 of 2' in resp.content.decode()

    def test_too_high_page_shows_last_page(self):
        """
        Creates 13 news posts and loads page 99.
        Expects the last page instead of an error.
        """
        for number in range(13):
            NewsPost.objects.create(title=f"Post {number}", text="text")

        resp = self.client.get(reverse('pages:news'), {'page': 99})

        assert resp.status_code == 200
        assert 'Page 2 of 2' in resp.content.decode()

    def test_news_title_shown_without_view_all_link(self):
        """
        Creates a post and loads the news page.
        Expects the "News" title and the card, without the "View all" link.
        """
        NewsPost.objects.create(title="Post", text="text")

        content = self.client.get(reverse('pages:news')).content.decode()

        assert '<h2 class="news-section-title">News</h2>' in content
        assert 'class="news-card"' in content
        assert 'news-view-all' not in content

    def test_empty_state_shown_without_posts(self):
        """
        Loads the news page without any news posts.
        Expects the "News" title, the empty image, the empty title and description,
        a button to the home page and no cards.
        """
        content = self.client.get(reverse('pages:news')).content.decode()

        assert '<h2 class="news-section-title">News</h2>' in content
        assert 'class="empty-state-image" src="/static/img/empty.png"' in content
        assert '<h2 class="empty-state-title">There\'s no news to share right now.</h2>' in content
        assert '<p class="empty-state-description">Check back soon for updates on Codabench.</p>' in content
        assert 'class="empty-state-button" href="/">Return to Home</a>' in content
        assert 'class="news-cards"' not in content

    def test_cards_have_read_more_and_open_link(self):
        """
        Creates a post with text and a link and loads the news page.
        Expects the same "Read more" button and "Open link" as the home page cards.
        """
        NewsPost.objects.create(title="Post", link="https://example.com/release", text="word " * 200)

        content = self.client.get(reverse('pages:news')).content.decode()

        assert '<button type="button" class="news-card-toggle" hidden>' in content
        assert 'class="news-card-link" href="https://example.com/release" target="_blank"' in content
