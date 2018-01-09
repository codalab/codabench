from django.conf import settings
from django.db import models


class Competition(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_when = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=256)

    def __str__(self):
        return "competition-{0}-{1}".format(self.title, self.pk)


class Phase(models.Model):
    competition = models.ForeignKey(Competition, related_name='phases', on_delete=models.DO_NOTHING)


class Submission(models.Model):
    phase = models.ForeignKey(Phase, related_name='submissions', on_delete=models.DO_NOTHING)


class CompetitionParticipant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False, blank=False, related_name='participant',
                                on_delete=models.DO_NOTHING)
    competition = models.OneToOneField(Competition, related_name='participants', on_delete=models.DO_NOTHING)
