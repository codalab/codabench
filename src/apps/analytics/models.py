from django.db import models
from competitions.models import Competition


class StorageUsageHistory(models.Model):
    bucket_name = models.CharField(max_length=255)
    at_date = models.DateTimeField()
    total_usage = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True) # in KiB up to ~ 930 TiB
    competitions_usage = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    users_usage = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    admin_usage = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CompetitionStorageDataPoint(models.Model):
    competition_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    created_by = models.CharField(max_length=255)
    created_when = models.DateTimeField()
    competition_type = models.CharField(max_length=128, choices=Competition.COMPETITION_TYPE, default=Competition.COMPETITION)
    datasets_total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    at_date = models.DateTimeField()


class UserStorageDataPoint(models.Model):
    user_id = models.PositiveIntegerField()
    email = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    datasets_total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    submissions_total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    at_date = models.DateTimeField()


class AdminStorageDataPoint(models.Model):
    backups_total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    others_total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    at_date = models.DateTimeField()
