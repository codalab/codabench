import uuid

from django.core.management.base import BaseCommand
from termcolor import colored

from profiles.models import User as CodalabUser

from tqdm import tqdm

from faker import Faker
fake = Faker()


class Command(BaseCommand):
    help = 'Creates a simple user, or multiple'

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
            count = options['amount']
        for i in tqdm(range(count), ncols=100):
            try:
                # Create a random user
                temp_bot_username = "{0}_{1}_{2}".format(fake.user_name(), str(uuid.uuid4())[0:8],
                                                         str(uuid.uuid4())[0:8])
                temp_bot_email = fake.email()
                temp_bot_name = fake.name()
                temp_bot = CodalabUser.objects.create(username=temp_bot_username, name=temp_bot_name, email=temp_bot_email)
            except:
                print(colored('Failed to create user', 'red'))
        print(
            colored("Operation completed succesfully! {} users created!".format(count))
        )
