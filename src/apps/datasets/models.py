import uuid
import botocore
import logging

import botocore.exceptions
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.timezone import now
from decimal import Decimal

from utils.data import PathWrapper
from utils.storage import BundleStorage
from competitions.models import Competition


logger = logging.getLogger()


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
    file_size = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # in Bytes

    # This is true if the Data model was created as part of unpacking a competition. Competition bundles themselves
    # are NOT marked True, since they are not created by unpacking!
    was_created_by_competition = models.BooleanField(default=False)

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, related_name='submission')
    file_name = models.CharField(max_length=64, default="")

    def get_download_url(self):
        return reverse('datasets:download', kwargs={'key': self.key})

    def save(self, *args, **kwargs):
        if self.data_file and (not self.file_size or self.file_size == -1):
            try:
                # save file size in bytes
                # self.data_file.size returns bytes
                self.file_size = self.data_file.size
            except TypeError:
                # -1 indicates an error
                self.file_size = Decimal(-1)
            except botocore.exceptions.ClientError:
                # file might not exist in the storage
                logger.warning(f"The data_file of Data id={self.id} does not exist in the storage. data_file and file_size has been cleared")
                self.file_size = Decimal(0)
                self.data_file = None

        if not self.name:
            self.name = f"{self.created_by.username} - {self.type}"
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.data_file.delete()
        super().delete(*args, **kwargs)

    @property
    def in_use(self):
        from competitions.models import Competition
        competitions_in_use = Competition.objects.filter(
            Q(phases__tasks__ingestion_program=self) |
            Q(phases__tasks__input_data=self) |
            Q(phases__tasks__reference_data=self) |
            Q(phases__tasks__scoring_program=self) |
            Q(phases__starting_kit=self) |
            Q(phases__public_data=self)
        ).values('pk', 'title').distinct()
        return competitions_in_use

    def __str__(self):
        return f'{self.name}({self.id})'


class DataGroup(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_when = models.DateTimeField(default=now)
    name = models.CharField(max_length=255)
    datas = models.ManyToManyField(Data, related_name="groups")
