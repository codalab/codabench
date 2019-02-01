import random

from django.core.management.base import BaseCommand
from competitions.models import CompetitionParticipant
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory


class Command(BaseCommand):
    help = "Generate data for testing"

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument(
            '-s'
            '--size',
            type=int,
            help='Determines the size of data to be created, i.e. 5 users, each with 5 comps with 5 phases with 5 submissions.'
                 'This defaults to 5')

    def handle(self, *args, **kwargs):
        size = kwargs['size'] if 'size' in kwargs else 5
        users = [UserFactory(username='admin', super_user=True) if i == 0 else UserFactory() for i in range(size)]
        competition_count = 0
        phases = 0
        submissions = 0
        for user in users:
            for _ in range(size):
                comp = self.create_competition_with_phases(user=user, nb_phases=size)
                competition_count += 1

                for phase in comp.phases.all():
                    phases += 1
                    for _ in range(size):
                        SubmissionFactory(phase=phase, owner=random.choice(users))
                        submissions += 1

        for user in users:
            competitions = []
            for submission in user.submission.all().select_related('phase__competition'):
                competitions.append(submission.phase.competition)
            competitions = set(competitions)
            for competition in competitions:
                CompetitionParticipant.objects.create(
                    status='approved',
                    competition=competition,
                    user=user,
                )

        print(f'Created {len(users)} users.')
        print(f'Created {competition_count} competitions.')
        print(f'Created {phases} phases.')
        print(f'Created {submissions} submissions.')

    @staticmethod
    def create_competition_with_phases(user, nb_phases):
        competition = CompetitionFactory(created_by=user)
        for i in range(nb_phases):
            PhaseFactory(competition=competition, index=i)
        return competition
