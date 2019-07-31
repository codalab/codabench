import random

import factory
from django.utils.timezone import now
from factory import post_generation
from factory.django import DjangoModelFactory

from competitions.models import Competition, Phase, Submission, CompetitionParticipant
from datasets.models import Data
from leaderboards.models import Leaderboard, Column, SubmissionScore
from profiles.models import User
from tasks.models import Task


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Faker('user_name')
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = "test"

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
    published = factory.LazyAttribute(lambda n: random.choice([True, False]))

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


class SubmissionFactory(DjangoModelFactory):
    class Meta:
        model = Submission

    owner = factory.SubFactory(UserFactory)
    phase = factory.SubFactory(PhaseFactory)
    name = factory.Sequence(lambda n: f'Submission {n}')
    created_when = factory.LazyFunction(now)
    data = factory.SubFactory(
        DataFactory,
        type='submission',
        created_by=factory.SelfAttribute('..owner'),
        created_when=factory.SelfAttribute('..created_when'),
    )


class CompetitionParticipantFactory(DjangoModelFactory):
    class Meta:
        model = CompetitionParticipant

    user = factory.SubFactory(UserFactory)
    competition = factory.SubFactory(CompetitionFactory)
    status = factory.LazyAttribute(lambda n: random.choice(['unknown', 'denied', 'approved', 'pending']))


class LeaderboardFactory(DjangoModelFactory):
    class Meta:
        model = Leaderboard

    competition = factory.SubFactory(CompetitionFactory)
    key = factory.Faker('word')


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
