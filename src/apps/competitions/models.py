import uuid
import os
import io

import botocore.exceptions
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.timezone import now
from decimal import Decimal

from celery_config import app, app_for_vhost
from leaderboards.models import SubmissionScore
from profiles.models import User, Organization
from utils.data import PathWrapper
from utils.storage import BundleStorage
from PIL import Image

from tasks.models import Task

import logging
logger = logging.getLogger(__name__)


class Competition(models.Model):
    COMPETITION = "competition"
    BENCHMARK = "benchmark"

    COMPETITION_TYPE = (
        (COMPETITION, "competition"),
        (BENCHMARK, "benchmark"),
    )

    title = models.CharField(max_length=256)
    logo = models.ImageField(upload_to=PathWrapper('logos'), null=True, blank=True)
    logo_icon = models.ImageField(upload_to=PathWrapper('logos', manual_override=True), null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="competitions")
    created_when = models.DateTimeField(default=now)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="collaborations", blank=True)
    published = models.BooleanField(default=False)
    secret_key = models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True)
    registration_auto_approve = models.BooleanField(default=False)
    terms = models.TextField(null=True, blank=True)
    is_migrating = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    docker_image = models.CharField(max_length=128, default="codalab/codalab-legacy:py37")
    enable_detailed_results = models.BooleanField(default=False)
    # If true, show detailed results in submission panel
    show_detailed_results_in_submission_panel = models.BooleanField(default=True)
    # If true, show detailed results in leaderboard
    show_detailed_results_in_leaderboard = models.BooleanField(default=True)
    make_programs_available = models.BooleanField(default=False)
    make_input_data_available = models.BooleanField(default=False)

    queue = models.ForeignKey('queues.Queue', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='competitions')

    allow_robot_submissions = models.BooleanField(default=False)
    # we use filed type to distinguish 'competition' and 'benchmark'
    competition_type = models.CharField(max_length=128, choices=COMPETITION_TYPE, default=COMPETITION)

    fact_sheet = models.JSONField(blank=True, null=True, max_length=4096, default=None)

    contact_email = models.EmailField(max_length=256, null=True, blank=True)
    reward = models.CharField(max_length=256, null=True, blank=True)
    report = models.CharField(max_length=256, null=True, blank=True)

    # if true, submissions are auto-run when submitted
    # if false, submissions run will be intiiated by organizer
    auto_run_submissions = models.BooleanField(default=True)

    # If true, participants see the make their submissions public
    can_participants_make_submissions_public = models.BooleanField(default=True)

    # If true, competition is featured and may show up on the home page
    is_featured = models.BooleanField(default=False)

    # Count of submissions for this competition
    submissions_count = models.PositiveIntegerField(default=0)

    # Count of participants in this competition (default = 1 because competition creator is also a participant)
    participants_count = models.PositiveIntegerField(default=1)

    # If true, forum is enabled (default=True)
    forum_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"competition-{self.title}-{self.pk}-{self.competition_type}"

    @property
    def bundle_dataset(self):
        try:
            bundle = CompetitionCreationTaskStatus.objects.get(resulting_competition=self).dataset
        except CompetitionCreationTaskStatus.DoesNotExist:
            bundle = None
        return bundle

    @property
    def all_organizers(self):
        return [self.created_by] + list(self.collaborators.all())

    def user_has_admin_permission(self, user):
        if isinstance(user, int):
            try:
                user = User.objects.get(id=user)
            except User.DoesNotExist:
                return False
        if user.is_staff or user.is_superuser:
            return True
        else:
            return user in self.all_organizers

    def apply_phase_migration(self, current_phase, next_phase, force_migration=False):
        """
        Does the actual migrating of submissions from current_phase to next_phase

        :param force_migration: overrides check for currently running submissions
        :param current_phase: The phase object to transfer submissions from
        :param next_phase: The new phase object we are entering
        """

        if not force_migration:
            logger.info(f"Checking for submissions that may still be running competition pk={self.pk}")
            status_list = [Submission.CANCELLED, Submission.FINISHED, Submission.FAILED, Submission.NONE]
            if current_phase.submissions.exclude(status__in=status_list).exists():
                logger.info(f"Some submissions still marked as processing for competition pk={self.pk}")
                self.is_migrating_delayed = True
                self.save()
                return
            else:
                logger.info(f"No submissions running for competition pk={self.pk}")

        logger.info(f"Doing phase migration on competition pk={self.pk} "
                    f"from phase: {current_phase.index} to phase: {next_phase.index}")

        self.is_migrating = True
        self.save()

        # Get submissions of current phase with finished status and which are on leaderboard
        submissions = Submission.objects.filter(
            phase=current_phase,
            is_migrated=False,
            parent__isnull=True,
            leaderboard__isnull=False,
            status=Submission.FINISHED
        )

        for submission in submissions:
            new_submission = Submission(
                created_by_migration=current_phase,
                participant=submission.participant,
                phase=next_phase,
                task=submission.task,
                owner=submission.owner,
                data=submission.data,
            )
            new_submission.save(ignore_submission_limit=True)
            new_submission.start()

            submission.is_migrated = True
            submission.save()

        # To check for submissions being migrated, does not allow to enter new submission
        next_phase.has_been_migrated = True
        next_phase.save()

        self.is_migrating_delayed = False
        self.save()

    def update_phase_statuses(self):
        current_phase = None
        for phase in self.phases.all():
            if phase.end is not None and phase.start < now() < phase.end:
                current_phase = phase
            elif phase.end is None:
                current_phase = phase

        if current_phase:
            current_index = current_phase.index
            previous_index = current_index - 1 if current_index >= 1 else None
            next_index = current_index + 1 if current_index < len(self.phases.all()) - 1 else None
        else:
            current_index = None

            next_phase = self.phases.filter(end__gt=now()).order_by('index').first()
            if next_phase:
                next_index = next_phase.index
                previous_index = next_index - 1 if next_index >= 1 else None
            else:
                next_index = None
                previous_index = None

        if current_index is not None:
            self.phases.filter(index=current_index).update(status=Phase.CURRENT)
        if next_index is not None:
            self.phases.filter(index=next_index).update(status=Phase.NEXT)
        if previous_index is not None:
            self.phases.filter(index=previous_index).update(status=Phase.PREVIOUS)

    def get_absolute_url(self):
        return reverse('competitions:detail', kwargs={'pk': self.pk})

    def make_logo_icon(self):
        if self.logo:
            # Read the content of the logo file
            self.logo.name
            self.logo_icon
            icon_dirname_only = os.path.dirname(self.logo.name)  # Get just the path
            icon_basename_only = os.path.basename(self.logo.name)  # Get just the filename
            file_name = os.path.splitext(icon_basename_only)[0]
            ext = os.path.splitext(icon_basename_only)[1]
            new_path = os.path.join(icon_dirname_only, f"{file_name}_icon{ext}")
            logo_content = self.logo.read()
            original_logo = Image.open(io.BytesIO(logo_content))
            # Resize the image to a smaller size for logo_icon
            width, height = original_logo.size
            new_width = 100  # Specify the desired width for the logo_icon
            new_height = int((new_width / width) * height)
            resized_logo = original_logo.resize((new_width, new_height))
            # Create a BytesIO object to save the resized image
            icon_content = io.BytesIO()
            resized_logo.save(icon_content, format='PNG')
            # Save the resized logo as logo_icon
            self.logo_icon.save(new_path, ContentFile(icon_content.getvalue()), save=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.logo:
            pass
        elif not self.logo_icon:
            self.make_logo_icon()
            self.save()
        elif os.path.dirname(self.logo.name) != os.path.dirname(self.logo_icon.name):
            self.make_logo_icon()
            self.save()
        to_create = User.objects.filter(
            Q(id=self.created_by_id) | Q(id__in=self.collaborators.all().values_list('id', flat=True))
        ).exclude(id__in=self.participants.values_list('user_id', flat=True)).distinct()
        new_participants = []
        for user in to_create:
            new_participants.append(CompetitionParticipant(user=user, competition=self, status='approved'))
        if new_participants:
            CompetitionParticipant.objects.bulk_create(new_participants)


class CompetitionCreationTaskStatus(models.Model):
    STARTING = "Starting"
    FINISHED = "Finished"
    FAILED = "Failed"

    STATUS_CHOICES = (
        (STARTING, "None"),
        (FINISHED, "Finished"),
        (FAILED, "Failed"),
    )

    dataset = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, related_name="competition_bundles")
    status = models.TextField(choices=STATUS_CHOICES, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='competition_creation_task_statuses',
    )

    # The resulting competition is only made on success
    resulting_competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True,
                                              related_name='creation_statuses')

    def __str__(self):
        return f"pk: {self.pk} ({self.status})"


class Phase(models.Model):
    PREVIOUS = "Previous"
    CURRENT = "Current"
    NEXT = "Next"
    FINAL = "Final"

    STATUS_CHOICES = (
        (PREVIOUS, "Previous"),
        (CURRENT, "Current"),
        (NEXT, "Next"),
    )

    status = models.TextField(choices=STATUS_CHOICES, null=True, blank=True)
    is_final_phase = models.BooleanField(default=False)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True, related_name='phases')
    index = models.PositiveIntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    execution_time_limit = models.PositiveIntegerField(default=60 * 10)
    auto_migrate_to_this_phase = models.BooleanField(default=False)
    has_been_migrated = models.BooleanField(default=False)
    hide_output = models.BooleanField(default=False)
    hide_prediction_output = models.BooleanField(default=False)
    hide_score_output = models.BooleanField(default=False)

    has_max_submissions = models.BooleanField(default=True)
    max_submissions_per_day = models.PositiveIntegerField(default=5, null=True, blank=True)
    max_submissions_per_person = models.PositiveIntegerField(default=100, null=True, blank=True)

    tasks = models.ManyToManyField('tasks.Task', blank=True, related_name='phases', through='PhaseTaskInstance')

    leaderboard = models.ForeignKey('leaderboards.Leaderboard', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="phases")

    public_data = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_public_data")
    starting_kit = models.ForeignKey('datasets.Data', on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_starting_kit")

    class Meta:
        ordering = ('index',)

    def __str__(self):
        return f"phase - {self.name} - For comp: {self.competition.title} - ({self.id})"

    @property
    def published(self):
        return self.competition.published

    def can_user_make_submissions(self, user):
        """Takes a user and checks how many submissions they've made vs the max.

        Returns:
            (can_make_submissions, reason_if_not)
        """
        if not self.has_max_submissions or (user.is_bot and self.competition.allow_robot_submissions):
            return True, None

        qs = self.submissions.filter(owner=user, parent__isnull=True).exclude(status='Failed')
        total_submission_count = qs.count()
        daily_submission_count = qs.filter(created_when__date=now().date()).count()

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
            if not next_phase.has_been_migrated:
                logger.info(
                    f"Checking for needed migrations on competition pk={self.competition.pk}, "
                    f"current phase: {current_phase.index}, next phase: {next_phase.index}")
                self.competition.apply_phase_migration(current_phase, next_phase)

        except next_phase.DoesNotExist:
            logger.error(f"This competition is missing the next phase to migrate to.")
        except current_phase.DoesNotExist:
            logger.error(f"This competition is missing the previous phase to migrate from.")


class PhaseTaskInstance(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="task_instances")
    order_index = models.PositiveIntegerField(default=999)

    class Meta:
        ordering = ["order_index", "task"]

    def __str__(self):
        return f'Task:{self.task.name}, Phase:{self.phase.name}, Order:{int(self.order_index)}'


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
    file_size = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # in Bytes
    submission = models.ForeignKey('Submission', on_delete=models.CASCADE, related_name='details')
    is_scoring = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.data_file and (not self.file_size or self.file_size == -1):
            try:
                # self.data_file.size returns bytes
                self.file_size = self.data_file.size
            except TypeError:
                # -1 indicates an error
                self.file_size = -1
            except botocore.exceptions.ClientError:
                # file might not exist in the storage
                logger.warning(f"The data_file of SubmissionDetails id={self.id} does not exist in the storage. data_file and file_size has been cleared")
                self.file_size = Decimal(0)
                self.data_file = None
        return super().save(*args, **kwargs)


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
    organization = models.ForeignKey(Organization, related_name='submissions', on_delete=models.DO_NOTHING, null=True)
    status = models.CharField(max_length=128, choices=STATUS_CHOICES, default=SUBMITTING, null=False, blank=False)
    status_details = models.TextField(null=True, blank=True)
    phase = models.ForeignKey(Phase, related_name='submissions', on_delete=models.CASCADE)
    appear_on_leaderboards = models.BooleanField(default=False)
    data = models.ForeignKey("datasets.Data", on_delete=models.SET_NULL, related_name='submission', null=True, blank=True)
    md5 = models.CharField(max_length=32, null=True, blank=True)

    prediction_result = models.FileField(upload_to=PathWrapper('prediction_result'), null=True, blank=True,
                                         storage=BundleStorage)
    scoring_result = models.FileField(upload_to=PathWrapper('scoring_result'), null=True, blank=True,
                                      storage=BundleStorage)
    detailed_result = models.FileField(upload_to=PathWrapper('detailed_result'), null=True, blank=True,
                                       storage=BundleStorage)

    prediction_result_file_size = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # in Bytes
    scoring_result_file_size = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # in Bytes
    detailed_result_file_size = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)  # in Bytes

    secret = models.UUIDField(default=uuid.uuid4)
    celery_task_id = models.UUIDField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions")
    leaderboard = models.ForeignKey("leaderboards.Leaderboard", on_delete=models.SET_NULL, related_name="submissions",
                                    null=True, blank=True)

    # Experimental
    name = models.CharField(max_length=120, default="", null=True, blank=True)
    participant = models.ForeignKey('CompetitionParticipant', related_name='submissions', on_delete=models.CASCADE,
                                    null=True, blank=True)
    created_when = models.DateTimeField(default=now)
    started_when = models.DateTimeField(null=True)
    is_public = models.BooleanField(default=False)
    is_specific_task_re_run = models.BooleanField(default=False)
    # Ingestion hostname
    ingestion_worker_hostname = models.CharField(max_length=255, blank=True, null=True)
    # Scoring hostname
    scoring_worker_hostname = models.CharField(max_length=255, blank=True, null=True)
    queue = models.ForeignKey('queues.Queue', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='submissions')
    is_migrated = models.BooleanField(default=False)
    created_by_migration = models.ForeignKey(Phase, related_name='migrated_submissions', on_delete=models.CASCADE,
                                             null=True,
                                             blank=True)

    scores = models.ManyToManyField('leaderboards.SubmissionScore', related_name='submissions')

    has_children = models.BooleanField(default=False)
    parent = models.ForeignKey('Submission', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    fact_sheet_answers = models.JSONField(null=True, blank=True, max_length=4096)

    # True when submission owner deletes a submission
    is_soft_deleted = models.BooleanField(default=False)
    # DataTime of when a submission is soft_deleted
    soft_deleted_when = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.phase.competition.title} submission PK={self.pk} by {self.owner.username}"

    def soft_delete(self):
        """
        Soft delete the submission: remove files but keep record in DB.
        Also deletes associated SubmissionDetails and cleans up storage.
        Also removes organization reference from the submission
        """

        # Remove related files from storage
        # 'save=False' prevents a database save, which is handled later after marking the submission as soft-deleted.
        self.prediction_result.delete(save=False)
        self.prediction_result_file_size = 0
        self.scoring_result.delete(save=False)
        self.scoring_result_file_size = 0
        self.detailed_result.delete(save=False)
        self.detailed_result_file_size = 0

        # Delete related SubmissionDetails files and records
        for detail in self.details.all():
            detail.data_file.delete(save=False)  # Delete file from storage
            detail.delete()  # Remove record from DB

        # Clear the data field if no other submissions are using it
        other_submissions_using_data = Submission.objects.filter(data=self.data).exclude(pk=self.pk).exists()
        if not other_submissions_using_data:
            self.data.delete()

        # Clear the data field for this submission
        self.data = None

        # Clear the organization field for this submission
        self.organization = None

        # Mark submission as deleted
        self.is_soft_deleted = True
        self.soft_deleted_when = now()
        self.save()

    def delete(self, **kwargs):

        # Check if any other submissions are using the same data
        other_submissions_using_data = Submission.objects.filter(data=self.data).exclude(pk=self.pk).exists()

        if not other_submissions_using_data:
            # If no other submissions are using the same data, delete it
            self.data.delete()

        # Also clean up details on delete
        self.details.all().delete()

        # Decrement the submissions_count for the competition on submission deletion
        # Fetching competition from the phase of this submission
        competition = self.phase.competition
        super().delete(**kwargs)
        # Ensure submissions_count stays non-negative
        if competition.submissions_count > 0:
            competition.submissions_count -= 1
            competition.save()

    def save(self, ignore_submission_limit=False, **kwargs):
        is_new = self.pk is None
        if is_new and not ignore_submission_limit:
            can_make_submission, reason_why_not = self.phase.can_user_make_submissions(self.owner)
            if not can_make_submission:
                raise PermissionError(reason_why_not)

        if self.status == Submission.RUNNING and not self.started_when:
            self.started_when = now()

        files_and_sizes_dict = {
            'prediction_result': 'prediction_result_file_size',
            'scoring_result': 'scoring_result_file_size',
            'detailed_result': 'detailed_result_file_size',
        }
        for file_path_attr, file_size_attr in files_and_sizes_dict.items():
            if getattr(self, file_path_attr) and (not getattr(self, file_size_attr) or getattr(self, file_size_attr) == -1):
                try:
                    # self.data_file.size returns bytes
                    setattr(self, file_size_attr, getattr(self, file_path_attr).size)
                except TypeError:
                    # -1 indicates an error
                    setattr(self, file_size_attr, Decimal(-1))
                except botocore.exceptions.ClientError:
                    # file might not exist in the storage
                    logger.warning(f"The {file_path_attr} of Submission id={self.id} does not exist in the storage. {file_path_attr} and {file_size_attr} has been cleared")
                    setattr(self, file_size_attr, Decimal(0))
                    setattr(self, file_path_attr, None)

        super().save(**kwargs)

        # Only increment when a submission is parent (do not count child submissions)
        if is_new and self.parent is None:
            # Increment the submissions_count for the competition
            self.phase.competition.submissions_count += 1
            self.phase.competition.save()

    def start(self, tasks=None):
        from .tasks import run_submission
        run_submission(self.pk, tasks=tasks)

    def run(self):
        # get tasks from the phase
        tasks = self.phase.tasks.all()
        # start submission providing the tasks
        self.start(tasks=tasks)
        return self

    def re_run(self, task=None):

        # task to use in the new submission
        new_submission_task = task or self.task

        # set is_specific_task_re_run
        is_specific_task_re_run = bool(task)

        flag_rerun_specific_task_or_has_no_children = False
        # Check if this submission needs to rerun on specific children or has no children
        if not self.has_children or is_specific_task_re_run:
            flag_rerun_specific_task_or_has_no_children = True

        # Check if task exists in case of specific task rerun or no children
        if flag_rerun_specific_task_or_has_no_children and new_submission_task is None:
            logger.error(f"Cannot rerun `{self}` because the task is None (deleted)")
            return None
        else:
            children_tasks = self.children.values_list('task', flat=True)
            if None in children_tasks:
                logger.error(f"Cannot rerun `{self}` because one or more children submission tasks are None (deleted)")
                return None

        # Create a new submission
        submission_arg_dict = {
            'owner': self.owner,
            'task': new_submission_task,
            'phase': self.phase,
            'data': self.data,
            'has_children': self.has_children,
            'is_specific_task_re_run': is_specific_task_re_run,
            'fact_sheet_answers': self.fact_sheet_answers,
            'queue': self.phase.competition.queue
        }
        sub = Submission(**submission_arg_dict)
        sub.save(ignore_submission_limit=True)

        # set tasks for rerunning
        if flag_rerun_specific_task_or_has_no_children:
            # in case of a submission with no children or specific task rerun
            # submission with no children is same as submission with one task
            tasks = [sub.task]
        else:
            # in case submission has multiple children or multiple task rerun
            # tasks are gathered from the children submissions
            tasks = Task.objects.filter(pk__in=self.children.values_list('task', flat=True))

        sub.start(tasks=tasks)
        return sub

    def cancel(self, status=CANCELLED):
        if self.status not in [Submission.CANCELLED, Submission.FAILED, Submission.FINISHED]:
            if self.has_children:
                for sub in self.children.all():
                    sub.cancel(status=status)
            celery_app = app
            # If a custom queue is set, we need to fetch the appropriate celery app
            if self.phase.competition.queue:
                celery_app = app_for_vhost(str(self.phase.competition.queue.vhost))

            celery_app.control.revoke(self.celery_task_id, terminate=True)
            self.status = status
            self.save()
            return True
        return False

    def check_child_submission_statuses(self):
        done_statuses = [self.FINISHED, self.FAILED, self.CANCELLED]
        if all([status in done_statuses for status in self.children.values_list('status', flat=True)]):
            self.status = 'Finished'
            self.save()

    def calculate_scores(self):
        # leaderboards = self.phase.competition.leaderboards.all()
        # for leaderboard in leaderboards:
        columns = self.phase.leaderboard.columns.exclude(computation__isnull=True)
        for column in columns:
            scores = self.scores.filter(column__index__in=column.computation_indexes.split(',')).values_list('score',
                                                                                                             flat=True)
            if scores.exists():
                score = column.compute(scores)
                try:
                    sub_score = self.scores.get(column=column)
                    sub_score.score = score
                    sub_score.save()
                except SubmissionScore.DoesNotExist:
                    sub_score = SubmissionScore.objects.create(
                        column=column,
                        score=score
                    )
                    self.scores.add(sub_score)

    @property
    def on_leaderboard(self):
        on_leaderboard = False
        if self.leaderboard:
            on_leaderboard = True
        elif self.has_children:
            on_leaderboard = bool(self.children.first().leaderboard)
        return on_leaderboard


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
    reason = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'competition')

    def __str__(self):
        return f"({self.id}) - User: {self.user.username} in Competition: {self.competition.title}"

    def save(self, *args, **kwargs):
        # Determine if this is a new participant (no existing record in DB)
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Increment the participants_count for the competition
            self.competition.participants_count += 1
            self.competition.save()

    def delete(self, *args, **kwargs):
        # Decrement the participants_count for the competition
        competition = self.competition
        super().delete(*args, **kwargs)
        competition.participants_count -= 1
        competition.save()


class Page(models.Model):
    competition = models.ForeignKey(Competition, related_name='pages', on_delete=models.CASCADE)
    title = models.TextField(max_length=255)
    content = models.TextField(null=True, blank=True)
    index = models.PositiveIntegerField()

    class Meta:
        ordering = ('index',)


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


# Competition White List Email Model class
# related to Competition Model
# Each Competition can have multiple white list emails
# These are used to auto approve if competition white list has this email
class CompetitionWhiteListEmail(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='whitelist_emails')
    email = models.EmailField()

    def __str__(self):
        return f"{self.email} - Competition: {self.competition.title}"
