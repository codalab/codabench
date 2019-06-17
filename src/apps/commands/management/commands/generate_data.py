import random

from django.core.management.base import BaseCommand
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, CompetitionParticipantFactory, \
    TaskFactory


class Command(BaseCommand):
    help = "Generate data for testing"

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument(
            '-n',
            '--no-admin',
            action='store_true',
            help='Do not create a superuser w/ username "admin"')
        parser.add_argument(
            '-s',
            '--size',
            type=int,
            help='Determines the size of data to be created, i.e. 3 users, each with 3 comps with 3 phases with 3 submissions.'
                 'This defaults to 3')

    def handle(self, *args, **kwargs):
        size = kwargs.get('size') or 3
        no_admin = kwargs.get('no_admin')
        print(f'Creating data of size {size} {"without an admin account." if no_admin else "with an admin account." }')
        users = [UserFactory(username='admin', super_user=True) if i == 0 and not no_admin else UserFactory() for i in range(size)]
        for user in users:
            for _ in range(size):
                comp = CompetitionFactory(created_by=user)
                for u in users:
                    CompetitionParticipantFactory(competition=comp, user=u, status='approved')
                for i in range(size):
                    phase = PhaseFactory(competition=comp, index=i, tasks=[TaskFactory(created_by=user)])
                    for _ in range(size):
                        SubmissionFactory(phase=phase, owner=random.choice(users))
