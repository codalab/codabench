from django.db import models
from django.conf import settings


class StorageUsageHistory(models.Model):
    bucket_name = models.CharField(max_length=255)
    total_usage = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )  # in KiB up to ~ 930 TiB
    competitions_usage = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    users_usage = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    admin_usage = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    orphaned_file_usage = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    at_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class CompetitionStorageDataPoint(models.Model):
    competition = models.ForeignKey(
        "competitions.competition", null=True, on_delete=models.SET_NULL
    )
    datasets_total = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    at_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserStorageDataPoint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    datasets_total = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    submissions_total = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    at_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class AdminStorageDataPoint(models.Model):
    backups_total = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )  # stores bytes
    at_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
