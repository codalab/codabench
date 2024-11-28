from django.test import TestCase
from competitions.models import Submission, CompetitionParticipant
from factories import UserFactory, CompetitionFactory, PhaseFactory, CompetitionParticipantFactory, SubmissionFactory


class CompetitionSubmissionsParticipantsCountsTests(TestCase):
    def setUp(self):

        # User
        self.creator = UserFactory(username='creator', password='creator')
        # Competition
        self.competition = CompetitionFactory(created_by=self.creator)
        # Phase
        self.phase = PhaseFactory(competition=self.competition)

        # Create a submission for the delete test
        self.submission = SubmissionFactory(phase=self.phase, owner=self.creator, status=CompetitionParticipant.APPROVED)
        self.competition.refresh_from_db()

    def test_adding_submission_updates_submission_count(self):
        initial_count = self.competition.submissions_count

        self.assertEqual(initial_count, 1)  # one submission created in the setup

        # Add a new submission
        _ = SubmissionFactory(phase=self.phase, owner=self.creator, status=Submission.SUBMITTED)
        self.competition.refresh_from_db()

        # Assert that the count increased by 1
        self.assertEqual(self.competition.submissions_count, initial_count + 1)

    def test_deleting_submission_updates_submission_count(self):
        initial_count = self.competition.submissions_count

        self.assertEqual(initial_count, 1)  # one submission created in the setup

        # Delete the existing submission
        self.submission.delete()
        self.competition.refresh_from_db()

        # Assert that the count decreased by 1
        self.assertEqual(self.competition.submissions_count, initial_count - 1)

    def test_adding_participant_updates_participants_count(self):
        initial_count = self.competition.participants_count

        self.assertEqual(initial_count, 1)  # default count is 1

        # Add a new approved participant
        new_participant = UserFactory(username='new_participant', password='test')
        CompetitionParticipantFactory(user=new_participant, competition=self.competition, status=CompetitionParticipant.APPROVED)
        self.competition.refresh_from_db()

        # Assert that the count increased by 1
        self.assertEqual(self.competition.participants_count, initial_count + 1)
