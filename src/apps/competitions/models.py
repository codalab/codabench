import logging
import uuid
from django.conf import settings
from django.db import models
from django.utils.timezone import now

from chahub.models import ChaHubSaveMixin
from utils.data import PathWrapper
from utils.storage import BundleStorage

logger = logging.getLogger()


class Competition(ChaHubSaveMixin, models.Model):
    title = models.CharField(max_length=256)
    logo = models.ImageField(upload_to=PathWrapper('logos'), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="competitions")
    created_when = models.DateTimeField(default=now)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="collaborations", blank=True)
    published = models.BooleanField(default=False)
    secret_key = models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True)
    is_migrating = models.BooleanField(default=False)

    def __str__(self):
        return f"competition-{self.title}-{self.pk}"

    @property
    def bundle_dataset(self):
        return CompetitionCreationTaskStatus.objects.get(resulting_competition=self).dataset

    def apply_phase_migration(self, current_phase, next_phase):
        '''
        Does the actual migrating of submissions from current_phase to next_phase

        :param current_phase: The phase object to transfer submissions from
        :param next_phase: The new phase object we are entering
        '''
        logger.info(f"Checking for submissions that may still be running competition pk={self.pk}")
        status_list = [Submission.CANCELLED, Submission.FINISHED, Submission.FAILED, Submission.NONE]

        if current_phase.submissions.exclude(status__in=status_list).exists():
            logger.info(f"Some submissions still marked as processing for competition pk={self.pk}")
            self.is_migrating_delayed = True
            self.save()
            return

        logger.info(f"No submissions running for competition pk={self.pk}")
        logger.info(
            f"Doing phase migration on competition pk={self.pk} from phase: {current_phase.index} to phase: {next_phase.index}")

        self.is_migrating = True
        self.save()

        submissions = Submission.objects.filter(phase=current_phase, is_migrated=False, parent__isnull=True)

        for submission in submissions:
            new_submission = Submission(
                created_by_migration=current_phase,
                participant=submission.participant,
                phase=next_phase,
                owner=submission.owner,
                data=submission.data,
            )
            new_submission.save(ignore_submission_limit=True)
            new_submission.start()

            submission.is_migrated = True
            submission.save()

        # To check for submissions being migrated, does not allow to enter new submission
        current_phase.has_been_migrated = True
        current_phase.save()

        self.is_migrating_delayed = False
        self.save()

    def get_chahub_endpoint(self):
        return "competitions/"

    def get_chahub_data(self):
        data = {
            'created_by': self.created_by.username,
            'creator_id': self.created_by.pk,
            'created_when': self.created_when.isoformat(),
            'title': self.title,
            # TODO: get URL
            'url': 'https://www.google.com/',
            'remote_id': self.pk,
            'published': self.published
        }
        if self.logo:
            data['logo_url'] = self.logo.url
            data['logo'] = self.logo.url

        chahub_id = self.created_by.chahub_uid
        if chahub_id:
            data['user'] = chahub_id
        return [data]

    def get_chahub_is_valid(self):
        return self.published


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
    auto_migrate_to_this_phase = models.BooleanField(default=False)
    has_been_migrated = models.BooleanField(default=False)

    has_max_submissions = models.BooleanField(default=False)
    max_submissions_per_day = models.PositiveIntegerField(null=True, blank=True)
    max_submissions_per_person = models.PositiveIntegerField(null=True, blank=True)

    tasks = models.ManyToManyField('tasks.Task', blank=True, related_name="phases")

    class Meta:
        ordering = ('index',)

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

    @property
    def is_active(self):
        """ Returns true when this phase of the competition is on-going. """
        if not self.end:
            return True
        else:
            return self.start < now() < self.end

    def check_future_phase_submissions(self):
        """
        Checks for if we need to migrate current phase submissions to next phase.
        """
        current_phase = self.competition.phases.get(index=self.index - 1)
        next_phase = self

        # Check for next phase and see if it has auto_migration enabled
        try:
            if not current_phase.has_been_migrated:
                logger.info(
                    f"Checking for needed migrations on competition pk={self.competition.pk}, "
                    f"current phase: {current_phase.index}, next phase: {next_phase.index}")
                self.competition.apply_phase_migration(current_phase, next_phase)

        except next_phase.DoesNotExist:
            logger.info(f"This competition is missing the next phase to migrate to.")
        except current_phase.DoesNotExist:
            logger.info(f"This competition is missing the previous phase to migrate from.")


class SubmissionDetails(models.Model):
    DETAILED_OUTPUT_NAMES_PREDICTION = [
        "prediction_stdout",
        "prediction_stderr",
        "prediction_ingestion_stdout",
        "prediction_ingestion_stderr",
    ]
    DETAILED_OUTPUT_NAMES_SCORING = [
        "scoring_stdout",
        "scoring_stderr",
        "scoring_ingestion_stdout",
        "scoring_ingestion_stderr",
    ]
    name = models.CharField(max_length=50)
    data_file = models.FileField(upload_to=PathWrapper('submission_details'), storage=BundleStorage)
    submission = models.ForeignKey('Submission', on_delete=models.CASCADE, related_name='details')
    is_scoring = models.BooleanField(default=False)


class Submission(ChaHubSaveMixin, models.Model):
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
    # Add "scoring_result" ???

    secret = models.UUIDField(default=uuid.uuid4)
    task_id = models.UUIDField(null=True, blank=True)
    leaderboard = models.ForeignKey("leaderboards.Leaderboard", on_delete=models.CASCADE, related_name="submissions",
                                    null=True, blank=True)

    # Experimental
    name = models.CharField(max_length=120, default="", null=True, blank=True)
    score = models.DecimalField(max_digits=20, decimal_places=10, default=None, null=True, blank=True)
    participant = models.ForeignKey('CompetitionParticipant', related_name='submissions', on_delete=models.CASCADE,
                                    null=True, blank=True)
    created_when = models.DateTimeField(default=now)
    is_public = models.BooleanField(default=False)
    is_migrated = models.BooleanField(default=False)
    created_by_migration = models.ForeignKey(Phase, related_name='migrated_submissions', on_delete=models.CASCADE, null=True,
                                             blank=True)

    scores = models.ManyToManyField('leaderboards.SubmissionScore', related_name='submissions')
    # TODO: Maybe a field named 'ignored_submission_limits' so we can see which submissions were manually submitted past ignored submission limits and not count them against users

    # uber experimental
    # track = models.IntegerField(default=1)

    ignore_total = models.BooleanField(default=False)
    has_children = models.BooleanField(default=False)
    parent = models.ForeignKey('Submission', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    class Meta:
        unique_together = ('owner', 'leaderboard')

    def __str__(self):
        return f"{self.phase.competition.title} submission PK={self.pk} by {self.owner.username}"

    def delete(self, **kwargs):
        # Also clean up details on delete
        self.details.all().delete()
        super().delete(**kwargs)

    def save(self, ignore_submission_limit=False, **kwargs):
        created = not self.pk
        if created and not ignore_submission_limit:
            can_make_submission, reason_why_not = self.phase.can_user_make_submissions(self.owner)
            if not can_make_submission:
                raise PermissionError(reason_why_not)

        super().save(**kwargs)

    def start(self):
        from .tasks import run_submission
        run_submission.apply_async((self.pk,))

    def re_run(self):
        sub = Submission(owner=self.owner, phase=self.phase, data=self.data)
        sub.save(ignore_submission_limit=True)
        sub.start()

    def cancel(self):
        from celery_config import app
        if self.status not in [Submission.CANCELLED, Submission.FAILED, Submission.FINISHED]:
            app.control.revoke(self.task_id, terminate=True)
            self.status = Submission.CANCELLED
            self.save()
            return True
        return False

    def check_children(self):
        done_statuses = [self.FINISHED, self.FAILED, self.CANCELLED]
        if all([status in done_statuses for status in self.children.values_list('status', flat=True)]):
            self.status = 'Finished'
            self.save()

    def get_chahub_endpoint(self):
        return "submissions/"

    def get_chahub_data(self):
        data = {
            "remote_id": self.id,
            "competition": self.phase.competition_id,
            "phase_index": self.phase.index,
            "participant": self.participant.user.username,
            "submitted_at": self.created_when.isoformat(),
        }
        chahub_id = self.owner.chahub_uid
        if chahub_id:
            data['user'] = chahub_id
        return [data]

    def get_chahub_is_valid(self):
        return self.status == self.FINISHED and self.is_public and self.phase.competition.published


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
