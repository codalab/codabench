from django.urls import reverse
from rest_framework.test import APITestCase

import datetime
import pytz
from random import randint


from factories import SubmissionFactory, UserFactory, CompetitionFactory, PhaseFactory, TaskFactory
from competitions.models import Competition


class AnalyticsTests(APITestCase):
    def setUp(self):
        self.first_day = datetime.datetime(2019, 1, 1, tzinfo=pytz.UTC)
        self.year_before_first_day = self.first_day - datetime.timedelta(days=-356)
        self.user = UserFactory(
            username='user',
            date_joined=self.year_before_first_day
        )
        self.admin = UserFactory(
            username='admin',
            super_user=True,
            date_joined=self.year_before_first_day
        )
        self.day_range = 10
        self.object_data = [
            {
                'factory': UserFactory,
                'datefield_name': 'date_joined',
                'countfield_name': 'registered_user_count',
            }, {
                'factory': CompetitionFactory,
                'datefield_name': 'created_when',
                'countfield_name': 'competition_count',
            }, {
                'factory': SubmissionFactory,
                'datefield_name': 'created_when',
                'countfield_name': 'submissions_made_count',
            }
        ]
        self.dummy_objects = []
        self.create_dummy_objects()

    def create_dummy_objects(self):
        for object_category in self.object_data:
            self.create_objects_in_category(**object_category)

    def create_objects_in_category(self, factory, datefield_name, countfield_name=None, **kwargs):
        for i in range(self.day_range):
            datefield = {
                datefield_name: self.create_datetime_with_days_offset(i),
            }
            if factory == CompetitionFactory:
                kwargs['created_by'] = self.user
            if factory == SubmissionFactory:
                kwargs['phase'] = PhaseFactory(
                    competition=Competition.objects.first(),
                    tasks=[TaskFactory(created_by=self.user)]
                )
                kwargs['owner'] = self.user
            self.dummy_objects.append(factory(**kwargs, **datefield))

    def create_datetime_with_days_offset(self, offset):
        return self.first_day + datetime.timedelta(days=offset)

    def date_range_tester(self, countfield_name):
        query_span = randint(0, self.day_range - 1)

        query_params = [
            self.create_datetime_with_days_offset(1).date().isoformat(),
            self.create_datetime_with_days_offset(query_span).date().isoformat(),
            'day',
        ]
        query = '?start_date={}&end_date={}&time_unit={}'.format(*query_params)
        self.client.login(username='admin', password='test')
        resp = self.client.get(reverse('analytics_api') + query)
        number_of_objects_in_range = resp.json()[countfield_name]

        assert number_of_objects_in_range == query_span

    def test_date_range_is_inclusive_of_bounds(self):
        for category in self.object_data:
            self.date_range_tester(category['countfield_name'])

    def test_super_user_can_view_analytics(self):
        self.client.login(username='admin', password='test')
        resp = self.client.get(reverse('analytics:analytics'))
        assert resp.status_code == 200

    def test_normal_user_cannot_view_analytics(self):
        self.client.login(username='user', password='test')
        resp = self.client.get(reverse('analytics:analytics'))
        assert resp.status_code == 403
