import os

from django.test import TestCase

import competitions.tests.unpacker_test_data as test_data
from competitions.unpackers.codabench_v1 import CodabenchV1Unpacker
from factories import UserFactory
from ..models import Competition


class CodabenchV1UnpackerTests(TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.base_dir, 'files')
        self.user = UserFactory()
        self.unpacker = CodabenchV1Unpacker(
            competition_yaml=test_data.codabench_v1_yaml_data,
            temp_directory=self.temp_dir,
            creator=self.user,
        )

    def test_task_unpacking(self):
        tasks = test_data.get_tasks(self.user.id)
        self.unpacker._unpack_tasks()
        assert self.unpacker.competition['tasks'] == tasks

    # could not mock up start date here, because every time we call _set_default_phase(), it will set datetime.now()
    # for each default phase, so "==" will never be equals.
    # def test_phase_unpacking(self):
    #     self.unpacker._set_default_phase()
    #     assert self.unpacker.competition['phases'] == test_data.get_phases('codabench/v1')

    def test_terms_unpacking(self):
        self.unpacker._unpack_terms()
        assert self.unpacker.competition['terms'] == test_data.TERMS

    def test_page_unpacking(self):
        self.unpacker._unpack_pages()
        assert self.unpacker.competition['pages'] == test_data.PAGES

    def test_leaderboard_unpacking(self):
        self.unpacker._unpack_leaderboard()
        assert self.unpacker.competition['leaderboards'] == test_data.LEADERBOARDS

    def test_set_competition_type(self):
        self.unpacker._set_competition_type()
        assert  self.unpacker.competition['competition_type'] == Competition.BENCHMARK
