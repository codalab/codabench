import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from django.urls import reverse
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
    file_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # This is true if the Data model was created as part of unpacking a competition. Competition bundles themselves
    # are NOT marked True, since they are not created by unpacking!
    was_created_by_competition = models.BooleanField(default=False)

    # TODO: add Model manager that automatically filters out upload_completed_successfully=False from queries
    # TODO: remove upload_completed_successfully=False after 3 days ???

    def get_download_url(self):
        return reverse('datasets:download', kwargs={'key': self.key})

    def save(self, *args, **kwargs):
        if not self.file_size and self.data_file:
            try:
                # save file size as kbs
                self.file_size = self.data_file.size / 1024
            except TypeError:
                # file returns a None size, can't divide None / 1024
                self.file_size = 0
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
            Q(phases__tasks__scoring_program=self)
        ).values_list('pk', flat=True).distinct()
        return competitions_in_use

    def __str__(self):
        return self.name or ''

    @staticmethod
    def get_chahub_endpoint():
        return "datasets/"

    def get_chahub_is_valid(self):
        if not self.was_created_by_competition:
            return self.upload_completed_successfully
        else:
            return True

    def get_whitelist(self):
        return ['remote_id', 'is_public']

    def get_chahub_data(self):
        ssl = settings.SECURE_SSL_REDIRECT
        site = Site.objects.get_current().domain
        return self.clean_private_data({
            'creator_id': self.created_by.id,
            'remote_id': self.pk,
            'created_by': str(self.created_by.username),
            'created_when': self.created_when.isoformat(),
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'key': str(self.key),
            'is_public': self.is_public,
            'download_url': f'http{"s" if ssl else ""}://{site}{self.get_download_url()}'
        })


class DataGroup(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_when = models.DateTimeField(default=now)
    name = models.CharField(max_length=255)
    datas = models.ManyToManyField(Data, related_name="groups")
