# Todo: Implement ChahubSaveMixin on Submissions
# Todo: Finish fixing tests
from unittest import mock
from django.conf import settings
from django.http.response import HttpResponseBase
from django.test import TestCase
from factories import UserFactory, CompetitionFactory, DataFactory, SubmissionFactory, PhaseFactory, \
    CompetitionParticipantFactory


class ChaHubTestCase(TestCase):
    def setUp(self):
        settings.PYTEST_FORCE_CHAHUB = True

    def tearDown(self):
        settings.PYTEST_FORCE_CHAHUB = False

    def mock_chahub_save(self, obj):
        with mock.patch('chahub.models.send_to_chahub') as chahub_mock:
            chahub_mock.return_value = HttpResponseBase(status=201)
            chahub_mock.return_value.content = ''
            obj.save()
            return chahub_mock


class ProfileMixinTests(ChaHubTestCase):
    def setUp(self):
        self.user = UserFactory.build(username='admin')  # create a user but don't save until later in the mock
        super().setUp()

    def test_profile_save_sends_to_chahub(self):
        resp = self.mock_chahub_save(self.user)
        assert resp.called

    def test_profile_save_not_sending_duplicate_data(self):
        resp1 = self.mock_chahub_save(self.user)
        assert resp1.called
        resp2 = self.mock_chahub_save(self.user)
        assert not resp2.called

    def test_profile_save_sends_updated_data(self):
        resp1 = self.mock_chahub_save(self.user)
        assert resp1.called
        self.user.username = 'abbie'
        resp2 = self.mock_chahub_save(self.user)
        assert resp2.called

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

    def test_competition_save_sends_to_chahub(self):
        resp = self.mock_chahub_save(self.comp)
        assert resp.called

    def test_competition_save_not_sending_duplicate_data(self):
        resp1 = self.mock_chahub_save(self.comp)
        assert resp1.called
        resp2 = self.mock_chahub_save(self.comp)
        assert not resp2.called

    def test_competition_save_sends_updated_data(self):
        resp1 = self.mock_chahub_save(self.comp)
        assert resp1.called
        self.comp.title = 'A Fresh New Competition Title'
        resp2 = self.mock_chahub_save(self.comp)
        assert resp2.called

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

    def test_dataset_save_sends_to_chahub(self):
        resp = self.mock_chahub_save(self.data)
        assert resp.called

    def test_dataset_save_not_sending_duplicate_data(self):
        resp1 = self.mock_chahub_save(self.data)
        assert resp1.called
        resp2 = self.mock_chahub_save(self.data)
        assert not resp2.called

    def test_dataset_save_sends_updated_data(self):
        self.data.name = 'Such great name'
        resp1 = self.mock_chahub_save(self.data)
        assert resp1.called
        self.data.name = 'An even better name'
        resp2 = self.mock_chahub_save(self.data)
        assert resp2.called

    def test_invalid_dataset_not_sent(self):
        self.data.is_public = False
        resp1 = self.mock_chahub_save(self.data)
        assert not resp1.called
        self.data.is_public = True
        resp2 = self.mock_chahub_save(self.data)
        assert resp2.called


class SubmissionMixinTests(ChaHubTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.comp = CompetitionFactory()
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

    def test_not_public_submission_not_sent(self):
        self.submission.is_public = False
        resp1 = self.mock_chahub_save(self.submission)
        assert not resp1.called
        self.submission.is_public = True
        resp2 = self.mock_chahub_save(self.submission)
        assert resp2.called

    def test_unfinished_submission_not_sent(self):
        self.submission.status = "Running"
        resp1 = self.mock_chahub_save(self.submission)
        assert not resp1.called
        self.submission.status = "Finished"
        resp2 = self.mock_chahub_save(self.submission)
        assert resp2.called


    # def test_submission_invalid_not_marked_for_retry_again(self):
    #     # Make submission invalid
    #     self.competition.published = False
    #     self.competition.save()
    #
    #     # Mark submission for retry
    #     submission = CompetitionSubmission(phase=self.phase, participant=self.participant, chahub_needs_retry=True)
    #     # with mock.patch('apps.chahub.models.send_to_chahub') as send_to_chahub_mock:
    #     with mock.patch('chahub.utils.send_to_chahub') as send_to_chahub_mock:
    #         submission.save()
    #         assert not send_to_chahub_mock.called
    #
    # def test_submission_valid_not_retried_again(self):
    #     # Mark submission for retry
    #     submission = CompetitionSubmission(phase=self.phase, participant=self.participant, chahub_needs_retry=True)
    #     # with mock.patch('apps.chahub.models.send_to_chahub') as send_to_chahub_mock:
    #     with mock.patch('chahub.utils.send_to_chahub') as send_to_chahub_mock:
    #         send_to_chahub_mock.return_value = HttpResponseBase(status=201)
    #         send_to_chahub_mock.return_value.content = ""
    #         submission.save()  # NOTE! not called with force_to_chahub=True as retrying would set
    #         # It does not call send method, only during "do_retries" task should it
    #         assert not send_to_chahub_mock.called
    #
    # def test_submission_retry_valid_retried_then_sent_and_not_retried_again(self):
    #     # Mark submission for retry
    #     submission = CompetitionSubmission(phase=self.phase, participant=self.participant, chahub_needs_retry=True)
    #     # with mock.patch('apps.chahub.models.send_to_chahub') as send_to_chahub_mock:
    #     with mock.patch('chahub.utils.send_to_chahub') as send_to_chahub_mock:
    #         send_to_chahub_mock.return_value = HttpResponseBase(status=201)
    #         send_to_chahub_mock.return_value.content = ""
    #         submission.save(force_to_chahub=True)
    #         # It does not need retry any more, and was successful
    #         assert send_to_chahub_mock.called
    #         assert not CompetitionSubmission.objects.get(pk=submission.pk).chahub_needs_retry
    #
    #         # reset
    #         send_to_chahub_mock.called = False
    #
    #         # Try sending again
    #         submission.save(force_to_chahub=True)
    #         assert not send_to_chahub_mock.called
