import re
from datetime import datetime, timedelta, timezone
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from competitions.models import Competition
from factories import CompetitionFactory, UserFactory
from pages.home_page import get_featured_benchmarks, get_popular_benchmarks, get_recent_benchmarks


def make_benchmark(participants_count=1, created_when=None, **kwargs):
    """Create a competition and set its participants count directly (saving can change it)."""
    competition = CompetitionFactory(created_when=created_when or now(), **kwargs)
    Competition.objects.filter(pk=competition.pk).update(participants_count=participants_count)
    competition.refresh_from_db()
    return competition


def first_items(pool, count):
    """Replacement for random.sample that keeps the pool order, to check which pool was used."""
    return pool[:count]


class FeaturedBenchmarksTests(TestCase):

    def test_returns_three_random_published_featured(self):
        """
        Creates 5 published featured benchmarks, 1 unpublished featured one and 1 published
        non-featured one. Expects 3 distinct benchmarks, all published and featured.
        """
        featured = [make_benchmark(published=True, is_featured=True) for _ in range(5)]
        make_benchmark(published=False, is_featured=True)
        make_benchmark(published=True, is_featured=False)

        result = get_featured_benchmarks()

        assert len(result) == 3
        assert len(set(result)) == 3
        assert set(result) <= set(featured)

    def test_returns_all_when_fewer_than_three(self):
        """
        Creates 2 published featured benchmarks.
        Expects both to be returned.
        """
        featured = [make_benchmark(published=True, is_featured=True) for _ in range(2)]

        assert set(get_featured_benchmarks()) == set(featured)

    def test_empty_when_nothing_is_featured(self):
        """
        Creates only non-featured benchmarks.
        Expects an empty list, so the Featured section is hidden.
        """
        make_benchmark(published=True, is_featured=False)

        assert get_featured_benchmarks() == []


class PopularBenchmarksTests(TestCase):

    def test_picks_from_eight_with_most_participants(self):
        """
        Creates 10 published non-featured benchmarks with 1 to 10 participants.
        Expects 3 distinct benchmarks, all from the 8 with the most participants (3 to 10).
        """
        benchmarks = [make_benchmark(participants_count=count, published=True) for count in range(1, 11)]
        top_eight = set(benchmarks[2:])

        result = get_popular_benchmarks()

        assert len(result) == 3
        assert len(set(result)) == 3
        assert set(result) <= top_eight

    def test_pool_is_ordered_by_participants(self):
        """
        Creates 4 benchmarks with different participant counts and makes the random pick
        keep the pool order. Expects the pool to start with the most participants.
        """
        low = make_benchmark(participants_count=1, published=True)
        high = make_benchmark(participants_count=50, published=True)
        mid = make_benchmark(participants_count=10, published=True)
        lower_mid = make_benchmark(participants_count=5, published=True)

        with mock.patch('pages.home_page.random.sample', side_effect=first_items):
            result = get_popular_benchmarks()

        assert result == [high, mid, lower_mid]
        assert low not in result

    def test_leaves_out_featured_and_unpublished(self):
        """
        Creates a featured and an unpublished benchmark with many participants, and one
        published non-featured benchmark with few. Expects only the non-featured published one.
        """
        normal = make_benchmark(participants_count=1, published=True)
        make_benchmark(participants_count=100, published=True, is_featured=True)
        make_benchmark(participants_count=100, published=False)

        assert get_popular_benchmarks() == [normal]


class RecentBenchmarksTests(TestCase):

    def test_picks_from_eight_latest(self):
        """
        Creates 10 published non-featured benchmarks created one day apart.
        Expects 3 distinct benchmarks, all from the 8 newest.
        """
        current = now()
        benchmarks = [make_benchmark(published=True, created_when=current - timedelta(days=days)) for days in range(10)]
        newest_eight = set(benchmarks[:8])

        result = get_recent_benchmarks()

        assert len(result) == 3
        assert len(set(result)) == 3
        assert set(result) <= newest_eight

    def test_pool_is_ordered_by_newest(self):
        """
        Creates 4 benchmarks with different creation dates and makes the random pick
        keep the pool order. Expects the pool to start with the newest.
        """
        current = now()
        oldest = make_benchmark(published=True, created_when=current - timedelta(days=30))
        newest = make_benchmark(published=True, created_when=current)
        middle = make_benchmark(published=True, created_when=current - timedelta(days=5))
        older = make_benchmark(published=True, created_when=current - timedelta(days=10))

        with mock.patch('pages.home_page.random.sample', side_effect=first_items):
            result = get_recent_benchmarks()

        assert result == [newest, middle, older]
        assert oldest not in result

    def test_leaves_out_featured_unpublished_and_excluded_ids(self):
        """
        Creates a featured, an unpublished, an excluded (shown in Popular) and a normal benchmark.
        Expects only the normal one to be returned.
        """
        normal = make_benchmark(published=True)
        make_benchmark(published=True, is_featured=True)
        make_benchmark(published=False)
        excluded = make_benchmark(published=True)

        assert get_recent_benchmarks(exclude_ids=[excluded.id]) == [normal]


class HomePageBenchmarkSectionsTests(TestCase):

    def get_home(self):
        return self.client.get(reverse('pages:home'))

    def test_featured_section_hidden_without_featured(self):
        """
        Creates only non-featured benchmarks and loads the home page.
        Expects no Featured section and no Featured pill.
        """
        make_benchmark(published=True)

        content = self.get_home().content.decode()

        assert "Featured Benchmarks" not in content
        assert "bc-featured-pill" not in content

    def test_featured_section_shown_with_featured(self):
        """
        Creates a featured benchmark and loads the home page.
        Expects the Featured section with a featured card and the Featured pill.
        """
        make_benchmark(published=True, is_featured=True)

        content = self.get_home().content.decode()

        assert "Featured Benchmarks" in content
        assert 'class="bc-card bc-featured"' in content
        assert '<span class="bc-featured-pill">Featured</span>' in content

    def test_three_cards_each_without_repeats(self):
        """
        Creates 2 featured and 8 normal published benchmarks and loads the home page.
        Expects 3 cards in Popular and in Recent, no benchmark in both, and the
        featured ones only in Featured.
        """
        featured_ids = {make_benchmark(published=True, is_featured=True).id for _ in range(2)}
        for _ in range(8):
            make_benchmark(published=True)

        context = self.get_home().context
        popular_ids = {benchmark["id"] for benchmark in context["popular_benchmarks"]}
        recent_ids = {benchmark["id"] for benchmark in context["recent_benchmarks"]}

        assert {benchmark["id"] for benchmark in context["featured_benchmarks"]} == featured_ids
        assert len(popular_ids) == 3
        assert len(recent_ids) == 3
        assert not popular_ids & recent_ids
        assert not featured_ids & (popular_ids | recent_ids)

    def test_card_shows_benchmark_values(self):
        """
        Creates a benchmark with an organizer display name, 1,234 participants, 56 submissions
        and a reward. Expects its card to link to the benchmark in a new tab and show the
        title, organizer, counts with separators and the Prize pill.
        """
        competition = make_benchmark(
            participants_count=1234, published=True, title="Card Title", reward="1000 EUR",
            created_by=UserFactory(display_name="Org Name"),
        )
        Competition.objects.filter(pk=competition.pk).update(submissions_count=56)

        content = self.get_home().content.decode()

        assert f'href="/competitions/{competition.id}/" target="_blank"' in content
        assert '<h3 class="bc-title">Card Title</h3>' in content
        assert '<span class="bc-organizer-name">Org Name</span>' in content
        assert "1,234 participants" in content
        assert "56 submissions" in content
        assert 'class="bc-pill bc-prize"' in content

    def test_card_logo_or_initial(self):
        """
        Creates one benchmark with a logo and one without.
        Expects the first card to show the logo image and the second to show
        the first letter of its title instead.
        """
        make_benchmark(published=True, title="With logo")
        make_benchmark(published=True, title="no logo", logo=None)

        content = self.get_home().content.decode()

        assert re.search(r'class="bc-logo">\s*<img src="[^"]*logos/', content)
        assert re.search(r'class="bc-logo">\s*<span>N</span>', content)

    def test_card_organizer_fallbacks(self):
        """
        Creates a benchmark whose creator has no display name, and one whose creator was deleted.
        Expects the first card to show the creator's username, and only one organizer pill
        on the page (none for the deleted creator).
        """
        creator = UserFactory(display_name=None)
        make_benchmark(published=True, created_by=creator)
        without_creator = make_benchmark(published=True)
        Competition.objects.filter(pk=without_creator.pk).update(created_by=None)

        content = self.get_home().content.decode()

        assert f'<span class="bc-organizer-name">{creator.username}</span>' in content
        assert content.count('class="bc-pill bc-organizer"') == 1

    def test_card_date_is_formatted(self):
        """
        Creates a benchmark without phases created on Sep 23, 2026 (the card date then
        falls back to the creation date). Expects the card to show "Sep 23, 2026".
        """
        make_benchmark(published=True, created_when=datetime(2026, 9, 23, 12, tzinfo=timezone.utc))

        assert re.search(r'calendar alternate icon"></i>Sep 23, 2026<', self.get_home().content.decode())

    def test_empty_message_without_benchmarks(self):
        """
        Loads the home page without any published benchmarks.
        Expects the "No benchmarks yet." message in Popular and Recent.
        """
        assert self.get_home().content.decode().count("No benchmarks yet.") == 2
