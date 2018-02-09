import datetime
import random
import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone

from competitions.models import Competition
from profiles.models import User as CodalabUser


class Command(BaseCommand):
    help = 'Creates a dummy competition'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--number',
            type=int,
            dest='amount',
            help='Amount of comps/users to create',
        )

    def handle(self, *args, **options):
        count = 1
        if options['amount']:
            count = options['amount']

        for i in range(count):
            try:
                # Setup a temp user
                temp_username = uuid.uuid4()
                temp_email = "{}.mailinator.com".format(temp_username)
                temp_name = "Bot_{}".format(temp_username)
                temp_user = CodalabUser.objects.create(username=temp_username, name=temp_name, email=temp_email)

                # Setup a new comp
                new_comp = Competition.objects.create(title="Competition {}".format(uuid.uuid4()), created_by=temp_user)
                new_comp.created_when = timezone.now() + datetime.timedelta(days=random.randint(-15, 15))
                new_comp.save()
                self.stdout.write(self.style.SUCCESS('Successfully created new user and competition: {0}, {1}'.format(temp_user, new_comp)))
            except:
                self.stdout.write(self.style.SUCCESS('Failed to create competition'))
