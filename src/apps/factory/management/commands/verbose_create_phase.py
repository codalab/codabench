import datetime
import random
import uuid

from django.core.exceptions import ObjectDoesNotExist
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
            'comp',
            # action='store_true',
            # dest='delete',
            type=int,
            #dest='competition',
            help='PK of the competition',
        )

        parser.add_argument(
            '--index',
            # action='store_true',
            # dest='delete',
            type=int,
            dest='index',
            help='Index of the phase',
        )

        parser.add_argument(
            '--start',
            # action='store_true',
            # dest='delete',
            type=lambda d: datetime.strptime(d, '%Y%m%d'), # Convert to string
            dest='start_date',
            help='Start date in Y-m-d format',
        )

        parser.add_argument(
            '--end',
            # action='store_true',
            # dest='delete',
            type=lambda d: datetime.strptime(d, '%Y%m%d'),  # Convert to string
            dest='end_date',
            help='End date in Y-m-d format',
        )

        parser.add_argument(
            '--desc',
            # action='store_true',
            # dest='delete',
            type=str,
            dest='description',
            help='Description of the phase',
        )

        parser.add_argument(
            '--name',
            # action='store_true',
            # dest='delete',
            type=str,
            dest='name',
            help='Name of the phase',
        )

    def handle(self, *args, **options):
        # Init specific vars
        temp_competition = None
        temp_index = None
        temp_start = None
        temp_end = None
        temp_name = None
        temp_description = None

        if options['comp']:
            try:
                temp_competition = Competition.objects.get(pk=options['comp'])
                self.stdout.write(self.style.SUCCESS(
                    'Succesfully found competition {0} with pk {1}'.format(temp_competition, options['comp'])))
            except ObjectDoesNotExist:
                self.stdout.write(self.style.SUCCESS('Failed to find competition with pk: {}'.format(options['comp'])))
                raise ObjectDoesNotExist(
                    'Failed to find the competition to attach to. Breaking...'
                )

        if options['start_date']:
            temp_start = options['start_date']
        else:
            # Our start date was within the last year-month
            temp_start = timezone.now() + datetime.timedelta(days=random.randint(-365, -30))

        if options['end_date']:
            temp_end = options['end_date']
        else:
            # Our comp will end in the next month to year
            temp_end = timezone.now() + datetime.timedelta(days=random.randint(30, 365))

        if options['index']:
            temp_index = options['index']
        else:
            # Grab all our phases for this comp, order them by increasing index,
            # find the last one ( Largest index), Add one to that index
            if Phase.objects.all().count() == 0:
                temp_index = 0
            else:
                last_phase = Phase.objects.filter(competition=temp_competition).order_by('index').last()
                if last_phase:
                    temp_index = last_phase.index + 1
                else:
                    temp_index = 0

        if options['name']:
            temp_name = options['name']
        else:
            temp_name = "Phase_{}".format(uuid.uuid4())

        if options['description']:
            temp_description = options['description']
        else:
            temp_description = "Description for phase {}".format(temp_name)

        try:
            new_phase = Phase.objects.create(
                name=temp_name,
                description=temp_description,
                competition=temp_competition,
                index=temp_index,
                start=temp_start,
                end=temp_end,
            )
            self.stdout.write(self.style.SUCCESS(
                'Successfully created new phase {0} with index {1} for competition {2}!'.format(new_phase, temp_index,
                                                                                                temp_competition)))
        except:
            self.stdout.write(self.style.SUCCESS('Failed to create phase'))
