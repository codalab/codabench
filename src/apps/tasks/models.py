import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from chahub.models import ChaHubSaveMixin


class Task(ChaHubSaveMixin, models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    key = models.UUIDField(default=uuid.uuid4, blank=True, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_when = models.DateTimeField(default=now)
    is_public = models.BooleanField(default=False)

    ingestion_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_ingestion_programs")
    input_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_input_datas")
    ingestion_only_during_scoring = models.BooleanField(default=False)

    reference_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_reference_datas")
    scoring_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="task_scoring_programs")

    def __str__(self):
        return f"Task - {self.name} - ({self.id})"

    @property
    def _validated(self):
        return self.solutions.filter(md5__in=self.phases.values_list('submissions__md5', flat=True)).exists()

    @staticmethod
    def get_chahub_endpoint():
        return 'tasks/'

    def get_whitelist(self):
        return [
            'remote_id',
            'is_public',
            'solutions',
            'ingestion_program',
            'input_data',
            'reference_data',
            'scoring_program',
        ]

    def get_chahub_data(self, include_solutions=True):
        data = {
            'remote_id': self.pk,
            'created_by': self.created_by.username,
            'creator_id': self.created_by.pk,
            'created_when': self.created_when.isoformat(),
            'name': self.name,
            'description': self.description,
            'key': str(self.key),
            'is_public': self.is_public,
            'ingestion_program': self.ingestion_program.get_chahub_data() if self.ingestion_program else None,
            'input_data': self.input_data.get_chahub_data() if self.input_data else None,
            'ingestion_only_during_scoring': self.ingestion_only_during_scoring,
            'reference_data': self.reference_data.get_chahub_data() if self.reference_data else None,
            'scoring_program': self.scoring_program.get_chahub_data() if self.scoring_program else None,
        }
        if include_solutions:
            data['solutions'] = [solution.get_chahub_data(include_tasks=False) for solution in self.solutions.all()]
        return self.clean_private_data(data)

    def save(self, *args, **kwargs):
        self.is_public = self.is_public and self._validated
        return super().save(*args, **kwargs)


class Solution(ChaHubSaveMixin, models.Model):
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

    @staticmethod
    def get_chahub_endpoint():
        return 'solutions/'

    def get_whitelist(self):
        return [
            'remote_id',
            'is_public',
            'data',
            'tasks'
        ]

    def get_chahub_data(self, include_tasks=True):
        data = {
            'remote_id': self.pk,
            'name': self.name,
            'description': self.description,
            'key': str(self.key),
            'data': self.data.get_chahub_data(),  # Todo: Make sure data is public if solution is public
        }
        if include_tasks:
            data['tasks'] = [task.get_chahub_data(include_solutions=False) for task in self.tasks.all()]
        return self.clean_private_data(data)
