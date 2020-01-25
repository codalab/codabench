from unittest import mock

from django.conf import settings
from django.http.response import HttpResponseBase
from django.test import TestCase

from chahub.tasks import do_chahub_retries


class ChaHubTestResponse(HttpResponseBase):
    @property
    def ok(self):
        return self.status_code < 400


class ChaHubTestCase(TestCase):
    def setUp(self):
        settings.PYTEST_FORCE_CHAHUB = True
        # set the url to localhost for tests
        settings.CHAHUB_API_URL = 'http://localhost/'
        settings.CHAHUB_API_KEY = 'asdf'

    def tearDown(self):
        settings.PYTEST_FORCE_CHAHUB = False
        settings.CHAHUB_API_URL = None

    def mock_chahub_save(self, obj):
        with mock.patch('chahub.tasks._send') as chahub_mock:
            chahub_mock.return_value = ChaHubTestResponse(status=201)
            chahub_mock.return_value.content = ''
            obj.save()
            return chahub_mock

    def mock_retries(self, limit=None):
        with mock.patch('apps.chahub.tasks.requests.get') as chahub_get_mock:
            # This checks that ChaHub is up, mock this so the task doesn't bail
            chahub_get_mock.return_value = ChaHubTestResponse(status=200)
            with mock.patch('chahub.tasks._send') as send_to_chahub_mock:
                send_to_chahub_mock.return_value = ChaHubTestResponse(status=201)
                send_to_chahub_mock.return_value.content = ''
                do_chahub_retries(limit=limit)
                return send_to_chahub_mock
