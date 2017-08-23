from django.db import models


class Competition(models.Model):
    title = models.CharField(max_length=256)


class Phase(models.Model):
    competition = models.ForeignKey(Competition, related_name='phases')


class Submission(models.Model):
    phase = models.ForeignKey(Phase, related_name='submissions')
