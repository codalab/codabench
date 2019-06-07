import random

from django.core.management.base import BaseCommand
from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, CompetitionParticipantFactory, \
    TaskFactory


class Command(BaseCommand):
    help = "Generate data for testing"

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument(
            '-a',
            '--create-admin',
            type=bool,
            help='Whether to create an admin'
                 'This defaults to false')
        parser.add_argument(
            '-s',
            '--size',
            type=int,
            help='Determines the size of data to be created, i.e. 5 users, each with 5 comps with 5 phases with 5 submissions.'
                 'This defaults to 5 if no argument passed')

    def handle(self, *args, **kwargs):
        size = kwargs['size'] if kwargs['size'] else 5
        create_admin = kwargs['create_admin'] if kwargs['create_admin'] else False
        users = [UserFactory(username='admin', super_user=True) if i == 0 and create_admin else UserFactory() for i in range(size)]
        for user in users:
            for _ in range(size):
                comp = CompetitionFactory(created_by=user)
                for u in users:
                    CompetitionParticipantFactory(competition=comp, user=u, status='approved')
                for i in range(size):
                    phase = PhaseFactory(competition=comp, index=i, tasks=[TaskFactory(created_by=user)])
                    for _ in range(size):
                        SubmissionFactory(phase=phase, owner=random.choice(users))
