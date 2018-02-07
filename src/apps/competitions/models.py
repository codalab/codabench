from django.conf import settings
from django.db import models

from src.utils.data import PathWrapper
# from .tasks import score_submission
from competitions import tasks


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
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    NONE = "NONE"
    SUBMITTED = "SUBMITTED"
    SUBMITTING = "SUBMITTING"

    MONTH_CHOICES = (
        (FINISHED, "Finished"),
        (FAILED, "Failed"),
        (NONE, "None"),
        # ....
        (SUBMITTED, "Submitted"),
        (SUBMITTING, "Submitting"),
    )

    description = models.CharField(max_length=240, default="", blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False, related_name='submission', on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=128, default=NONE, null=False, blank=False)
    # phase = models.ForeignKey(Phase, related_name='submissions', on_delete=models.CASCADE)
    appear_on_leaderboards = models.BooleanField(default=False)

    # Experimental
    name = models.CharField(max_length=120, default="", null=True, blank=True)
    description = models.CharField(max_length=120, default="", null=True, blank=True)
    score = models.IntegerField(default=None, null=True, blank=True)
    participant = models.ForeignKey('CompetitionParticipant', related_name='submissions', on_delete=models.CASCADE,
                                    null=True, blank=True)
    zip_file = models.FileField(upload_to=PathWrapper('submissions'), null=True, blank=True)
    created_when = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)

    # uber experimental
    track = models.IntegerField(default=1)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        super(Submission, self).save()

        if not self.score:
            tasks.score_submission.delay(self.pk)


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
