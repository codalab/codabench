import random

import factory
from django.core.files.base import ContentFile
from django.utils.timezone import now
from factory import post_generation
from factory.django import DjangoModelFactory
from pytz import UTC

from competitions.models import Competition, Phase, Submission, CompetitionParticipant, PhaseTaskInstance
from datasets.models import Data
from leaderboards.models import Leaderboard, Column, SubmissionScore
from profiles.models import User, Organization
from tasks.models import Task, Solution
from queues.models import Queue


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)
        exclude = (
            '_username',
            '_i',
        )

    _username = factory.Faker('user_name')
    _i = factory.Sequence(lambda n: n)
    username = factory.LazyAttribute(lambda o: f"{o._username}-{o._i}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = "test"

    date_joined = factory.Faker('date_time_between', start_date='-5y', end_date='now', tzinfo=UTC)

    # Set Notifications to False
    organizer_direct_message_updates = False
    allow_forum_notifications = False
    allow_organization_invite_emails = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = cls._get_manager(model_class)
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create_user(*args, **kwargs)

    @post_generation
    def super_user(self, created, extracted, **kwargs):
        if extracted:
            self.is_superuser = True
            self.is_staff = True


class CompetitionFactory(DjangoModelFactory):
    class Meta:
        model = Competition

    title = factory.Sequence(lambda n: f'Competition {n}')
    created_by = factory.SubFactory(UserFactory)
    logo = factory.django.ImageField()
    published = factory.LazyAttribute(lambda n: random.choice([True, True]))
    description = factory.Faker('paragraph')

    created_when = factory.Faker('date_time_between', start_date='-5y', end_date='now', tzinfo=UTC)

    @post_generation
    def collaborators(self, created, extracted, **kwargs):
        if not created:
            return
        if extracted:
            for user in extracted:
                self.collaborators.add(user)


class DataFactory(DjangoModelFactory):
    class Meta:
        model = Data

    created_by = factory.SubFactory(UserFactory)
    created_when = factory.LazyFunction(now)
    type = factory.Iterator([
        'ingestion_program',
        'input_data',
        'public_data',
        'reference_data',
        'scoring_program',
        'starting_kit',
        'competition_bundle',
        'submission',
        'solution'])
    name = factory.LazyAttribute(lambda o: f"{o.type} @ {o.created_when}")


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    name = factory.Sequence(lambda n: f'Task {n}')
    created_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def solutions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for solution in extracted:
                self.solutions.add(solution)


class SolutionFactory(DjangoModelFactory):
    class Meta:
        model = Solution

    name = factory.Sequence(lambda n: f'Solution {n}')


class QueueFactory(DjangoModelFactory):
    class Meta:
        model = Queue

    name = factory.Sequence(lambda n: f'Queue {n}')
    owner = factory.SubFactory(UserFactory)
    is_public = False


class PhaseFactory(DjangoModelFactory):
    class Meta:
        model = Phase

    competition = factory.SubFactory(CompetitionFactory)
    start = factory.LazyFunction(now)
    name = factory.Sequence(lambda n: f'Phase {n}')
    index = factory.Sequence(lambda n: n)

    @factory.post_generation
    def tasks(self, created, extracted, **kwargs):
        if not created:
            return

        if extracted:
            for task in extracted:
                self.tasks.add(task)
        else:
            self.tasks.add(TaskFactory.create())


class PhaseTaskInstanceFactory(DjangoModelFactory):
    class Meta:
        model = PhaseTaskInstance

    order_index = 99
    phase = factory.SubFactory(PhaseFactory)
    task = factory.SubFactory(TaskFactory)


class LeaderboardFactory(DjangoModelFactory):
    class Meta:
        model = Leaderboard

    title = factory.Faker('word')
    key = factory.Faker('word')


class SubmissionFactory(DjangoModelFactory):
    class Meta:
        model = Submission

    owner = factory.SubFactory(UserFactory)
    phase = factory.SubFactory(PhaseFactory)
    name = factory.Sequence(lambda n: f'Submission {n}')
    leaderboard = factory.SubFactory(LeaderboardFactory)

    created_when = factory.Faker('date_time_between', start_date='-5y', end_date='now', tzinfo=UTC)
    data = factory.SubFactory(
        DataFactory,
        type='submission',
        data_file=factory.LazyAttribute(lambda _: ContentFile('', 'submission.zip')),
        created_by=factory.SelfAttribute('..owner'),
        created_when=factory.SelfAttribute('..created_when'),
    )
    task = factory.LazyAttribute(lambda submission: random.choice(submission.phase.tasks.all()))


class CompetitionParticipantFactory(DjangoModelFactory):
    class Meta:
        model = CompetitionParticipant

    user = factory.SubFactory(UserFactory)
    competition = factory.SubFactory(CompetitionFactory)
    status = factory.LazyAttribute(lambda n: random.choice(['unknown', 'denied', 'approved', 'pending']))


class ColumnFactory(DjangoModelFactory):
    class Meta:
        model = Column

    title = factory.Faker('word')
    key = factory.Faker('word')
    index = factory.Sequence(lambda n: n)
    leaderboard = factory.SubFactory(LeaderboardFactory)
    sorting = factory.LazyAttribute(lambda n: random.choice(['asc', 'desc']))


class SubmissionScoreFactory(DjangoModelFactory):
    class Meta:
        model = SubmissionScore

    column = factory.SubFactory(ColumnFactory)
    score = factory.LazyAttribute(lambda n: random.choice(range(1, 11)) / 10)

    @post_generation
    def submissions(self, created, submissions, **kwargs):
        if not created:
            return
        if submissions:
            if isinstance(submissions, Submission):
                self.submissions.add(submissions)
            else:
                for sub in submissions:
                    self.submissions.add(sub)


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Faker('word')
    email = factory.Faker('email')
