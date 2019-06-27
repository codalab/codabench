from django.urls import reverse
from rest_framework.test import APITestCase

from factories import SubmissionFactory, UserFactory, CompetitionFactory

import datetime
import json
import pytz


class AnalyticsTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(username='user')
        self.admin = UserFactory(username='admin', super_user=True)
        self.day_range = 10
        self.first_day = datetime.datetime(2019, 1, 1, tzinfo=pytz.UTC)

    def create_datetime_with_days_offset(self, offset):
        return self.first_day + datetime.timedelta(days=offset)

    def date_range_tester(self, factory, date_field_name, count_field_name, **kwargs):
        object_quantity = self.day_range
        self.test_objects = []

        for i in range(object_quantity):
            datefield = {
                date_field_name: self.create_datetime_with_days_offset(i),
            }
            self.test_objects.append(factory(**kwargs, **datefield))

        query_params = [
            self.create_datetime_with_days_offset(1).isoformat()[0:10],
            self.create_datetime_with_days_offset(self.day_range - 2).isoformat()[0:10],
            'day',
        ]
        query = '?start_date={}&end_date={}&time_unit={}'.format(*query_params)
        self.client.login(username='admin', password='test')
        resp = self.client.get(reverse('analytics_api') + query)
        print(json.loads(resp.content.decode('utf-8')))
        return json.loads(resp.content.decode('utf-8'))[count_field_name]

    def test_date_range_is_inclusive_of_bounds(self):
        number_of_users_created = self.date_range_tester(UserFactory, 'date_joined', 'registered_user_count')
        assert number_of_users_created == self.day_range - 2
        number_of_competitions_created = self.date_range_tester(CompetitionFactory, 'created_when', 'competition_count')
        assert number_of_competitions_created == self.day_range - 2
        number_of_submissions_created = self.date_range_tester(SubmissionFactory, 'created_when', 'submissions_made_count')
        assert number_of_submissions_created == self.day_range - 2

    def test_super_user_can_view_analytics(self):
        self.client.login(username='admin', password='test')
        resp = self.client.get(reverse('analytics:analytics'))
        assert resp.status_code == 200

    def test_normal_user_cannot_view_analytics(self):
        self.client.login(username='user', password='test')
        resp = self.client.get(reverse('analytics:analytics'))
        assert resp.status_code == 403
