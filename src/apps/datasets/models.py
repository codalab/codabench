import uuid

from django.conf import settings
from django.db import models

from settings.base import BundleStorage
from utils.data import PathWrapper


class Data(models.Model):
    """Data models are unqiue based on name + created_by. If no name is given, then there is no uniqueness to enforce"""

    # It's useful to have these defaults map to the YAML names for these, like `scoring_program`
    INGESTION_PROGRAM = 'ingestion_program'
    INPUT_DATA = 'input_data'
    PUBLIC_DATA = 'public_data'
    REFERENCE_DATA = 'reference_data'
    SCORING_PROGRAM = 'scoring_program'
    STARTING_KIT = 'starting_kit'
    COMPETITION_BUNDLE = 'competition_bundle'

    TYPES = (
        (INGESTION_PROGRAM, 'Ingestion Program',),
        (INPUT_DATA, 'Input Data',),
        (PUBLIC_DATA, 'Public Data',),
        (REFERENCE_DATA, 'Reference Data',),
        (SCORING_PROGRAM, 'Scoring Program',),
        (STARTING_KIT, 'Starting Kit',),
        (COMPETITION_BUNDLE, 'Competition Bundle',),
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=64, choices=TYPES)
    description = models.TextField(null=True, blank=True)
    data_file = models.FileField(
        upload_to=PathWrapper('dataset'),
        storage=BundleStorage
    )
    key = models.UUIDField(default=uuid.uuid4, blank=True)
    is_public = models.BooleanField(default=False)
    upload_completed_successfully = models.BooleanField(default=False)

    # This is true if the Data model was created as part of unpacking a competition. Competition bundles themselves
    # are NOT marked True, since they are not created by unpacking!
    was_created_by_competition = models.BooleanField(default=False)

    # TODO: add Model manager that automatically filters out upload_completed_successfully=False from queries
    # TODO: remove upload_completed_successfully=False after 3 days ???

    # class Meta:
    #     unique_together = ('name', 'created_by')

    # def clean(self):
    #     if self.name:
    #         if Data.objects.filter(name=self.name, created_by=self.created_by).exists():
    #             raise ValidationError("")
    #     super().clean()


class DataGroup(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    datas = models.ManyToManyField(Data, related_name="groups")
