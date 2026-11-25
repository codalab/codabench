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


class OrphanFilesJob(models.Model):
    class JobType(models.TextChoices):
        SCAN = "scan", "Scan"
        CLEANUP = "cleanup", "Cleanup"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        STARTED = "STARTED", "Started"
        PROGRESS = "PROGRESS", "In progress"
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        REVOKED = "REVOKED", "Revoked"

    task_id = models.UUIDField(unique=True)

    job_type = models.CharField(
        max_length=16,
        choices=JobType.choices,
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )

    grace_period_days = models.PositiveIntegerField(default=7)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    result = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]