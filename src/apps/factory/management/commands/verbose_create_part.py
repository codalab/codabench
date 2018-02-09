from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from termcolor import colored

from competitions.models import Competition, CompetitionParticipant
from profiles.models import User as CodalabUser


class Command(BaseCommand):
    help = 'Creates a dummy competition'

    def add_arguments(self, parser):
        # Required Positional args
        parser.add_argument(
            'user',
            type=str,
            help='email of the user',
        )
        parser.add_argument(
            'comp',
            type=int,
            help='pk of the competition',
        )

    def handle(self, *args, **options):
        # Init specific vars
        temp_competition = None
        temp_user = None
        existing_part = None

        if options['user']:
            try:
                temp_user = CodalabUser.objects.get(email=options['user'])
                self.stdout.write(
                    colored(
                        'Successfully found user {0} for email {1}'.format(
                            temp_user,
                            options['user'],
                        ),
                        'green',
                    )
                )
            except ObjectDoesNotExist:
                self.stdout.write(
                    colored(
                        'Failed to find user for email {}'.format(
                            options['user'],
                        ),
                        'red',
                    )
                )
                raise ObjectDoesNotExist('Failed to find user for email {}'.format(
                    options['user'],
                ))

        if options['comp']:
            try:
                temp_competition = Competition.objects.get(pk=options['comp'])
                self.stdout.write(
                    colored(
                        'Successfully found comp {0} for pk {1}'.format(
                            temp_competition,
                            options['comp'],
                        ),
                        'green',
                    )
                )
            except ObjectDoesNotExist:
                self.stdout.write(
                    colored(
                        'Failed to find comp for pk {}'.format(
                            options['comp'],
                        ),
                        'red',
                    )
                )
                raise ObjectDoesNotExist('Failed to find comp for pk {}'.format(
                    options['comp'],
                ))

        # See if one exists already before making a new one
        try:
            existing_part = CompetitionParticipant.objects.get(competition=temp_competition, user=temp_user)
            self.stdout.write(
                colored(
                    'Failed to create participant, one already exists for this user and comp',
                    'red',
                )
            )
            raise ValueError("Object already exists!")
        except ObjectDoesNotExist:
            self.stdout.write(
                colored(
                    'Particpant does not exist for competition and user, proceeding.'
                    'green',
                )
            )
            existing_part = None

        try:
            new_part = CompetitionParticipant.objects.create(
                competition=temp_competition,
                user=temp_user
            )
            self.stdout.write(
                colored(
                    'Successfully created new participant {0} for user {1} on competition {2}'.format(
                        new_part,
                        temp_user,
                        temp_competition,
                    ),
                    'green',
                )
            )
        except:
            self.stdout.write(
                colored('Failed to create participant', 'red')
            )
