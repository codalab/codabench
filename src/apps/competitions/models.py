from django.conf import settings
from django.db import models

from src.utils.data import PathWrapper


class Competition(models.Model):
    title = models.CharField(max_length=256)
    logo = models.ImageField(upload_to=PathWrapper('logos'), null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="competitions")
    created_when = models.DateTimeField(auto_now_add=True)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="collaborations")

    def __str__(self):
        return "competition-{0}-{1}".format(self.title, self.pk)


class Phase(models.Model):
    competition = models.ForeignKey(Competition, related_name='phases', on_delete=models.CASCADE)
    index = models.PositiveIntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)

    # These related names are all garbage. Had to do it this way just to prevent clashes...
    input_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="input_datas")
    reference_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="reference_datas")
    scoring_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, related_name="scoring_programs")
    ingestion_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="ingestion_programs")
    public_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="public_datas")
    starting_kit = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="starting_kits")


class Submission(models.Model):
    phase = models.ForeignKey(Phase, related_name='submissions', on_delete=models.CASCADE)
    appear_on_leaderboards = models.BooleanField(default=False)

    # Experimental
    score = models.IntegerField(default=0, null=True, blank=True)
    participant = models.ForeignKey('CompetitionParticipant', related_name='submissions', on_delete=models.CASCADE,
                                    null=True, blank=True)
    zip_file = models.FileField(upload_to=PathWrapper('submissions'), null=True, blank=True)


class CompetitionParticipant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False, blank=False, related_name='participant',
                                on_delete=models.DO_NOTHING)
    competition = models.OneToOneField(Competition, related_name='participants', on_delete=models.CASCADE)


class Page(models.Model):
    competition = models.ForeignKey(Competition, related_name='pages', on_delete=models.CASCADE)
    title = models.TextField(max_length=255)
    content = models.TextField()
    index = models.PositiveIntegerField()


# class Leaderboard(models.Model):
#     pass
#
#
# class Leaderboard


"""
What if the competition creator adds/removes leaderboards?

what if the competition creator adds/removes columns?
"""
