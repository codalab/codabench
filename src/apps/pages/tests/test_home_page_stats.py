import json
import os
import re
import tempfile
from unittest import mock

from django.test import TestCase
from django.urls import reverse


class HomePageStatsTests(TestCase):

    def get_stat_values(self, counters):
        """Write the counters to a temporary file, load the home page and return the shown values."""
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as counters_file:
            json.dump(counters, counters_file)
        self.addCleanup(os.remove, counters_file.name)

        with mock.patch('utils.context_processors.HOME_PAGE_COUNTERS_FILE_PATH', counters_file.name):
            content = self.client.get(reverse('pages:home')).content.decode()

        return re.findall(r'class="home-stat-value">([^<]+)<', content)

    def test_shows_counters_with_separators(self):
        """
        Uses counters for all 5 stats.
        Expects them in order (benchmarks, users, organizers, participants, submissions)
        with thousands separators.
        """
        values = self.get_stat_values({
            "public_competitions": 1204,
            "users": 48213,
            "organizers": 2875,
            "participants": 31560,
            "submissions": 1532870,
        })

        assert values == ["1,204", "48,213", "2,875", "31,560", "1,532,870"]

    def test_missing_counters_show_zero(self):
        """
        Uses an old counters file without organizers and participants.
        Expects those two stats to show 0.
        """
        values = self.get_stat_values({"public_competitions": 3, "users": 10, "submissions": 25})

        assert values == ["3", "10", "0", "0", "25"]

    def test_unreadable_file_shows_zero(self):
        """
        Points the counters file to a path that does not exist.
        Expects all 5 stats to show 0.
        """
        with mock.patch('utils.context_processors.HOME_PAGE_COUNTERS_FILE_PATH', '/does/not/exist.json'):
            content = self.client.get(reverse('pages:home')).content.decode()

        assert re.findall(r'class="home-stat-value">([^<]+)<', content) == ["0"] * 5

    def test_section_has_title_and_labels(self):
        """
        Loads the home page.
        Expects the "Codabench in Numbers" title and the 5 labels.
        """
        content = self.client.get(reverse('pages:home')).content.decode()

        assert "Codabench in Numbers" in content
        for label in ["Public Benchmarks", "Platform Users", "Organizers", "Participants", "Submissions"]:
            assert f'class="home-stat-label">{label}<' in content
