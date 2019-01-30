import factory
from django.utils.timezone import now
from factory.django import DjangoModelFactory

from competitions.models import Competition, Phase, Submission
from datasets.models import Data
from profiles.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    # TODO: change this to use create_user()?
    username = factory.Faker('user_name')
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'admin')


class CompetitionFactory(DjangoModelFactory):
    class Meta:
        model = Competition

    title = factory.Sequence(lambda n: f'Competition {n}')
    created_by = factory.SubFactory(UserFactory)


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


def create_competition_with_phases(user=None, number_of_phases=3):
    user = UserFactory() if user is None else user
    competition = CompetitionFactory(created_by=user)
    for i in range(number_of_phases):
        PhaseFactory(competition=competition, index=i)
    return competition
