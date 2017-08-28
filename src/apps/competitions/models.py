from django.conf import settings
from django.db import models


class Competition(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_when = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=256)


class Phase(models.Model):
    competition = models.ForeignKey(Competition, related_name='phases')


class Submission(models.Model):
    phase = models.ForeignKey(Phase, related_name='submissions')
