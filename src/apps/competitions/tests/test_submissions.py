from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from competitions.models import Competition, Phase, Submission
from datasets.models import Data
from django.utils.timezone import now

User = get_user_model()


class SubmissionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='tester'
        )
        self.user.set_password('testing')
        self.user.save()
        self.competition = Competition.objects.create(
            title='Test Competition',
            created_by=self.user,
        )
        self.phase = Phase.objects.create(
            competition=self.competition,
            index=0,
            start=now(),
            name='Test Phase',
        )

    def make_submission(self, user=None, phase=None, data=None, submission_status=None, submission_date=None, submission_name=None):
        user = self.user if user is None else user
        phase = self.phase if phase is None else phase
        submission_date = now() if submission_date is None else submission_date

        data = data if data is not None else Data.objects.create(
            created_by=user,
            created_when=submission_date,
            type='submission',
            name=f'submission @ {submission_date.strftime("%m-%d-%Y %H:%M")}'
        )

        submission = Submission.objects.create(
            owner=user,
            phase=phase,
            data=data,
            created_when=submission_date,
            name=submission_name,
        )
        if submission_status:
            submission.status = submission_status
            submission.save()

        if submission_date:
            submission.created_when = submission_date
            submission.save()

        return submission

    def set_max_submissions(self, phase=None, per_person=None, per_day=None):
        phase = self.phase if phase is None else phase
        phase.has_max_submissions = True
        phase.max_submissions_per_person = per_person
        phase.max_submissions_per_day = per_day
        phase.save()

    def test_creating_submission_checks_max_submission_per_day_not_exceeded(self):
        self.set_max_submissions(per_day=1)
        self.make_submission()
        try:
            self.make_submission()
            assert False, "This should have raised a PermissionError"
        except PermissionError:
            pass

    def test_creating_submission_checks_max_submission_per_person_not_exceeded(self):
        self.set_max_submissions(per_person=1)
        self.make_submission()
        try:
            self.make_submission()
            assert False, "This should have raised a PermissionError"
        except PermissionError:
            pass

    def test_failed_submissions_not_counted_towards_max(self):
        self.set_max_submissions(per_person=1, per_day=1)
        self.make_submission(submission_status="Failed")
        try:
            self.make_submission()
        except PermissionError:
            assert False, "This counted failed submissions"

    def test_max_per_day_not_counting_previous_days_submissions(self):
        self.set_max_submissions(per_day=1)
        yesterday = now() - timedelta(days=1)
        self.make_submission(submission_date=yesterday)
        try:
            self.make_submission()
        except PermissionError:
            assert False, "This counted yesterday's submissions"

    def test_max_submissions_not_counting_other_user_submissions(self):
        self.set_max_submissions(per_person=1, per_day=1)
        other_user = User.objects.create(username='test2')
        self.make_submission(user=other_user)
        try:
            self.make_submission()
        except PermissionError:
            assert False, "This counted other user's submissions"

    def test_submission_not_created_if_max_reached(self):
        self.set_max_submissions(per_person=1)
        self.make_submission()
        try:
            self.make_submission(submission_name='Find Me')
        except PermissionError:
            try:
                Submission.objects.get(name='Find Me')
                assert False, "Submission should not have been created"
            except Submission.DoesNotExist:
                pass
