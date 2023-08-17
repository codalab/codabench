import time
import logging
from celery_config import app
from datetime import datetime, timezone, timedelta
from django.db.models import Sum, Q, F
from decimal import Decimal

from competitions.models import Submission, SubmissionDetails
from datasets.models import Data
from utils.storage import BundleStorage
from analytics.models import (
    StorageUsageHistory,
    CompetitionStorageDataPoint,
    UserStorageDataPoint,
    AdminStorageDataPoint,
)
from competitions.models import Competition
from datasets.models import Data
from profiles.models import User
from competitions.models import Submission, SubmissionDetails

logger = logging.getLogger()


@app.task(queue="site-worker", soft_time_limit=60 * 60 * 12)  # 12 hours
def create_storage_analytics_snapshot():
    logger.info("Task create_storage_analytics_snapshot started")
    starting_time = time.process_time()

    # Measure all files with unset size
    for dataset in Data.objects.filter(Q(file_size__isnull=True) | Q(file_size__lt=0)):
        try:
            dataset.file_size = Decimal(dataset.data_file.size / 1024)
        except:
            dataset.file_size = Decimal(-1)
        finally:
            dataset.save()

    for submission in Submission.objects.filter(
        Q(prediction_result_file_size__isnull=True)
        | Q(prediction_result_file_size__lt=0)
    ):
        try:
            submission.prediction_result_file_size = Decimal(
                submission.prediction_result.size / 1024
            )
        except:
            submission.prediction_result_file_size = Decimal(-1)
        finally:
            submission.save()

    for submission in Submission.objects.filter(
        Q(scoring_result_file_size__isnull=True) | Q(scoring_result_file_size__lt=0)
    ):
        try:
            submission.scoring_result_file_size = Decimal(
                submission.scoring_result.size / 1024
            )
        except:
            submission.scoring_result_file_size = Decimal(-1)
        finally:
            submission.save()

    for submission in Submission.objects.filter(
        Q(detailed_result_file_size__isnull=True) | Q(detailed_result_file_size__lt=0)
    ):
        try:
            submission.detailed_result_file_size = Decimal(
                submission.detailed_result.size / 1024
            )
        except:
            submission.detailed_result_file_size = Decimal(-1)
        finally:
            submission.save()

    for submissiondetails in SubmissionDetails.objects.filter(
        Q(file_size__isnull=True) | Q(file_size__lt=0)
    ):
        try:
            submissiondetails.file_size = Decimal(
                submissiondetails.data_file.size / 1024
            )
        except:
            submissiondetails.file_size = Decimal(-1)
        finally:
            submissiondetails.save()

    # Retrieve the last storage usage history point
    bucket = BundleStorage.bucket  # type: ignore
    current_datetime = datetime.now(timezone.utc)

    # Competitions details
    competitions = Competition.objects.all().reverse()
    for competition in competitions:
        datasets_usage = Data.objects.filter(
            (
                Q(competition__id=competition.id)
                & Q(type=Data.SUBMISSION)
                & Q(was_created_by_competition=True)
            )
            | (
                Q(competition__id=competition.id)
                & Q(type=Data.SOLUTION)
                & Q(was_created_by_competition=True)
            )
            | (
                Q(competition__id=competition.id)
                & ~Q(type=Data.SUBMISSION)
                & ~Q(type=Data.SOLUTION)
            )
        ).aggregate(total=Sum("file_size"))["total"]

        defaults = {
            "title": competition.title,
            "created_by": competition.created_by,
            "created_when": competition.created_when,
            "competition_type": competition.competition_type,
            "datasets_total": datasets_usage or 0,
        }
        lookup_params = {"competition_id": competition.id, "at_date": current_datetime}
        CompetitionStorageDataPoint.objects.update_or_create(
            defaults=defaults, **lookup_params
        )

    # User details
    users = User.objects.exclude(id=-1).exclude(username="AnonymousUser")
    for user in users:
        datasets_usage = Data.objects.filter(
            Q(created_by__id=user.id)
            & (
                (
                    Q(type=Data.SUBMISSION)
                    & (
                        Q(competition__isnull=True)
                        | Q(was_created_by_competition=False)
                    )
                )
                | (
                    Q(type=Data.SOLUTION)
                    & (
                        Q(competition__isnull=True)
                        | Q(was_created_by_competition=False)
                    )
                )
                | (
                    ~Q(type=Data.SUBMISSION)
                    & ~Q(type=Data.SOLUTION)
                    & Q(competition__isnull=True)
                )
            )
        ).aggregate(total=Sum("file_size"))["total"]
        submissions_usage = Submission.objects.filter(owner__id=user.id).aggregate(
            total=Sum(
                F("prediction_result_file_size")
                + F("scoring_result_file_size")
                + F("detailed_result_file_size")
            )
        )["total"]
        submissiondetails_usage = SubmissionDetails.objects.filter(
            submission__owner=user.id
        ).aggregate(total=Sum("file_size"))["total"]

        defaults = {
            "email": user.email,
            "username": user.username,
            "datasets_total": datasets_usage or 0,
            "submissions_total": (submissions_usage or 0)
            + (submissiondetails_usage or 0),
        }
        lookup_params = {"user_id": user.id, "at_date": current_datetime}
        UserStorageDataPoint.objects.update_or_create(
            defaults=defaults, **lookup_params
        )

    # Admin details
    datasets_usage = Data.objects.filter(
        (
            Q(type=Data.SUBMISSION)
            & (Q(competition__isnull=True) | Q(was_created_by_competition=False))
            & Q(created_by__isnull=True)
        )
        | (
            Q(type=Data.SOLUTION)
            & (Q(competition__isnull=True) | Q(was_created_by_competition=False))
            & Q(created_by__isnull=True)
        )
        | (
            ~Q(type=Data.SUBMISSION)
            & ~Q(type=Data.SOLUTION)
            & Q(competition__isnull=True)
            & Q(created_by__isnull=True)
        )
    ).aggregate(total=Sum("file_size"))["total"]
    backups_usage = 0
    objects = bucket.objects.filter(Prefix="backups")
    for object in objects:
        backups_usage += object.size

    defaults = {"backups_total": backups_usage, "others_total": datasets_usage or 0}
    lookup_params = {"at_date": current_datetime}
    AdminStorageDataPoint.objects.update_or_create(defaults=defaults, **lookup_params)

    # Save the storage usage history points
    last_storage_usage_history_point = (
        StorageUsageHistory.objects.filter(bucket_name=bucket.name)
        .order_by("-at_date")
        .first()
    )
    last_storage_usage_history_date = (
        last_storage_usage_history_point.at_date
        if last_storage_usage_history_point
        else current_datetime - timedelta(days=1000)
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    days_count = int((current_datetime - last_storage_usage_history_date).days)
    days = range(1, days_count + 1)
    usage_at_date = {
        last_storage_usage_history_date
        + timedelta(day): {
            "total": Decimal(0),
            "competitions": Decimal(0),
            "users": Decimal(0),
            "admin": Decimal(0),
        }
        for day in days
    }

    for competition_data_point in CompetitionStorageDataPoint.objects.all().order_by(
        "at_date"
    ):
        for date in usage_at_date:
            if competition_data_point.at_date <= date:
                if competition_data_point.datasets_total:
                    usage_at_date[date][
                        "competitions"
                    ] += competition_data_point.datasets_total

    for user_data_point in UserStorageDataPoint.objects.all().order_by("at_date"):
        for date in usage_at_date:
            if user_data_point.at_date <= date:
                if user_data_point.datasets_total:
                    usage_at_date[date]["users"] += user_data_point.datasets_total
                if user_data_point.submissions_total:
                    usage_at_date[date]["users"] += user_data_point.submissions_total

    for admin_data_point in AdminStorageDataPoint.objects.all().order_by("at_date"):
        for date in usage_at_date:
            if admin_data_point.at_date <= date:
                if admin_data_point.backups_total:
                    usage_at_date[date]["admin"] += admin_data_point.backups_total
                if admin_data_point.others_total:
                    usage_at_date[date]["admin"] += admin_data_point.others_total

    for date, usages in usage_at_date.items():
        storage_usage_history_point = {
            "bucket_name": bucket.name,
            "at_date": date,
            "total_usage": usages["total"],
            "competitions_usage": usages["competitions"],
            "users_usage": usages["users"],
            "admin_usage": usages["admin"],
        }
        StorageUsageHistory.objects.create(**storage_usage_history_point)

    elapsed_time = time.process_time() - starting_time
    logger.info(
        "Task create_storage_analytics_snapshot stoped. Duration = {:.3f} seconds".format(
            elapsed_time
        )
    )


@app.task(queue="site-worker")  # 12 hours
def reset_computed_storage_analytics():
    logger.info("Task reset_computed_storage_analytics started")
    starting_time = time.process_time()

    # Reset the value of all computed file sizes so they will be re-computed again without any shifting on the next run of the storage analytics task
    Submission.objects.all().update(
        prediction_result_file_size=None,
        scoring_result_file_size=None,
        detailed_result_file_size=None,
    )
    SubmissionDetails.objects.all().update(file_size=None)
    Data.objects.all().update(file_size=None)

    elapsed_time = time.process_time() - starting_time
    logger.info(
        "Task reset_computed_storage_analytics stoped. Duration = {:.3f} seconds".format(
            elapsed_time
        )
    )
