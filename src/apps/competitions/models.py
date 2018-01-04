from django.conf import settings
from django.db import models


class Competition(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_when = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=256)

    def __str__(self):
        return "competition-{0}-{1}".format(self.title, self.pk)


class Phase(models.Model):
    competition = models.ForeignKey(Competition, related_name='phases')


class Submission(models.Model):
    phase = models.ForeignKey(Phase, related_name='submissions')


class CompetitionParticipant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False, blank=False, related_name='participant')
    competition = models.OneToOneField(Competition, related_name='participants')
