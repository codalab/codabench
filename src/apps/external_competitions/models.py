from django.db import models
from django.utils.timezone import now


class ExternalPlatform(models.Model):
    PLATFORM_TYPE_CODABENCH = 'codabench'
    PLATFORM_TYPE_CODALAB = 'codalab'
    PLATFORM_TYPE_CHOICES = (
        (PLATFORM_TYPE_CODABENCH, 'Codabench instance'),
        (PLATFORM_TYPE_CODALAB, 'CodaLab instance'),
    )

    name = models.CharField(max_length=128, unique=True)
    platform_type = models.CharField(max_length=32, choices=PLATFORM_TYPE_CHOICES)
    competitions_fetch_url = models.URLField(help_text="API URL used to fetch the list of competitions from this platform")
    competition_base_url = models.URLField(help_text="Base URL used to build links back to individual competitions on this platform")
    is_active = models.BooleanField(default=True, help_text="Inactive platforms are skipped by the fetch task")
    created_when = models.DateTimeField(default=now)
    updated_when = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ExternalCompetition(models.Model):
    platform = models.ForeignKey(ExternalPlatform, on_delete=models.CASCADE, related_name='competitions')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    image_url = models.URLField(max_length=1000, blank=True, default='')
    organizer_name = models.CharField(max_length=255, blank=True, default='')
    competition_url = models.URLField(unique=True, help_text="Link to the competition on its source platform")
    competition_created_when = models.DateTimeField(
        null=True, blank=True, help_text="When the competition was created on its source platform"
    )
    competition_started_when = models.DateTimeField(
        null=True, blank=True, help_text="When the competition starts/started on its source platform"
    )
    created_when = models.DateTimeField(default=now)
    updated_when = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.platform.name})"


class ExternalFetchLog(models.Model):
    STATUS_RUNNING = 'RUNNING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_PARTIAL_SUCCESS = 'PARTIAL_SUCCESS'
    STATUS_FAILURE = 'FAILURE'
    STATUS_CHOICES = (
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_PARTIAL_SUCCESS, 'Partial success'),
        (STATUS_FAILURE, 'Failure'),
    )

    platform = models.ForeignKey(ExternalPlatform, on_delete=models.CASCADE, related_name='fetch_logs')
    started_at = models.DateTimeField(default=now)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RUNNING)
    total_fetched = models.PositiveIntegerField(default=0)
    new_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    deleted_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.platform.name} @ {self.started_at:%Y-%m-%d %H:%M} — {self.status}"
