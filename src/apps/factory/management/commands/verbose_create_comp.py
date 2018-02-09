import datetime
import random
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from competitions.models import Competition, Phase, Submission
from datasets.models import DataGroup, Data
from profiles.models import User as CodalabUser


class Command(BaseCommand):
    help = 'Creates a dummy competition'

    def add_arguments(self, parser):
        #     # parser.add_argument('poll_id', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument(
            '--number',
            # action='store_true',
            # dest='delete',
            type=int,
            dest='amount',
            help='Amount of comps/users to create',
        )
        parser.add_argument(
            '--user',
            # action='store_true',
            # dest='delete',
            type=str,
            dest='user',
            help='Creator of the comp',
        )
        parser.add_argument(
            '--title',
            # action='store_true',
            # dest='delete',
            type=str,
            dest='title',
            help='Title of the competition',
        )
        parser.add_argument(
            '--multiple',
            # action='store_true',
            # dest='delete',
            type=bool,
            dest='multiple',
            help='Create multiple users/competitions?',
        )
        parser.add_argument(
            '--random',
            # action='store_true',
            # dest='delete',
            type=bool,
            dest='random_date',
            help='Random Start Date?',
        )
        parser.add_argument(
            '--fail_easy',
            # action='store_true',
            # dest='delete',
            type=bool,
            dest='fail_easy',
            help='Fail if user not found, or error.',
        )

    def handle(self, *args, **options):
        # Init specific vars
        count = 1
        temp_user = None
        temp_title = None
        temp_date = None

        # If we have an amount inputted, set our count to that
        if options['amount'] and options['multiple']:
            print(options['amount'])
            count = options['amount']
        # If we have a title inputed, set our title to that
        if options['title']:
            temp_title = options['title']

        # If we are given a user
        if options['user']:
            print("User email given as : {}".format(options['user']))
            # Try to grab them and say whether we found them, alert on fail
            try:
                temp_user = CodalabUser.objects.get(email=options['user'])
                self.stdout.write(self.style.SUCCESS('Succesfully found user with email: {}'.format(options['user'])))
            except:
                self.stdout.write(self.style.SUCCESS('Failed to find user with email: {}'.format(options['user'])))
                if options['fail_easy']:
                    raise ValueError(
                        'The user with email: `{}` was not found and the fail_easy flag is set. Breaking...'.format(
                            options['user']))
        # For the number of objects we should create
        for i in range(count):
            try:
                # If our user is not set, create a random new one and set our user to that
                if not temp_user:
                    temp_username = uuid.uuid4()
                    temp_email = "{}.mailinator.com".format(temp_username)
                    temp_name = "Bot_{}".format(temp_username)
                    temp_user = CodalabUser.objects.create(username=temp_username, name=temp_name, email=temp_email)

                # If no temp_title, generate a new one
                if not temp_title:
                    temp_title = "Competition {}".format(uuid.uuid4())

                # Should we generate a random date?
                if options['random_date']:
                    temp_date = timezone.now() + datetime.timedelta(days=random.randint(-15, 15))
                else:
                    temp_date = timezone.now()

                new_comp = Competition.objects.create(title=temp_title, created_by=temp_user)
                new_comp.created_when = temp_date
                new_comp.save()
                self.stdout.write(self.style.SUCCESS('Successfully created new user and competition: {0}, {1}'.format(temp_user, new_comp)))
            except:
                self.stdout.write(self.style.SUCCESS('Failed to create competition'))
                if options['fail_easy']:
                    raise ValueError(
                        'Failed to create one or more competitions. Breaking...'
                    )