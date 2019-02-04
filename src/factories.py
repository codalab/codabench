import random

import factory
from django.utils.timezone import now
from factory import post_generation
from factory.django import DjangoModelFactory

from competitions.models import Competition, Phase, Submission, CompetitionParticipant
from datasets.models import Data
from profiles.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Faker('user_name')
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'admin')

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


class PhaseFactory(DjangoModelFactory):
    class Meta:
        model = Phase

    competition = factory.SubFactory(CompetitionFactory)
    start = factory.LazyFunction(now)
    name = factory.Sequence(lambda n: f'Phase {n}')
    index = factory.Sequence(lambda n: n)


class DataFactory(DjangoModelFactory):
    class Meta:
        model = Data

    created_by = factory.SubFactory(UserFactory)
    created_when = factory.LazyFunction(now)
    name = factory.LazyAttribute(lambda o: f"{o.type} @ {o.created_when}")


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
