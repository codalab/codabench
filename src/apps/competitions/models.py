import uuid

from django.conf import settings
from django.db import models

from utils.data import PathWrapper
# from .tasks import score_submission
from competitions import compute_worker


class Competition(models.Model):
    # TODO: Check null and blank attributes
    title = models.CharField(max_length=256)
    logo = models.ImageField(upload_to=PathWrapper('logos'), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="competitions")
    created_when = models.DateTimeField(auto_now_add=True)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="collaborations", blank=True)

    def __str__(self):
        return "competition-{0}-{1}".format(self.title, self.pk)


class Phase(models.Model):
    # TODO: Check null and blank attributes
    competition = models.ForeignKey(Competition, related_name='phases', on_delete=models.CASCADE, null=True, blank=True)
    index = models.PositiveIntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)

    # These related names are all garbage. Had to do it this way just to prevent clashes...
    input_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="input_datas")
    reference_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="reference_datas")
    scoring_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="scoring_programs")
    ingestion_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="ingestion_programs")
    public_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="public_datas")
    starting_kit = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="starting_kits")

    def __str__(self):
        return self.name


class Submission(models.Model):
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    SUBMITTED = "SUBMITTED"
    SUBMITTING = "SUBMITTING"
    PREDICTING = "PREDICTING"
    SCORING = "SCORING"

    # MONTH_CHOICES = (
    #     (FINISHED, "Finished"),
    #     (FAILED, "Failed"),
    #     (NONE, "None"),
    #     # ....
    #     (SUBMITTED, "Submitted"),
    #     (SUBMITTING, "Submitting"),
    # )

    description = models.CharField(max_length=240, default="", blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='submission', on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=128, default=SUBMITTED, null=False, blank=False)
    phase = models.ForeignKey(Phase, related_name='submissions', on_delete=models.CASCADE)
    secret = models.UUIDField(default=uuid.uuid4, blank=True)
    appear_on_leaderboards = models.BooleanField(default=False)

    # Experimental
    name = models.CharField(max_length=120, default="", null=True, blank=True)
    score = models.IntegerField(default=None, null=True, blank=True)
    participant = models.ForeignKey('CompetitionParticipant', related_name='submissions', on_delete=models.CASCADE,
                                    null=True, blank=True)
    zip_file = models.FileField(upload_to=PathWrapper('submissions'), null=True, blank=True)
    stdout_file = models.FileField(upload_to=PathWrapper('submissions_stdout'), null=True, blank=True)
    stderr_file = models.FileField(upload_to=PathWrapper('submissions_stderr'), null=True, blank=True)
    output_file = models.FileField(upload_to=PathWrapper('submissions_output'), null=True, blank=True)
    scoring_stdout_file = models.FileField(upload_to=PathWrapper('submissions_scoring_stdout'), null=True, blank=True)
    scoring_stderr_file = models.FileField(upload_to=PathWrapper('submissions_scoring_stderr'), null=True, blank=True)
    scoring_output_file = models.FileField(upload_to=PathWrapper('submissions_scoring_output'), null=True, blank=True)
    created_when = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)

    # uber experimental
    track = models.IntegerField(default=1)

    # def save(self, force_insert=False, force_update=False, using=None,
    #          update_fields=None):
    #
    #     super(Submission, self).save()
    #
    #     if not self.score:
    #         if self.phase:
    #             if self.phase.scoring_program:
    #                 tasks.score_submission.delay(self.pk, self.phase.pk)
    #         tasks.score_submission_lazy.delay(self.pk)

    def change_status(self, new_status):
        # Available statuses:
        #     Submitting
        #     Submitted
        #     Predicting
        #     Scoring
        #     Finished OR Failed
        #
        # If status goes to "Scoring" then we should kick off the "Score" task
        if new_status == Submission.SCORING:
            self._score()

    def evaluate(self):
        """Helper function to make things a bit more clear -- this is how we start processing a submission,
        with a prediction. Scoring is kicked off after status is changed to 'Scoring'"""
        self._predict()

    def _predict(self):
        # TODO: Sign these URLs and stdout/stderr/output
        ingestion_program = self.phase.ingestion_program.data_file.name if self.phase.ingestion_program else None
        input_data = self.phase.input_data.data_file.name if self.phase.input_data else None
        compute_worker.predict.delay(
            self.pk,
            self.secret,
            self.zip_file.name,
            ingestion_program,
            input_data,
            self.stdout_file.name,
            self.stderr_file.name,
            self.output_file.name,
        )

    def _score(self):
        # TODO: Sign these URLs and stdout/stderr/output
        reference_data = self.phase.reference_data.data_file.name if self.phase.reference_data else None
        compute_worker.score.delay(
            self.pk,
            self.secret,
            self.phase.scoring_program.data_file.name,
            reference_data,
            self.stdout_file.name,
            self.stderr_file.name,
            self.output_file.name,
        )


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
