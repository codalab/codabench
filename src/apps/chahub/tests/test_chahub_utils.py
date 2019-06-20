from unittest import mock

from django.conf import settings
from django.http.response import HttpResponseBase
from django.test import TestCase

from factories import UserFactory, CompetitionParticipantFactory, CompetitionFactory, PhaseFactory


class ChaHubUtilityTests(TestCase):
    def setUp(self):
        settings.PYTEST_FORCE_CHAHUB = True
        # set the url to localhost for tests
        settings.CHAHUB_API_URL = 'localhost/'
        self.user = UserFactory.build(username='norm')

    def tearDown(self):
        settings.PYTEST_FORCE_CHAHUB = False
        settings.CHAHUB_API_URL = None

    def mock_chahub_save(self, obj):
        with mock.patch('apps.chahub.utils.requests.post') as requests_post_mock:
            requests_post_mock.return_value = HttpResponseBase(status=201)
            requests_post_mock.return_value.content = ''
            with mock.patch('apps.chahub.utils.requests.put') as requests_put_mock:
                requests_put_mock.return_value = HttpResponseBase(status=201)
                requests_put_mock.return_value.content = ''
                obj.save()
            return requests_post_mock, requests_put_mock

    def test_send_to_chahub_posts_new_data_and_puts_updated_data(self):
        post_resp, put_response = self.mock_chahub_save(self.user)
        assert post_resp.called
        assert not put_response.called
        self.user.username = 'test'
        post_resp, put_response = self.mock_chahub_save(self.user)
        assert not post_resp.called
        assert put_response.called
