import uuid

from django.conf import settings
from django.db import models

from settings.base import BundleStorage
from utils.data import PathWrapper


class Data(models.Model):
    TYPES = (
        ('Ingestion Program', 'Ingestion Program',),
        ('Input Data', 'Input Data',),
        ('Public Data', 'Public Data',),
        ('Reference Data', 'Reference Data',),
        ('Scoring Program', 'Scoring Program',),
        ('Starting Kit', 'Starting Kit',),
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=64, choices=TYPES)
    description = models.TextField(null=True, blank=True)
    data_file = models.FileField(
        upload_to=PathWrapper('dataset'),
        storage=BundleStorage
    )
    key = models.UUIDField(default=uuid.uuid4, blank=True)
    is_public = models.BooleanField(default=False)
    upload_completed_successfully = models.BooleanField(default=False)

    # TODO: add Model manager that automatically filters out upload_completed_successfully=False

    class Meta:
        unique_together = ('name', 'created_by')


class DataGroup(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    datas = models.ManyToManyField(Data, related_name="groups")
