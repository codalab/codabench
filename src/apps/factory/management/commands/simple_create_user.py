import datetime
import random
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from competitions.models import Competition, Phase, Submission
from datasets.models import DataGroup, Data
from profiles.models import User as CodalabUser


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        #     # parser.add_argument('poll_id', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument(
            '--number',
            # action='store_true',
            # dest='delete',
            type=int,
            dest='amount',
            help='Amount of users to create',
        )

    def handle(self, *args, **options):
        count = 1
        if options['amount']:
            print(options['amount'])
            count = options['amount']
        for i in range(count):
            print(i)
            try:
                # Get or create a random user via UUID ( If we get lucky they exist? )
                temp_username = uuid.uuid4()
                temp_email = "{}.mailinator.com".format(temp_username)
                temp_name = "Bot_{}".format(temp_username)
                temp_user = CodalabUser.objects.create(username=temp_username, name=temp_name, email=temp_email)

                self.stdout.write(self.style.SUCCESS('Successfully created user "%s"' % temp_user))
            except:
                self.stdout.write(self.style.SUCCESS('Failed to create user'))