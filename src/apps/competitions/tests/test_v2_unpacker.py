import os

from django.test import TestCase

import competitions.tests.unpacker_test_data as test_data
from competitions.unpackers.v2 import V2Unpacker
from factories import UserFactory


class V2UnpackerTests(TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.base_dir, 'files')
        self.user = UserFactory()
        self.unpacker = V2Unpacker(
            competition_yaml=test_data.v2_yaml_data,
            temp_directory=self.temp_dir,
            creator=self.user,
        )

    def test_task_unpacking(self):
        tasks = test_data.get_tasks(self.user.id)
        self.unpacker._unpack_tasks()
        assert self.unpacker.competition['tasks'] == tasks

    def test_phase_unpacking(self):
        self.unpacker._unpack_phases()
        assert self.unpacker.competition['phases'] == test_data.get_phases(2)

    def test_terms_unpacking(self):
        self.unpacker._unpack_terms()
        assert self.unpacker.competition['terms'] == test_data.TERMS

    def test_page_unpacking(self):
        self.unpacker._unpack_pages()
        assert self.unpacker.competition['pages'] == test_data.PAGES

    def test_leaderboard_unpacking(self):
        self.unpacker._unpack_leaderboards()
        assert self.unpacker.competition['leaderboards'] == test_data.V2_LEADERBOARDS

    def test_competition_type_if_not_set(self):
        assert self.unpacker.competition['competition_type'] == 'competition'
