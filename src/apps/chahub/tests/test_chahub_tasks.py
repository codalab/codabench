from unittest import mock
from django.conf import settings
from django.http.response import HttpResponseBase
from django.test import TestCase

from chahub.tasks import do_chahub_retries
from factories import UserFactory, CompetitionFactory, DataFactory, SubmissionFactory, PhaseFactory, \
    CompetitionParticipantFactory


class ChaHubDoRetriesTests(TestCase):
    def setUp(self):
        for _ in range(5):
            user = UserFactory(chahub_needs_retry=True)
            comp = CompetitionFactory(chahub_needs_retry=True, published=True)
            participant = CompetitionParticipantFactory(competition=comp, user=user, status='approved')
            phase = PhaseFactory(competition=comp)
            DataFactory(chahub_needs_retry=True, is_public=True)
            SubmissionFactory(
                chahub_needs_retry=True,
                status="Finished",
                phase=phase,
                is_public=True,
                participant=participant
            )
        settings.PYTEST_FORCE_CHAHUB = True
        # set the url to localhost for tests
        settings.CHAHUB_API_URL = 'localhost/'

    def tearDown(self):
        settings.PYTEST_FORCE_CHAHUB = False
        settings.CHAHUB_API_URL = None

    def test_do_retries_picks_up_all_expected_items(self):
        with mock.patch('apps.chahub.tasks.requests.get') as chahub_get_mock:
            # This checks that ChaHub is up, mock this so the task doesn't bail
            chahub_get_mock.return_value = HttpResponseBase(status=200)
            with mock.patch('chahub.models.send_to_chahub') as send_to_chahub_mock:
                send_to_chahub_mock.return_value = HttpResponseBase(status=201)
                send_to_chahub_mock.return_value.content = ''
                do_chahub_retries()
                # Should grab 5 each Users, Comps, Datasets, Submissions
                assert send_to_chahub_mock.call_count == 20

    def test_do_retries_limit_will_limit_number_of_retries(self):
        with mock.patch('apps.chahub.tasks.requests.get') as chahub_get_mock:
            # This checks that ChaHub is up, mock this so the task doesn't bail
            chahub_get_mock.return_value = HttpResponseBase(status=200)
            with mock.patch('chahub.models.send_to_chahub') as send_to_chahub_mock:
                send_to_chahub_mock.return_value = HttpResponseBase(status=201)
                send_to_chahub_mock.return_value.content = ''
                do_chahub_retries(limit=2)
                # Should grab 2 each Users, Comps, Datasets, Submissions
                assert send_to_chahub_mock.call_count == 8
