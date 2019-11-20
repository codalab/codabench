from chahub.tests.utils import ChaHubTestCase
from factories import UserFactory, CompetitionFactory, DataFactory, SubmissionFactory, PhaseFactory, \
    CompetitionParticipantFactory


class ChaHubDoRetriesTests(ChaHubTestCase):
    def setUp(self):
        for _ in range(5):
            user = UserFactory(chahub_needs_retry=True)
            comp = CompetitionFactory(chahub_needs_retry=True, published=True)
            participant = CompetitionParticipantFactory(competition=comp, user=user, status='approved')
            phase = PhaseFactory(competition=comp)
            DataFactory(chahub_needs_retry=True, is_public=True, upload_completed_successfully=True)
            SubmissionFactory(
                chahub_needs_retry=True,
                status="Finished",
                phase=phase,
                is_public=True,
                participant=participant
            )
        super().setUp()

    def test_do_retries_picks_up_all_expected_items(self):
        resp = self.mock_retries()
        # Should call once each for Users, Comps, Datasets, Submissions
        assert resp.call_count == 4
        for call in resp.call_args_list:
            # Should get passed a batch of data that is 5 long
            assert len(call[1]['data']) == 5

    def test_do_retries_limit_will_limit_number_of_retries(self):
        resp = self.mock_retries(limit=2)
        # Should call once each for Users, Comps, Datasets, Submissions
        assert resp.call_count == 4
        for call in resp.call_args_list:
            # Should get passed a batch of data that is 2 long, matching the limit
            assert len(call[1]['data']) == 2
