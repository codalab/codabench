import uuid

from django.conf import settings
from django.db import models


class TaskDescriptionMixin(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    key = models.UUIDField(default=uuid.uuid4, blank=True, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Task(TaskDescriptionMixin):
    is_public = models.BooleanField(default=False)

    ingestion_module = models.ForeignKey('tasks.IngestionModule', null=True, blank=True, on_delete=models.SET_NULL)
    scoring_module = models.ForeignKey('tasks.ScoringModule', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Task - {self.name} - ({self.id})"


class Solution(models.Model):
    key = models.UUIDField(default=uuid.uuid4, blank=True, unique=True)
    tasks = models.ManyToManyField(Task, related_name="solutions")
    data = models.ForeignKey('datasets.Data', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Solution - {self.data.name} - ({self.id})"


class IngestionModule(TaskDescriptionMixin):

    # Data Pieces
    ingestion_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_ingestion_programs")
    input_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_input_datas")

    only_during_scoring = models.BooleanField(default=False)

    def __str__(self):
        return f"Ingestion Module - {self.name} - ({self.id})"


class ScoringModule(TaskDescriptionMixin):

    # Data Pieces
    reference_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_reference_datas")
    scoring_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_scoring_programs")

    def __str__(self):
        return f"Scoring Module - {self.name} - ({self.id})"
