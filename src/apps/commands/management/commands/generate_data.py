import random

from django.core.management.base import BaseCommand
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, CompetitionParticipantFactory


class Command(BaseCommand):
    help = "Generate data for testing"

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument(
            '-s'
            '--size',
            type=int,
            help='Determines the size of data to be created, i.e. 5 users, each with 5 comps with 5 phases with 5 submissions.'
                 'This defaults to 5 if no argument passed')

    def handle(self, *args, **kwargs):
        size = kwargs['size'] if 'size' in kwargs else 5
        users = [UserFactory(username='admin', super_user=True) if i == 0 else UserFactory() for i in range(size)]
        for user in users:
            for _ in range(size):
                comp = CompetitionFactory(created_by=user)
                for u in users:
                    CompetitionParticipantFactory(competition=comp, user=u, status='approved')
                for i in range(size):
                    phase = PhaseFactory(competition=comp, index=i)
                    for _ in range(size):
                        SubmissionFactory(phase=phase, owner=random.choice(users))
