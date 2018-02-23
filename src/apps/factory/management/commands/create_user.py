from django.core.management.base import BaseCommand
from termcolor import colored

from profiles.models import User as CodalabUser


class Command(BaseCommand):
    help = 'Add a user. Takes 2 positional args, username, email.'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            'email',
            type=str,
            dest='email',
            help='New users email (required)',
        )

        parser.add_argument(
            'username',
            type=str,
            dest='username',
            help='New users username (required)',
        )

    def handle(self, *args, **options):
        # These are the only 2 required fields.
        temp_username = options['username']
        temp_email = options['email']
        try:
            temp_user = CodalabUser.objects.create(email=temp_email, username=temp_username)
            print(colored('Successfully created user "%s"' % temp_user, 'green'))
        except:
            print(colored('Failed to create user', 'red'))
