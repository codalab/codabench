import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now


class Task(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    key = models.UUIDField(default=uuid.uuid4, blank=True, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(default=now)
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_tasks', blank=True)

    ingestion_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_ingestion_programs")
    input_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_input_datas")
    ingestion_only_during_scoring = models.BooleanField(default=False)

    reference_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_reference_datas")
    scoring_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_scoring_programs")

    def __str__(self):
        return f"Task - {self.name} - ({self.id})"

    @property
    def _validated(self):
        # TODO: Should only include submissions that are successful, not any!
        return self.solutions.filter(md5__in=self.phases.values_list('submissions__md5', flat=True)).exists()


class Solution(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    key = models.UUIDField(default=uuid.uuid4, blank=True, unique=True)
    tasks = models.ManyToManyField(Task, related_name="solutions")
    data = models.ForeignKey('datasets.Data', null=True, blank=True, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    # md5 for solutions is generated during competition unpacking
    md5 = models.CharField(max_length=32, null=True, blank=True)

    def __str__(self):
        return f"Solution - {self.name} - ({self.id})"
