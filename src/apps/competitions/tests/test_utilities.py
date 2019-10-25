import pytz

from datetime import date, datetime
from unittest import TestCase

from competitions.unpackers.utils import get_datetime


class GetDatetimeTests(TestCase):
    def test_get_datetime_turns_date_into_datetime(self):
        some_date = date(2019, 5, 29)  # Welcome to this world lil Tyrone :)
        new_date = get_datetime(some_date)
        assert isinstance(new_date, datetime)
        assert new_date == datetime(2019, 5, 29, 0, 0, tzinfo=pytz.timezone('UTC'))

    def test_get_datetime_turns_misc_data_into_datetime(self):
        some_date = "2019-5-29"
        new_date = get_datetime(some_date)
        assert isinstance(new_date, datetime)
        assert new_date == datetime(2019, 5, 29, 0, 0, tzinfo=pytz.timezone('UTC'))

        some_date = "5/29/2019"
        new_date = get_datetime(some_date)
        assert isinstance(new_date, datetime)
        assert new_date == datetime(2019, 5, 29, 0, 0, tzinfo=pytz.timezone('UTC'))

        some_date = "2019-5-29 1:45PM"
        new_date = get_datetime(some_date)
        assert isinstance(new_date, datetime)
        assert new_date == datetime(2019, 5, 29, 13, 45, tzinfo=pytz.timezone('UTC'))

        some_date = "5/29/2019 1:45PM"
        new_date = get_datetime(some_date)
        assert isinstance(new_date, datetime)
        assert new_date == datetime(2019, 5, 29, 13, 45, tzinfo=pytz.timezone('UTC'))

    def test_get_datetime_adds_timezone_to_datetime(self):
        some_date = datetime(2019, 5, 29, 0, 0)
        new_date = get_datetime(some_date)
        assert isinstance(new_date, datetime)
        assert new_date == datetime(2019, 5, 29, 0, 0, tzinfo=pytz.timezone('UTC'))

    def test_get_datetime_keeps_timezone_if_exists(self):
        some_date = datetime(2019, 5, 29, 0, 0, tzinfo=pytz.timezone('GMT'))
        new_date = get_datetime(some_date)
        assert isinstance(new_date, datetime)
        assert new_date == datetime(2019, 5, 29, 0, 0, tzinfo=pytz.timezone('GMT'))
