import uuid

from django.conf import settings
from django.db import models

from settings.base import BundleStorage
from utils.data import PathWrapper


class Data(models.Model):
    """Data models are unqiue based on name + created_by. If no name is given, then there is no uniqueness to enforce"""
    TYPES = (
        ('Ingestion Program', 'Ingestion Program',),
        ('Input Data', 'Input Data',),
        ('Public Data', 'Public Data',),
        ('Reference Data', 'Reference Data',),
        ('Scoring Program', 'Scoring Program',),
        ('Starting Kit', 'Starting Kit',),
        ('Competition Bundle', 'Competition Bundle',),
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
