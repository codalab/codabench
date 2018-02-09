from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

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
                self.stdout.write(self.style.SUCCESS(
                    'Successfully found user {0} for email {1}'.format(
                        temp_user,
                        options['user'],
                    )
                ))
            except ObjectDoesNotExist:
                self.stdout.write(self.style.SUCCESS(
                    'Failed to find user for email {}'.format(
                        options['user'],
                    )
                ))
                raise ObjectDoesNotExist('Failed to find user for email {}'.format(
                    options['user'],
                ))

        if options['comp']:
            try:
                temp_competition = Competition.objects.get(pk=options['comp'])
                self.stdout.write(self.style.SUCCESS(
                    'Successfully found comp {0} for pk {1}'.format(
                        temp_competition,
                        options['comp'],
                    )
                ))
            except ObjectDoesNotExist:
                self.stdout.write(self.style.SUCCESS(
                    'Failed to find comp for pk {}'.format(
                        options['comp'],
                    )
                ))
                raise ObjectDoesNotExist('Failed to find comp for pk {}'.format(
                    options['comp'],
                ))

        # See if one exists already before making a new one
        try:
            existing_part = CompetitionParticipant.objects.get(competition=temp_competition, user=temp_user)
            self.stdout.write(
                self.style.SUCCESS('Failed to create participant, one already exists for this user and comp'))
            raise ValueError("Object already exists!")
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.SUCCESS('Particpant does not exist for competition and user, proceeding.'))
            existing_part = None

        try:
            new_part = CompetitionParticipant.objects.create(
                competition=temp_competition,
                user=temp_user
            )
            self.stdout.write(self.style.SUCCESS(
                'Successfully created new participant for user {0} on competition {1}'.format(
                    temp_user,
                    temp_competition,
                )
            ))
        except:
            self.stdout.write(self.style.SUCCESS('Failed to create participant'))
