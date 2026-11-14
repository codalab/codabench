from django.test import TestCase
from django.urls import reverse

from factories import UserFactory, CompetitionFactory, CompetitionParticipantFactory


def card_titles(response):
    """Return the titles of the competition cards on the page, in order."""
    return [competition['title'] for competition in response.context['competitions']]


class PublicCompetitionsListTests(TestCase):

    def test_page_shows_only_published_competitions(self):
        """
        Creates a published and an unpublished competition and opens the page.
        Expects only the published one.
        """
        CompetitionFactory(title="Published", published=True)
        CompetitionFactory(title="Draft", published=False)

        response = self.client.get(reverse('competitions:public'))

        assert response.status_code == 200
        assert card_titles(response) == ["Published"]

    def test_page_title_has_the_same_style_as_news(self):
        """
        Opens the page.
        Expects the title with the shared page title class, the same size as the News title.
        """
        CompetitionFactory(published=True)

        content = self.client.get(reverse('competitions:public')).content.decode()

        assert '<h1 class="hb-title">Public Benchmarks and Competitions</h1>' in content

    def test_page_uses_the_home_page_cards(self):
        """
        Creates a published competition and opens the page.
        Expects the home page card with a link to the competition.
        """
        competition = CompetitionFactory(title="Card Competition", published=True)

        content = self.client.get(reverse('competitions:public')).content.decode()

        assert 'class="bc-card"' in content
        assert f'href="/competitions/{competition.id}/"' in content

    def test_page_does_not_show_the_organizer_email(self):
        """
        Creates a competition with a contact email and an organizer with an email, and opens the page.
        Expects neither email in the page.
        """
        organizer = UserFactory(email="organizer-secret@example.com")
        CompetitionFactory(published=True, created_by=organizer, contact_email="contact-secret@example.com")

        content = self.client.get(reverse('competitions:public')).content.decode()

        assert "organizer-secret@example.com" not in content
        assert "contact-secret@example.com" not in content


class PublicCompetitionsLoggedOutTests(TestCase):

    def test_logged_out_visitor_does_not_see_create_upload_or_personal_filters(self):
        """
        Opens the page without logging in.
        Expects no Create and Upload buttons and no Participating in or Organizing filters.
        """
        CompetitionFactory(published=True)

        content = self.client.get(reverse('competitions:public')).content.decode()

        assert f'href="{reverse("competitions:create")}"' not in content
        assert f'href="{reverse("competitions:upload")}"' not in content
        assert 'name="participating_in"' not in content
        assert 'name="organizing"' not in content
        assert 'name="has_reward"' in content

    def test_logged_out_visitor_with_personal_filters_sees_all_competitions(self):
        """
        Opens the page without logging in, with the Participating in and Organizing filters in the URL.
        Expects the page to load and to ignore those filters.
        Why: the old page returned an error for this.
        """
        CompetitionFactory(title="Open Competition", published=True)

        response = self.client.get(reverse('competitions:public'), {'participating_in': 'true', 'organizing': 'true'})

        assert response.status_code == 200
        assert card_titles(response) == ["Open Competition"]
        assert response.context['filter_pills'] == []

    def test_logged_in_user_sees_create_upload_and_personal_filters(self):
        """
        Logs in and opens the page.
        Expects the Create and Upload buttons and the Participating in and Organizing filters.
        """
        CompetitionFactory(published=True)
        self.client.force_login(UserFactory())

        content = self.client.get(reverse('competitions:public')).content.decode()

        assert f'href="{reverse("competitions:create")}"' in content
        assert f'href="{reverse("competitions:upload")}"' in content
        assert 'name="participating_in"' in content
        assert 'name="organizing"' in content


class PublicCompetitionsFilterTests(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_search_finds_competitions_by_title(self):
        """
        Creates two competitions and searches for a word in one title, in other letter case.
        Expects only that competition and the search text kept in the search box.
        """
        CompetitionFactory(title="Vision Challenge", published=True)
        CompetitionFactory(title="Speech Challenge", published=True)

        response = self.client.get(reverse('competitions:public'), {'search': 'vision'})

        assert card_titles(response) == ["Vision Challenge"]
        assert 'value="vision"' in response.content.decode()

    def test_has_reward_filter_shows_only_competitions_with_a_reward(self):
        """
        Creates competitions with a reward, an empty reward and no reward, and turns on Has reward.
        Expects only the competition with a reward and a count of 1 on the Filters button.
        """
        CompetitionFactory(title="With Reward", published=True, reward="1000 dollars")
        CompetitionFactory(title="Empty Reward", published=True, reward="")
        CompetitionFactory(title="No Reward", published=True, reward=None)

        response = self.client.get(reverse('competitions:public'), {'has_reward': 'true'})

        assert card_titles(response) == ["With Reward"]
        assert response.context['active_filter_count'] == 1
        assert '<span class="public-competitions-badge">1</span>' in response.content.decode()

    def test_participating_filter_leaves_out_competitions_the_user_organizes(self):
        """
        Makes the user a participant of one competition and the creator of another, and turns on Participating in.
        Expects only the competition the user takes part in.
        """
        joined = CompetitionFactory(title="Joined", published=True)
        CompetitionParticipantFactory(user=self.user, competition=joined, status="approved")
        CompetitionFactory(title="Created", published=True, created_by=self.user)
        CompetitionFactory(title="Other", published=True)

        response = self.client.get(reverse('competitions:public'), {'participating_in': 'true'})

        assert card_titles(response) == ["Joined"]

    def test_organizing_filter_shows_created_and_co_organized_competitions(self):
        """
        Makes the user the creator of one competition and a collaborator of another, and turns on Organizing.
        Expects both competitions, each once.
        """
        CompetitionFactory(title="Created", published=True, created_by=self.user)
        CompetitionFactory(title="Co-organized", published=True, collaborators=[self.user])
        CompetitionFactory(title="Other", published=True)

        response = self.client.get(reverse('competitions:public'), {'organizing': 'true'})

        assert sorted(card_titles(response)) == ["Co-organized", "Created"]

    def test_filter_pills_link_to_the_list_without_that_filter(self):
        """
        Opens the page with a search, Has reward and a sort.
        Expects a pill for the search and one for Has reward. Each pill link keeps the other values.
        """
        CompetitionFactory(title="Vision", published=True, reward="prize")

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'has_reward': 'true', 'ordering': 'popular'})

        assert response.context['filter_pills'] == [
            {'label': "Search: vision", 'query': "has_reward=true&ordering=popular"},
            {'label': "Has reward", 'query': "search=vision&ordering=popular"},
        ]

    def test_clear_all_keeps_the_sort(self):
        """
        Opens the page with a search and the Most popular sort.
        Expects the Clear all link to keep only the sort.
        """
        CompetitionFactory(title="Vision", published=True)

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'ordering': 'popular'})

        assert response.context['clear_filters_url'] == "?ordering=popular"
        assert 'class="public-competitions-clear" href="?ordering=popular"' in response.content.decode()


class PublicCompetitionsSortTests(TestCase):

    def test_default_sort_is_most_recent_first(self):
        """
        Creates three competitions and opens the page without a sort.
        Expects the newest first and Most recent shown as the sort.
        """
        for title in ["First", "Second", "Third"]:
            CompetitionFactory(title=title, published=True)

        response = self.client.get(reverse('competitions:public'))

        assert card_titles(response) == ["Third", "Second", "First"]
        assert response.context['selected_sort_label'] == "Most recent"

    def test_most_popular_sort_uses_participants_and_newest_for_ties(self):
        """
        Creates competitions with 5, 20 and 20 participants and sorts by Most popular.
        Expects 20 participants first, and the newer of the two with 20 before the older one.
        Why: a fixed order for ties keeps a competition from showing on two pages.
        """
        CompetitionFactory(title="Small", published=True, participants_count=5)
        CompetitionFactory(title="Big Old", published=True, participants_count=20)
        CompetitionFactory(title="Big New", published=True, participants_count=20)

        response = self.client.get(reverse('competitions:public'), {'ordering': 'popular'})

        assert card_titles(response) == ["Big New", "Big Old", "Small"]
        assert response.context['selected_sort_label'] == "Most popular"

    def test_most_submissions_sort(self):
        """
        Creates competitions with 3 and 30 submissions and sorts by Most submissions.
        Expects the one with 30 first.
        """
        CompetitionFactory(title="Few", published=True, submissions_count=3)
        CompetitionFactory(title="Many", published=True, submissions_count=30)

        response = self.client.get(reverse('competitions:public'), {'ordering': 'with_most_submissions'})

        assert card_titles(response) == ["Many", "Few"]

    def test_unknown_sort_uses_most_recent(self):
        """
        Opens the page with a sort value that does not exist.
        Expects the page to load with the Most recent sort.
        """
        CompetitionFactory(title="Old", published=True)
        CompetitionFactory(title="New", published=True)

        response = self.client.get(reverse('competitions:public'), {'ordering': 'not-a-sort'})

        assert response.status_code == 200
        assert card_titles(response) == ["New", "Old"]
        assert response.context['selected_sort_label'] == "Most recent"

    def test_sort_links_keep_the_filters_and_go_to_page_one(self):
        """
        Opens page 2 with a search and Has reward.
        Expects each sort link to keep the search and the filter, set its sort and drop the page.
        """
        CompetitionFactory(title="Vision", published=True, reward="prize")

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'has_reward': 'true', 'page': '2'})

        assert [option['query'] for option in response.context['sort_options']] == [
            "search=vision&has_reward=true&ordering=recent",
            "search=vision&has_reward=true&ordering=popular",
            "search=vision&has_reward=true&ordering=with_most_submissions",
        ]


class PublicCompetitionsPaginationTests(TestCase):

    def test_first_page_shows_twelve_competitions_and_next_link_keeps_the_filters(self):
        """
        Creates 13 competitions with a reward and opens the page with a search and Has reward.
        Expects 12 cards, "Page 1 of 2" and a Next link that keeps the search and the filter.
        """
        for number in range(13):
            CompetitionFactory(title=f"Vision {number}", published=True, reward="prize")

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'has_reward': 'true'})
        content = response.content.decode()

        assert len(response.context['competitions']) == 12
        assert 'Page 1 of 2' in content
        assert 'href="?search=vision&amp;has_reward=true&amp;page=2" aria-label="Next page"' in content

    def test_second_page_shows_the_oldest_competition(self):
        """
        Creates 13 competitions and opens page 2.
        Expects only the oldest competition and "Page 2 of 2".
        """
        for number in range(13):
            CompetitionFactory(title=f"Competition {number}", published=True)

        response = self.client.get(reverse('competitions:public'), {'page': 2})

        assert card_titles(response) == ["Competition 0"]
        assert 'Page 2 of 2' in response.content.decode()

    def test_no_pagination_when_competitions_fit_on_one_page(self):
        """
        Creates 12 competitions and opens the page.
        Expects 12 cards and no pagination.
        """
        for number in range(12):
            CompetitionFactory(published=True)

        response = self.client.get(reverse('competitions:public'))

        assert len(response.context['competitions']) == 12
        assert 'class="cb-pagination"' not in response.content.decode()


class PublicCompetitionsEmptyStateTests(TestCase):

    def test_empty_state_without_public_competitions(self):
        """
        Opens the page when no competition is published.
        Expects the empty state with a button to the home page, and no search or filters.
        """
        CompetitionFactory(published=False)

        content = self.client.get(reverse('competitions:public')).content.decode()

        assert '<h2 class="empty-state-title">There are no public competitions yet.</h2>' in content
        assert 'href="/">Return to Home</a>' in content
        assert 'id="public-competitions-filters"' not in content

    def test_empty_state_for_no_results_has_a_clear_filters_button(self):
        """
        Opens the page with a search that finds nothing and the Most popular sort.
        Expects the no results empty state, a Clear filters button that keeps the sort, and the search still shown.
        """
        CompetitionFactory(title="Vision", published=True)

        content = self.client.get(reverse('competitions:public'), {'search': 'nothing', 'ordering': 'popular'}).content.decode()

        assert '<h2 class="empty-state-title">No competitions match your search.</h2>' in content
        assert 'href="?ordering=popular">Clear filters</a>' in content
        assert 'id="public-competitions-filters"' in content

    def test_search_text_is_escaped(self):
        """
        Searches for text with HTML in it.
        Expects the text escaped in the search box and the pill, and no script tag in the page.
        """
        CompetitionFactory(published=True)

        content = self.client.get(reverse('competitions:public'), {'search': '<script>alert(1)</script>'}).content.decode()

        assert '<script>alert(1)</script>' not in content
        assert '&lt;script&gt;alert(1)&lt;/script&gt;' in content
