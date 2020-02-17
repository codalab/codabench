import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from factories import UserFactory, CompetitionFactory, PhaseFactory, SubmissionFactory, CompetitionParticipantFactory, \
    TaskFactory


User = get_user_model()


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
        users = []
        for i in range(size):
            if i == 0 and not no_admin:
                try:
                    user = UserFactory(username='admin', password='admin', super_user=True)
                except IntegrityError:
                    # admin user already exists
                    user = User.objects.get(username='admin')
            else:
                user = UserFactory()
            users.append(user)

        for user in users:
            for _ in range(size):
                comp = CompetitionFactory(created_by=user)
                for u in users:
                    try:
                        CompetitionParticipantFactory(competition=comp, user=u, status='approved')
                    except IntegrityError:
                        # User already a participant in the competition
                        pass
                for i in range(size):
                    phase = PhaseFactory(competition=comp, index=i, tasks=[TaskFactory(created_by=user)])
                    for _ in range(size):
                        SubmissionFactory(phase=phase, owner=random.choice(users))
