import uuid
from django.conf import settings
from django.db import models
from django.utils.timezone import now

from utils.data import PathWrapper
from utils.storage import BundleStorage


class Competition(models.Model):
    title = models.CharField(max_length=256)
    logo = models.ImageField(upload_to=PathWrapper('logos'), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="competitions")
    created_when = models.DateTimeField(default=now)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="collaborations", blank=True)
    published = models.BooleanField(default=False)
    secret_key = models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True)

    def __str__(self):
        return "competition-{0}-{1}".format(self.title, self.pk)

    @property
    def bundle_dataset(self):
        return CompetitionCreationTaskStatus.objects.get(resulting_competition=self).dataset


class CompetitionCreationTaskStatus(models.Model):
    STARTING = "Starting"
    FINISHED = "Finished"
    FAILED = "Failed"

    STATUS_CHOICES = (
        (STARTING, "None"),
        (FINISHED, "Finished"),
        (FAILED, "Failed"),
    )

    dataset = models.ForeignKey('datasets.Data', on_delete=models.CASCADE, related_name="competition_bundles")
    status = models.TextField(choices=STATUS_CHOICES, null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    # The resulting competition is only made on success
    resulting_competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Comp uploaded by {self.dataset.created_by} - {self.status}"


class Phase(models.Model):
    PREVIOUS = "Previous"
    CURRENT = "Current"
    NEXT = "Next"
    FINAL = "Final"

    STATUS_CHOICES = (
        (PREVIOUS, "Previous"),
        (CURRENT, "Current"),
        (NEXT, "Next"),
        (FINAL, "Final"),
    )

    status = models.TextField(choices=STATUS_CHOICES, null=True, blank=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True, related_name='phases')
    index = models.PositiveIntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    execution_time_limit = models.PositiveIntegerField(default=60 * 10)

    has_max_submissions = models.BooleanField(default=False)
    max_submissions_per_day = models.PositiveIntegerField(null=True, blank=True)
    max_submissions_per_person = models.PositiveIntegerField(null=True, blank=True)

    # These related names are all garbage. Had to do it this way just to prevent clashes...
    input_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_input_datas")
    reference_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_reference_datas")
    scoring_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_scoring_programs")
    ingestion_program = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_ingestion_programs")
    public_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_public_datas")
    starting_kit = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_starting_kits")

    # Task and Solution fields
    tasks = models.ManyToManyField('tasks.Task', blank=True, related_name="phases")
    solutions = models.ManyToManyField('tasks.Solution', blank=True, related_name="phases")
    is_task_and_solution = models.BooleanField(default=False)

    def __str__(self):
        return f"phase - {self.name} - For comp: {self.competition.title} - ({self.id})"

    def can_user_make_submissions(self, user):
        """Takes a user and checks how many submissions they've made vs the max.

        Returns:
            (can_make_submissions, reason_if_not)
        """
        if not self.has_max_submissions:
            return True, None

        qs = self.submissions.filter(owner=user).exclude(status='Failed')
        total_submission_count = qs.count()
        daily_submission_count = qs.filter(created_when__day=now().day).count()

        if self.max_submissions_per_day:
            if daily_submission_count >= self.max_submissions_per_day:
                return False, 'Reached maximum allowed submissions for today for this phase'
        if self.max_submissions_per_person:
            if total_submission_count >= self.max_submissions_per_person:
                return False, 'Reached maximum allowed submissions for this phase'
        return True, None


class SubmissionDetails(models.Model):
    DETAILED_OUTPUT_NAMES = [
        "stdout",
        "stderr",
        "ingestion_stdout",
        "ingestion_stderr",
    ]
    name = models.CharField(max_length=50)
    data_file = models.FileField(upload_to=PathWrapper('submission_details'), storage=BundleStorage)
    submission = models.ForeignKey('Submission', on_delete=models.CASCADE, related_name='details')


class Submission(models.Model):
    NONE = "None"
    SUBMITTING = "Submitting"
    SUBMITTED = "Submitted"
    PREPARING = "Preparing"
    RUNNING = "Running"
    SCORING = "Scoring"
    CANCELLED = "Cancelled"
    FINISHED = "Finished"
    FAILED = "Failed"

    STATUS_CHOICES = (
        (NONE, "None"),
        (SUBMITTING, "Submitting"),
        (SUBMITTED, "Submitted"),
        (PREPARING, "Preparing"),
        (RUNNING, "Running"),
        (SCORING, "Scoring"),
        (CANCELLED, "Cancelled"),
        (FINISHED, "Finished"),
        (FAILED, "Failed"),
    )

    description = models.CharField(max_length=240, default="", blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='submission', on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=128, choices=STATUS_CHOICES, default=SUBMITTING, null=False, blank=False)
    status_details = models.TextField(null=True, blank=True)
    phase = models.ForeignKey(Phase, related_name='submissions', on_delete=models.CASCADE)
    appear_on_leaderboards = models.BooleanField(default=False)
    data = models.ForeignKey("datasets.Data", on_delete=models.CASCADE)
    result = models.FileField(upload_to=PathWrapper('submission_result'), null=True, blank=True, storage=BundleStorage)
    secret = models.UUIDField(default=uuid.uuid4)
    task_id = models.UUIDField(null=True, blank=True)
    leaderboard = models.ForeignKey("leaderboards.Leaderboard", on_delete=models.CASCADE, related_name="submissions", null=True, blank=True)

    # Experimental
    name = models.CharField(max_length=120, default="", null=True, blank=True)
    score = models.DecimalField(max_digits=20, decimal_places=10, default=None, null=True, blank=True)
    participant = models.ForeignKey('CompetitionParticipant', related_name='submissions', on_delete=models.CASCADE,
                                    null=True, blank=True)
    created_when = models.DateTimeField(default=now)
    is_public = models.BooleanField(default=False)

    # TODO: Maybe a field named 'ignored_submission_limits' so we can see which submissions were manually submitted past ignored submission limits and not count them against users

    # uber experimental
    # track = models.IntegerField(default=1)

    class Meta:
        unique_together = ('owner', 'leaderboard')

    def __str__(self):
        return f"{self.phase.competition.title} submission PK={self.pk} by {self.owner.username}"

    def delete(self, **kwargs):
        # Also clean up details on delete
        self.details.delete()
        super().delete(**kwargs)

    def save(self, **kwargs):
        created = not self.pk
        if created:
            can_make_submission, reason_why_not = self.phase.can_user_make_submissions(self.owner)
            if not can_make_submission:
                raise PermissionError(reason_why_not)

        super().save(**kwargs)

    def start(self):
        from .tasks import run_submission
        run_submission.apply_async((self.pk,))

    def cancel(self):
        from celery_config import app
        app.control.revoke(self.task_id, terminate=True)

        self.status = Submission.CANCELLED
        self.save()


class CompetitionParticipant(models.Model):
    UNKNOWN = 'unknown'
    DENIED = 'denied'
    APPROVED = 'approved'
    PENDING = 'pending'

    STATUS_CHOICES = (
        (UNKNOWN, 'unknown'),
        (DENIED, 'denied'),
        (APPROVED, 'approved'),
        (PENDING, 'pending'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False, related_name='competitions_im_in',
                             on_delete=models.DO_NOTHING)
    competition = models.ForeignKey(Competition, related_name='participants', on_delete=models.CASCADE)
    status = models.CharField(max_length=128, choices=STATUS_CHOICES, null=False, blank=False, default=UNKNOWN)
    # TODO:// is this the right logic for status?
    reason = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"({self.id}) - User: {self.user.username} in Competition: {self.competition.title}"


class Page(models.Model):
    competition = models.ForeignKey(Competition, related_name='pages', on_delete=models.CASCADE)
    title = models.TextField(max_length=255)
    content = models.TextField()
    index = models.PositiveIntegerField()


class CompetitionDump(models.Model):
    STARTING = "Starting"
    FINISHED = "Finished"
    FAILED = "Failed"

    STATUS_CHOICES = (
        (STARTING, "None"),
        (FINISHED, "Finished"),
        (FAILED, "Failed"),
    )

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='dumps')
    dataset = models.ForeignKey('datasets.Data', on_delete=models.CASCADE, related_name="competition_dump_file")
    status = models.TextField(choices=STATUS_CHOICES, null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    # The resulting competition is only made on success
    # resulting_competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Comp dump created by {self.dataset.created_by} - {self.status}"


# class Leaderboard(models.Model):
#     pass
#
#
# class Leaderboard


"""
What if the competition creator adds/removes leaderboards?

what if the competition creator adds/removes columns?
"""
