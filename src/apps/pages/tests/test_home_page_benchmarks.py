import re
from datetime import datetime, timedelta, timezone
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from competitions.models import Competition, Tag, TagCategory
from factories import CompetitionFactory, UserFactory
from profiles.models import User
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
        title, organizer, the counts in their pills with separators, and the Prize pill.
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
        assert re.search(r'title="Participants"><i [^>]*></i>1,234<', content)
        assert re.search(r'title="Submissions"><i [^>]*></i>56<', content)
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
        Expects the first card to show the creator's username, and only one organizer line
        on the page (none for the deleted creator).
        """
        creator = UserFactory(display_name=None)
        make_benchmark(published=True, created_by=creator)
        without_creator = make_benchmark(published=True)
        Competition.objects.filter(pk=without_creator.pk).update(created_by=None)

        content = self.get_home().content.decode()

        assert f'<span class="bc-organizer-name">{creator.username}</span>' in content
        assert content.count('class="bc-organizer"') == 1

    def test_card_date_is_formatted(self):
        """
        Creates a benchmark without phases created on Sep 23, 2026 (the card date then
        falls back to the creation date). Expects the card to show "Sep 23, 2026".
        """
        make_benchmark(published=True, created_when=datetime(2026, 9, 23, 12, tzinfo=timezone.utc))

        assert re.search(r'bi-calendar-event" aria-hidden="true"></i>Sep 23, 2026<', self.get_home().content.decode())

    def test_empty_message_without_benchmarks(self):
        """
        Loads the home page without any published benchmarks.
        Expects the "No benchmarks yet." message in Popular and Recent.
        """
        assert self.get_home().content.decode().count("No benchmarks yet.") == 2

    def test_card_shows_tags(self):
        """
        Creates a published benchmark with the tag Computer Vision in the category Domain.
        Expects its card to show the tag, with the category as its hover text.
        """
        category = TagCategory.objects.create(name="Domain")
        tag = Tag.objects.create(name="Computer Vision", category=category)
        competition = make_benchmark(published=True)
        competition.tags.add(tag)

        content = self.get_home().content.decode()

        assert '<span class="bc-tag" title="Domain">Computer Vision</span>' in content

    def test_card_shows_no_tags_text(self):
        """
        Creates a published benchmark without tags.
        Expects its card to show No tags instead of a tag row.
        """
        make_benchmark(published=True)

        content = self.get_home().content.decode()

        assert '<span class="bc-tag-empty">No tags</span>' in content
        assert 'class="bc-tag-row"' not in content

    def test_card_sends_all_tags_sorted(self):
        """
        Creates a benchmark with 7 tags in the category Domain and 2 in the category Field,
        added out of order. Expects all 9 tags on its card, Domain first, then Field,
        and A to Z inside each category.
        """
        domain = TagCategory.objects.create(name="Domain")
        field = TagCategory.objects.create(name="Field")
        domain_tags = [Tag.objects.create(name=f"Domain {number}", category=domain) for number in range(7)]
        field_tags = [Tag.objects.create(name=f"Field {number}", category=field) for number in range(2)]
        competition = make_benchmark(published=True)
        # Out of order on purpose: Field before Domain, and Domain from 6 down to 0
        competition.tags.add(*field_tags, *reversed(domain_tags))

        context = self.get_home().context
        all_cards = context["featured_benchmarks"] + context["popular_benchmarks"] + context["recent_benchmarks"]
        card = next(card for card in all_cards if card["id"] == competition.id)
        tag_names = [tag["name"] for tag in card["tags"]]

        assert tag_names == [f"Domain {number}" for number in range(7)] + ["Field 0", "Field 1"]

    def test_card_organizer_photo_or_initial(self):
        """
        Creates one benchmark whose creator has a profile photo, and one whose creator has none.
        Expects the first card to show the photo in the avatar, and the second to show
        the first letter of the creator's name instead.
        """
        with_photo = UserFactory(display_name="Photo Owner")
        User.objects.filter(pk=with_photo.pk).update(photo="profile_photos/owner.png")
        make_benchmark(published=True, created_by=with_photo)
        make_benchmark(published=True, created_by=UserFactory(display_name="no photo"))

        content = self.get_home().content.decode()

        # Why no closing quote after .png: the storage adds a signature to the address, like ?AWSAccessKeyId=...
        assert re.search(r'class="bc-avatar">\s*<img src="[^"]*profile_photos/owner\.png', content)
        assert re.search(r'class="bc-avatar">\s*N\s*</span>', content)

    def test_home_page_loads_card_tags_script(self):
        """
        Loads the home page.
        Expects it to include card_tags.js, which fits the tags of each card on one line.
        """
        content = self.get_home().content.decode()

        assert 'src="/static/js/ours/card_tags.js"' in content
