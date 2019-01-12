import uuid

from django.conf import settings
from django.db import models


class Task(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    key = models.UUIDField(default=uuid.uuid4, blank=True, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)

    # Data pieces
    input_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_input_datas")
    reference_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_reference_datas")
    scoring_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_scoring_programs")
    ingestion_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_ingestion_programs")
    #solution = models.ForeignKey('tasks.Solution', on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")

    def __str__(self):
        return f"task-{self.name}-{self.id}"


class Solution(models.Model):
    key = models.UUIDField(default=uuid.uuid4, blank=True)
    tasks = models.ManyToManyField(Task, related_name="solutions")
    data = models.ForeignKey('datasets.Data', null=True, blank=True, on_delete=models.SET_NULL)
