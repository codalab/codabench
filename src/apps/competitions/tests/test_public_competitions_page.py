from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from competitions.models import Competition, Tag, TagCategory
from competitions.public_competitions import read_date, read_tag_ids
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
        assert 'name="has_a_prize"' in content

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

    def test_has_a_prize_filter_shows_only_competitions_with_a_prize(self):
        """
        Creates competitions with a reward, an empty reward and no reward, and turns on Has a prize.
        Expects only the competition with a reward and a count of 1 on the Filters button.
        """
        CompetitionFactory(title="With Reward", published=True, reward="1000 dollars")
        CompetitionFactory(title="Empty Reward", published=True, reward="")
        CompetitionFactory(title="No Reward", published=True, reward=None)

        response = self.client.get(reverse('competitions:public'), {'has_a_prize': 'true'})

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
        Opens the page with a search, Has a prize and a sort.
        Expects a pill for the search, with the prefix Search:, and one for Has a prize, without a prefix.
        Each pill link keeps the other values.
        """
        CompetitionFactory(title="Vision", published=True, reward="prize")

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'has_a_prize': 'true', 'ordering': 'popular'})

        assert response.context['filter_pills'] == [
            {'prefix': "Search:", 'label': "vision", 'query': "has_a_prize=true&ordering=popular"},
            {'prefix': "", 'label': "Has a prize", 'query': "search=vision&ordering=popular"},
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
        Opens page 2 with a search and Has a prize.
        Expects each sort link to keep the search and the filter, set its sort and drop the page.
        """
        CompetitionFactory(title="Vision", published=True, reward="prize")

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'has_a_prize': 'true', 'page': '2'})

        assert [option['query'] for option in response.context['sort_options']] == [
            "search=vision&has_a_prize=true&ordering=recent",
            "search=vision&has_a_prize=true&ordering=popular",
            "search=vision&has_a_prize=true&ordering=with_most_submissions",
        ]


class PublicCompetitionsPaginationTests(TestCase):

    def test_first_page_shows_twelve_competitions_and_next_link_keeps_the_filters(self):
        """
        Creates 13 competitions with a reward and opens the page with a search and Has a prize.
        Expects 12 cards, "Page 1 of 2" and a Next link that keeps the search and the filter.
        """
        for number in range(13):
            CompetitionFactory(title=f"Vision {number}", published=True, reward="prize")

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'has_a_prize': 'true'})
        content = response.content.decode()

        assert len(response.context['competitions']) == 12
        assert 'Page 1 of 2' in content
        assert 'href="?search=vision&amp;has_a_prize=true&amp;page=2" aria-label="Next page"' in content

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


class PublicCompetitionsTagFilterTests(TestCase):

    def setUp(self):
        # Two categories, created in this order: Domain first, then Conference
        self.domain = TagCategory.objects.create(name="Domain")
        self.conference = TagCategory.objects.create(name="Conference")
        self.vision = Tag.objects.create(name="Vision", category=self.domain)
        self.nlp = Tag.objects.create(name="NLP", category=self.domain)
        self.audio = Tag.objects.create(name="Audio", category=self.domain)
        self.neurips = Tag.objects.create(name="NeurIPS", category=self.conference)

    def test_tag_filter_shows_only_competitions_with_that_tag(self):
        """
        Creates a competition with the tag Vision and one with the tag NLP, and filters by Vision.
        Expects only the Vision competition.
        """
        CompetitionFactory(title="Vision Challenge", published=True).tags.add(self.vision)
        CompetitionFactory(title="NLP Challenge", published=True).tags.add(self.nlp)

        response = self.client.get(reverse('competitions:public'), {'tags': self.vision.id})

        assert card_titles(response) == ["Vision Challenge"]

    def test_both_ways_of_sending_tags_give_the_same_list(self):
        """
        Creates competitions with the tags Vision, NLP and NeurIPS, and filters by all three in three ways:
        repeated (tags=1&tags=2&tags=3), with commas (tags=1,2,3) and mixed (tags=1,2&tags=3).
        Expects the same competitions each time.
        """
        CompetitionFactory(title="Vision Challenge", published=True).tags.add(self.vision)
        CompetitionFactory(title="NLP Challenge", published=True).tags.add(self.nlp)
        CompetitionFactory(title="NeurIPS Challenge", published=True).tags.add(self.neurips)
        CompetitionFactory(title="Audio Challenge", published=True).tags.add(self.audio)
        ids = [self.vision.id, self.nlp.id, self.neurips.id]

        repeated = self.client.get(f"{reverse('competitions:public')}?tags={ids[0]}&tags={ids[1]}&tags={ids[2]}")
        with_commas = self.client.get(f"{reverse('competitions:public')}?tags={ids[0]},{ids[1]},{ids[2]}")
        mixed = self.client.get(f"{reverse('competitions:public')}?tags={ids[0]},{ids[1]}&tags={ids[2]}")

        expected = ["NeurIPS Challenge", "NLP Challenge", "Vision Challenge"]
        assert card_titles(repeated) == expected
        assert card_titles(with_commas) == expected
        assert card_titles(mixed) == expected

    def test_any_filter_is_the_default_and_shows_competitions_with_either_tag(self):
        """
        Creates competitions with Vision, with NLP, and with both, and filters by Vision and NLP without a Match value.
        Expects all three, because Any filter is the default.
        """
        CompetitionFactory(title="Vision Only", published=True).tags.add(self.vision)
        CompetitionFactory(title="NLP Only", published=True).tags.add(self.nlp)
        CompetitionFactory(title="Both", published=True).tags.add(self.vision, self.nlp)

        response = self.client.get(f"{reverse('competitions:public')}?tags={self.vision.id}&tags={self.nlp.id}")

        assert card_titles(response) == ["Both", "NLP Only", "Vision Only"]

    def test_all_filters_shows_only_competitions_with_every_tag(self):
        """
        Creates competitions with Vision, with NLP, and with both, and filters by Vision and NLP with All filters.
        Expects only the competition with both tags.
        """
        CompetitionFactory(title="Vision Only", published=True).tags.add(self.vision)
        CompetitionFactory(title="NLP Only", published=True).tags.add(self.nlp)
        CompetitionFactory(title="Both", published=True).tags.add(self.vision, self.nlp)

        response = self.client.get(f"{reverse('competitions:public')}?tags={self.vision.id}&tags={self.nlp.id}&filter_mode=and")

        assert card_titles(response) == ["Both"]

    def test_invalid_and_unknown_tag_ids_are_ignored(self):
        """
        Creates a competition and filters by tags=abc and by a tag id that does not exist.
        Expects the text value to be skipped, and the unknown id to find nothing but to get no pill.
        """
        CompetitionFactory(title="Open Competition", published=True)

        with_text = self.client.get(reverse('competitions:public'), {'tags': 'abc'})
        with_unknown_id = self.client.get(reverse('competitions:public'), {'tags': 999999})

        assert card_titles(with_text) == ["Open Competition"]
        assert with_text.context['filters']['tag_ids'] == []
        assert card_titles(with_unknown_id) == []
        assert with_unknown_id.context['filter_pills'] == []

    def test_matching_tags_come_first_and_are_marked_on_the_card(self):
        """
        Creates a competition with the tags Audio, NLP and NeurIPS, and filters by NeurIPS.
        Expects NeurIPS first on the card and marked as a match, and the other tags after it, not marked.
        """
        competition = CompetitionFactory(title="Speech Challenge", published=True)
        competition.tags.add(self.audio, self.nlp, self.neurips)

        response = self.client.get(reverse('competitions:public'), {'tags': self.neurips.id})
        card_tags = response.context['competitions'][0]['tags']

        assert [(tag['name'], tag['is_match']) for tag in card_tags] == [
            ("NeurIPS", True),
            ("Audio", False),
            ("NLP", False),
        ]
        assert '<span class="bc-tag bc-tag-match" title="Conference">NeurIPS</span>' in response.content.decode()

    def test_tag_dropdowns_list_the_categories_and_tick_the_selected_tags(self):
        """
        Creates a competition and opens the page with the tag NLP selected.
        Expects one dropdown for each category in the order they were created, the tags sorted A to Z,
        the number of ticked tags of each category, and the NLP checkbox ticked.
        """
        CompetitionFactory(published=True)

        response = self.client.get(reverse('competitions:public'), {'tags': self.nlp.id})
        tag_categories = response.context['tag_categories']

        assert [category['name'] for category in tag_categories] == ["Domain", "Conference"]
        assert [tag['name'] for tag in tag_categories[0]['tags']] == ["Audio", "NLP", "Vision"]
        assert [category['selected_count'] for category in tag_categories] == [1, 0]
        assert f'name="tags" value="{self.nlp.id}" checked' in response.content.decode()

    def test_tag_pill_shows_its_category_and_removes_only_its_tag(self):
        """
        Creates a competition and opens the page with the tags Vision and NeurIPS selected.
        Expects one pill for each tag, with its category as the prefix,
        and each pill link keeping only the other tag.
        """
        CompetitionFactory(published=True)

        response = self.client.get(f"{reverse('competitions:public')}?tags={self.vision.id}&tags={self.neurips.id}")

        assert response.context['filter_pills'] == [
            {'prefix': "Domain:", 'label': "Vision", 'query': f"tags={self.neurips.id}"},
            {'prefix': "Conference:", 'label': "NeurIPS", 'query': f"tags={self.vision.id}"},
        ]


class PublicCompetitionsDateFilterTests(TestCase):

    def create_competition_on(self, title, created_when):
        """Create a published competition with the given creation date and time."""
        competition = CompetitionFactory(title=title, published=True)
        Competition.objects.filter(pk=competition.pk).update(created_when=created_when)
        return competition

    def test_created_dates_filter_the_list_and_the_end_date_includes_its_day(self):
        """
        Creates competitions on Feb 28, Mar 31 in the evening and Apr 1, and filters from Mar 1 to Mar 31.
        Expects only the Mar 31 one: the end date includes the whole day.
        """
        self.create_competition_on("February", datetime(2026, 2, 28, 12, tzinfo=timezone.utc))
        self.create_competition_on("March Evening", datetime(2026, 3, 31, 18, tzinfo=timezone.utc))
        self.create_competition_on("April", datetime(2026, 4, 1, 12, tzinfo=timezone.utc))

        response = self.client.get(reverse('competitions:public'), {'start_date': '2026-03-01', 'end_date': '2026-03-31'})

        assert card_titles(response) == ["March Evening"]

    def test_invalid_date_is_ignored(self):
        """
        Creates a competition and opens the page with a start date that does not exist.
        Expects the competition, no date filter and no date pill.
        """
        self.create_competition_on("Open Competition", datetime(2026, 1, 15, 12, tzinfo=timezone.utc))

        response = self.client.get(reverse('competitions:public'), {'start_date': '2026-13-45'})

        assert card_titles(response) == ["Open Competition"]
        assert response.context['filters']['start_date'] is None
        assert response.context['filter_pills'] == []

    def test_date_pills_show_the_formatted_date(self):
        """
        Opens the page with a start date of Jan 1, 2026 and an end date of Mar 31, 2026.
        Expects a Created from: pill and a Created to: pill with the dates written out,
        each linking to the list without its date.
        """
        self.create_competition_on("Open Competition", datetime(2026, 2, 1, 12, tzinfo=timezone.utc))

        response = self.client.get(reverse('competitions:public'), {'start_date': '2026-01-01', 'end_date': '2026-03-31'})

        assert response.context['filter_pills'] == [
            {'prefix': "Created from:", 'label': "Jan 1, 2026", 'query': "end_date=2026-03-31"},
            {'prefix': "Created to:", 'label': "Mar 31, 2026", 'query': "start_date=2026-01-01"},
        ]

    def test_date_boxes_show_the_selected_dates_again(self):
        """
        Opens the page with a start and an end date.
        Expects the From and To date boxes to show the same dates after the page loads.
        """
        self.create_competition_on("Open Competition", datetime(2026, 2, 1, 12, tzinfo=timezone.utc))

        content = self.client.get(reverse('competitions:public'), {'start_date': '2026-01-01', 'end_date': '2026-03-31'}).content.decode()

        assert 'name="start_date" value="2026-01-01"' in content
        assert 'name="end_date" value="2026-03-31"' in content


class PublicCompetitionsMatchAndCountTests(TestCase):

    def test_match_buttons_show_any_first_and_selected_by_default(self):
        """
        Opens the page without a Match value.
        Expects Any filter first and selected, All filters second, and the help line of Any filter.
        """
        CompetitionFactory(published=True)

        response = self.client.get(reverse('competitions:public'))
        options = response.context['filter_mode_options']

        assert [(option['label'], option['is_selected']) for option in options] == [
            ("Any filter", True),
            ("All filters", False),
        ]
        assert 'name="filter_mode" value="or" checked' in response.content.decode()
        assert "Competitions must match at least one filter or tag you pick." in response.content.decode()

    def test_all_filters_button_is_selected_with_filter_mode_and(self):
        """
        Opens the page with filter_mode=and.
        Expects All filters selected and its help line shown.
        """
        CompetitionFactory(published=True)

        response = self.client.get(reverse('competitions:public'), {'filter_mode': 'and'})
        content = response.content.decode()

        assert 'name="filter_mode" value="and" checked' in content
        assert "Competitions must match every filter and tag you pick." in content

    def test_filters_button_counts_checkboxes_dates_and_tags(self):
        """
        Opens the page with Has a prize, a start date and 2 tags.
        Expects 4 on the Filters button.
        """
        category = TagCategory.objects.create(name="Domain")
        first_tag = Tag.objects.create(name="Vision", category=category)
        second_tag = Tag.objects.create(name="NLP", category=category)
        CompetitionFactory(published=True)

        response = self.client.get(
            f"{reverse('competitions:public')}?has_a_prize=true&start_date=2026-01-01&tags={first_tag.id}&tags={second_tag.id}"
        )

        assert response.context['active_filter_count'] == 4

    def test_search_and_match_do_not_count_on_the_filters_button(self):
        """
        Opens the page with a search and All filters, and nothing else.
        Expects no number on the Filters button. Why: the search and the Match switch are not filters of the panel.
        """
        CompetitionFactory(title="Vision", published=True)

        response = self.client.get(reverse('competitions:public'), {'search': 'vision', 'filter_mode': 'and'})

        assert response.context['active_filter_count'] == 0
        assert 'class="public-competitions-badge"' not in response.content.decode()


class PublicCompetitionsReadValuesTests(TestCase):

    def test_read_tag_ids_accepts_repeated_comma_and_mixed_values(self):
        """
        Reads tag ids sent repeated, with commas, mixed, and with a repeat.
        Expects the same list of numbers for the same tags, and each id once.
        """
        assert read_tag_ids(["1", "3"]) == [1, 3]
        assert read_tag_ids(["1,3"]) == [1, 3]
        assert read_tag_ids(["1,3", "7"]) == [1, 3, 7]
        assert read_tag_ids(["3", "1,3"]) == [3, 1]

    def test_read_tag_ids_skips_values_that_are_not_numbers(self):
        """
        Reads tag ids with text, empty parts and spaces in them.
        Expects only the numbers, and an empty list when there is nothing.
        """
        assert read_tag_ids(["abc", "2", " 5 ", "1,,x"]) == [2, 5, 1]
        assert read_tag_ids([]) == []

    def test_read_date_gives_the_start_or_end_of_the_day(self):
        """
        Reads 2026-03-31 as a start date and as an end date.
        Expects midnight for the start and 23:59:59 for the end, both in UTC.
        """
        assert read_date("2026-03-31") == datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
        assert read_date("2026-03-31", end_of_day=True) == datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc)

    def test_read_date_returns_none_for_empty_or_invalid_text(self):
        """
        Reads an empty date, None, a date that does not exist and a date in another format.
        Expects None each time.
        """
        assert read_date("") is None
        assert read_date(None) is None
        assert read_date("2026-13-45") is None
        assert read_date("31/03/2026") is None
