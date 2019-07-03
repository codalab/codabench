import datetime
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.timezone import now

from chahub.models import ChaHubSaveMixin
from utils.data import PathWrapper
from utils.storage import BundleStorage


class Data(ChaHubSaveMixin, models.Model):
    """Data models are unqiue based on name + created_by. If no name is given, then there is no uniqueness to enforce"""

    # It's useful to have these defaults map to the YAML names for these, like `scoring_program`
    INGESTION_PROGRAM = 'ingestion_program'
    INPUT_DATA = 'input_data'
    PUBLIC_DATA = 'public_data'
    REFERENCE_DATA = 'reference_data'
    SCORING_PROGRAM = 'scoring_program'
    STARTING_KIT = 'starting_kit'
    COMPETITION_BUNDLE = 'competition_bundle'
    SUBMISSION = 'submission'
    SOLUTION = 'solution'

    TYPES = (
        (INGESTION_PROGRAM, 'Ingestion Program',),
        (INPUT_DATA, 'Input Data',),
        (PUBLIC_DATA, 'Public Data',),
        (REFERENCE_DATA, 'Reference Data',),
        (SCORING_PROGRAM, 'Scoring Program',),
        (STARTING_KIT, 'Starting Kit',),
        (COMPETITION_BUNDLE, 'Competition Bundle',),
        (SUBMISSION, 'Submission',),
        (SOLUTION, 'Solution',),
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_when = models.DateTimeField(default=now)
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=64, choices=TYPES)
    description = models.TextField(null=True, blank=True)
    data_file = models.FileField(
        upload_to=PathWrapper('dataset'),
        storage=BundleStorage,
        null=True,
        blank=True
    )
    key = models.UUIDField(default=uuid.uuid4, blank=True, unique=True)
    is_public = models.BooleanField(default=False)
    upload_completed_successfully = models.BooleanField(default=False)

    # This is true if the Data model was created as part of unpacking a competition. Competition bundles themselves
    # are NOT marked True, since they are not created by unpacking!
    was_created_by_competition = models.BooleanField(default=False)

    # TODO: add Model manager that automatically filters out upload_completed_successfully=False from queries
    # TODO: remove upload_completed_successfully=False after 3 days ???

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.created_by.username} - {self.type}"
        return super().save(*args, **kwargs)

    @property
    def in_use(self):
        from competitions.models import Competition
        competitions_in_use = Competition.objects.filter(
            Q(phases__tasks__ingestion_program=self) |
            Q(phases__tasks__input_data=self) |
            Q(phases__tasks__reference_data=self) |
            Q(phases__tasks__scoring_program=self)
        ).values_list('pk', flat=True)
        return competitions_in_use

    def __str__(self):
        return self.name or ''

    def get_chahub_endpoint(self):
        return "datasets/"

    def clean_chahub_data(self, data):
        validated_data = {}
        for key, item in data.items():
            if not item:
                continue
            elif isinstance(item, datetime.datetime):
                validated_data[key] = item.isoformat()
            elif isinstance(item, uuid.UUID):
                validated_data[key] = str(item)
            else:
                validated_data[key] = item
        return validated_data

    def get_chahub_data(self):
        data = {
            'creator_id': self.created_by.id,
            'remote_id': self.pk,
            'created_by': str(self.created_by.username),
            'created_when': self.created_when,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'key': self.key,
            'is_public': self.is_public
        }
        chahub_id = self.created_by.chahub_uid
        if chahub_id:
            data['user'] = chahub_id
        data = self.clean_chahub_data(data)
        return [data]

    def get_chahub_is_valid(self):
        return self.is_public


class DataGroup(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_when = models.DateTimeField(default=now)
    name = models.CharField(max_length=255)
    datas = models.ManyToManyField(Data, related_name="groups")
