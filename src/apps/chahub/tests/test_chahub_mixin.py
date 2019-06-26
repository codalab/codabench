from unittest import mock
from django.conf import settings
from django.http.response import HttpResponseBase
from django.test import TestCase

from competitions.models import Submission
from factories import UserFactory, CompetitionFactory, DataFactory, SubmissionFactory, PhaseFactory, \
    CompetitionParticipantFactory


class ChaHubTestCase(TestCase):
    def setUp(self):
        settings.PYTEST_FORCE_CHAHUB = True
        # set the url to localhost for tests
        settings.CHAHUB_API_URL = 'localhost/'

    def tearDown(self):
        settings.PYTEST_FORCE_CHAHUB = False
        settings.CHAHUB_API_URL = None

    def mock_chahub_save(self, obj):
        with mock.patch('chahub.models.send_to_chahub') as chahub_mock:
            chahub_mock.return_value = HttpResponseBase(status=201)
            chahub_mock.return_value.content = ''
            obj.save()
            return chahub_mock


class SubmissionMixinTests(ChaHubTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.comp = CompetitionFactory(published=True)
        self.participant = CompetitionParticipantFactory(user=self.user, competition=self.comp)
        self.phase = PhaseFactory(competition=self.comp)
        self.data = DataFactory()
        super().setUp()
        self.submission = SubmissionFactory.build(
            owner=self.user,
            phase=self.phase,
            data=self.data,
            participant=self.participant,
            status='Finished',
            is_public=True,
        )

    def test_submission_save_sends_to_chahub(self):
        resp = self.mock_chahub_save(self.submission)
        assert resp.called

    def test_submission_save_not_sending_duplicate_data(self):
        resp1 = self.mock_chahub_save(self.submission)
        assert resp1.called
        resp2 = self.mock_chahub_save(self.submission)
        assert not resp2.called

    def test_submission_save_sends_updated_data(self):
        resp1 = self.mock_chahub_save(self.submission)
        assert resp1.called
        self.phase.index += 1
        resp2 = self.mock_chahub_save(self.submission)
        assert resp2.called
        assert resp1.call_args[0][1]['phase_index'] == resp2.call_args[0][1]['phase_index'] - 1  # updated data actually sent

    def test_invalid_submission_not_sent(self):
        self.comp.published = False
        self.comp.save()
        self.submission.status = "Running"
        self.submission.is_public = False
        resp1 = self.mock_chahub_save(self.submission)
        assert not resp1.called
        self.submission.status = "Finished"
        resp2 = self.mock_chahub_save(self.submission)
        assert not resp2.called
        self.comp.published = True
        self.mock_chahub_save(self.comp)  # Inside mock so test doesn't get angry about invalid endpoints
        resp3 = self.mock_chahub_save(self.submission)
        assert not resp3.called
        self.submission.is_public = True
        resp4 = self.mock_chahub_save(self.submission)
        assert resp4.called

    def test_retrying_invalid_submission_wont_retry_again(self):
        self.submission.is_public = False
        self.submission.chahub_needs_retry = True
        resp = self.mock_chahub_save(self.submission)
        assert not resp.called
        assert not Submission.objects.get(id=self.submission.id).chahub_needs_retry

    def test_valid_submission_marked_for_retry_sent_and_needs_retry_unset(self):
        # Mark submission for retry
        self.submission.chahub_needs_retry = True
        resp = self.mock_chahub_save(self.submission)
        assert resp.called
        assert not Submission.objects.get(id=self.submission.id).chahub_needs_retry


class ProfileMixinTests(ChaHubTestCase):
    def setUp(self):
        self.user = UserFactory.build(username='admin')  # create a user but don't save until later in the mock
        super().setUp()

    def test_profile_save_not_sending_on_blacklisted_data_update(self):
        resp1 = self.mock_chahub_save(self.user)
        assert resp1.called
        self.user.password = 'this_is_different'  # Not using user.set_password() to control when the save happens
        resp2 = self.mock_chahub_save(self.user)
        assert not resp2.called


class CompetitionMixinTests(ChaHubTestCase):
    def setUp(self):
        self.user = UserFactory(username='admin', password='test')
        self.comp = CompetitionFactory.build(created_by=self.user, published=True, title='competition 1')
        super().setUp()

    def test_invalid_competition_not_sent(self):
        self.comp.published = False  # not valid to send to Chahub
        resp1 = self.mock_chahub_save(self.comp)
        assert not resp1.called
        self.comp.published = True  # make it valid
        resp2 = self.mock_chahub_save(self.comp)
        assert resp2.called


class DatasetMixinTests(ChaHubTestCase):
    def setUp(self):
        self.user = UserFactory()
        super().setUp()
        self.data = DataFactory.build(created_by=self.user, is_public=True)

    def test_invalid_dataset_not_sent(self):
        self.data.is_public = False
        resp1 = self.mock_chahub_save(self.data)
        assert not resp1.called
        self.data.is_public = True
        resp2 = self.mock_chahub_save(self.data)
        assert resp2.called
