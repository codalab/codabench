from chahub.tests.utils import ChaHubTestCase
from competitions.models import Submission
from factories import UserFactory, CompetitionFactory, DataFactory, SubmissionFactory, PhaseFactory, \
    CompetitionParticipantFactory
from profiles.models import User


class SubmissionMixinTests(ChaHubTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.comp = CompetitionFactory(published=True)
        self.participant = CompetitionParticipantFactory(user=self.user, competition=self.comp)
        self.phase = PhaseFactory(competition=self.comp)
        self.data = DataFactory()
        # Calling this after initial setup so we don't turn on FORCE_CHAHUB and try and send all our setup objects
        super().setUp()
        self.submission = SubmissionFactory.build(
            owner=self.user,
            phase=self.phase,
            data=self.data,
            participant=self.participant,
            status='Finished',
            is_public=True,
            leaderboard=None
        )

    def test_submission_save_sends_to_chahub(self):
        resp = self.mock_chahub_save(self.submission)
        assert resp.called

    def test_submission_save_not_sending_duplicate_data(self):
        resp1 = self.mock_chahub_save(self.submission)
        assert resp1.called
        self.submission = Submission.objects.get(id=self.submission.id)
        resp2 = self.mock_chahub_save(self.submission)
        assert not resp2.called

    def test_submission_save_sends_updated_data(self):
        resp1 = self.mock_chahub_save(self.submission)
        assert resp1.called
        self.phase.index += 1
        resp2 = self.mock_chahub_save(self.submission)
        assert resp2.called

    def test_invalid_submission_not_sent(self):
        self.submission.status = "Running"
        self.submission.is_public = False
        resp1 = self.mock_chahub_save(self.submission)
        assert not resp1.called
        self.submission = Submission.objects.get(id=self.submission.id)
        self.submission.status = "Finished"
        resp2 = self.mock_chahub_save(self.submission)
        assert resp2.called

    def test_retrying_invalid_submission_wont_retry_again(self):
        self.submission.status = "Running"
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
        self.user = User.objects.get(id=self.user.id)
        self.user.password = 'this_is_different'  # Not using user.set_password() to control when the save happens
        resp2 = self.mock_chahub_save(self.user)
        assert not resp2.called


class CompetitionMixinTests(ChaHubTestCase):
    def setUp(self):
        self.comp = CompetitionFactory(published=False)
        PhaseFactory(competition=self.comp)
        super().setUp()

    def test_unpublished_comp_doesnt_send_private_data(self):
        resp = self.mock_chahub_save(self.comp)
        # Gross traversal through call args to get the data passed to _send
        assert resp.called
        data = resp.call_args[0][1][0]
        whitelist = self.comp.get_whitelist()
        for key, value in data.items():
            if key not in whitelist:
                assert value is None
