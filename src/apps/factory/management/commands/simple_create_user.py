import uuid

from django.core.management.base import BaseCommand
from profiles.models import User as CodalabUser


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--number',
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
                # Create a random user
                temp_username = uuid.uuid4()
                temp_email = "{}.mailinator.com".format(temp_username)
                temp_name = "Bot_{}".format(temp_username)
                temp_user = CodalabUser.objects.create(username=temp_username, name=temp_name, email=temp_email)

                self.stdout.write(self.style.SUCCESS('Successfully created user "%s"' % temp_user))
            except:
                self.stdout.write(self.style.SUCCESS('Failed to create user'))