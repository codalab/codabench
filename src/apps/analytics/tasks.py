import os
import time
import logging
import json
from celery_config import app
from datetime import datetime, timezone, timedelta
from django.db.models import (
    Sum,
    Q,
    F,
    Case,
    Value,
    When,
    DecimalField,
)
from django.db.models.functions import TruncDay
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
from profiles.models import User

from utils.data import pretty_bytes

logger = logging.getLogger()


@app.task(queue="site-worker", soft_time_limit=60 * 60 * 24)  # 24 hours
def create_storage_analytics_snapshot():
    # Timer started !
    logger.info("Task create_storage_analytics_snapshot started")
    starting_time = time.process_time()

    # Measure all files with unset size
    for dataset in Data.objects.filter(Q(file_size__isnull=True) | Q(file_size__lt=0)):
        try:
            dataset.file_size = Decimal(
                dataset.data_file.size
            )  # file_size is in Bytes
        except Exception:
            dataset.file_size = Decimal(-1)
        finally:
            dataset.save()

    for submission in Submission.objects.filter(
        Q(prediction_result_file_size__isnull=True) |
        Q(prediction_result_file_size__lt=0)
    ):
        try:
            submission.prediction_result_file_size = Decimal(
                submission.prediction_result.size
            )  # prediction_result_file_size is in Bytes
        except Exception:
            submission.prediction_result_file_size = Decimal(-1)
        finally:
            submission.save()

    for submission in Submission.objects.filter(
        Q(scoring_result_file_size__isnull=True) | Q(scoring_result_file_size__lt=0)
    ):
        try:
            submission.scoring_result_file_size = Decimal(
                submission.scoring_result.size
            )  # scoring_result_file_size is in Bytes
        except Exception:
            submission.scoring_result_file_size = Decimal(-1)
        finally:
            submission.save()

    for submission in Submission.objects.filter(
        Q(detailed_result_file_size__isnull=True) | Q(detailed_result_file_size__lt=0)
    ):
        try:
            submission.detailed_result_file_size = Decimal(
                submission.detailed_result.size
            )  # detailed_result_file_size is in Bytes
        except Exception:
            submission.detailed_result_file_size = Decimal(-1)
        finally:
            submission.save()

    for submissiondetails in SubmissionDetails.objects.filter(
        Q(file_size__isnull=True) | Q(file_size__lt=0)
    ):
        try:
            submissiondetails.file_size = Decimal(
                submissiondetails.data_file.size
            )  # file_size is in Bytes
        except Exception:
            submissiondetails.file_size = Decimal(-1)
        finally:
            submissiondetails.save()

    # Evaluate the storage usage per category (competition, user or admin) and per day
    current_datetime = datetime.now(timezone.utc)
    max_history_days = 365  # days

    # Competitions
    competitions_datasets = (
        Data.objects.filter(competition_id__isnull=False)
        .annotate(day=TruncDay("created_when"))
        .values("day", "competition_id")
        .annotate(
            size=Sum(
                Case(
                    When(file_size__gt=0, then=F("file_size")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )
    )

    last_competition_storage_datapoint = CompetitionStorageDataPoint.objects.order_by(
        "-at_date"
    ).first()
    last_competition_storage_datapoint_date = (
        last_competition_storage_datapoint.at_date
        if last_competition_storage_datapoint
        else current_datetime - timedelta(days=max_history_days)
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    competition_storage_days_count = int(
        (current_datetime - last_competition_storage_datapoint_date).days
    )
    competition_storage_day_range = [
        last_competition_storage_datapoint_date + timedelta(day)
        for day in range(1, competition_storage_days_count + 1)
    ]

    for date in competition_storage_day_range:
        for competition in Competition.objects.order_by("id"):
            datasets_usage = competitions_datasets.filter(
                Q(competition_id=competition.id) & Q(day__lt=date)
            ).aggregate(total=Sum("size"))["total"]
            defaults = {
                "datasets_total": datasets_usage or 0,
            }
            lookup_params = {"competition_id": competition.id, "at_date": date}
            CompetitionStorageDataPoint.objects.update_or_create(
                defaults=defaults, **lookup_params
            )

    # Users
    users_datasets = (
        Data.objects.filter(created_by_id__isnull=False)
        .annotate(day=TruncDay("created_when"))
        .values("day", "created_by_id")
        .annotate(
            size=Sum(
                Case(
                    When(file_size__gt=0, then=F("file_size")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )
    )

    users_submissions = (
        Submission.objects.filter(owner_id__isnull=False)
        .annotate(day=TruncDay("created_when"))
        .values("day", "owner_id")
        .annotate(
            size=Sum(
                Case(
                    When(
                        prediction_result_file_size__gt=0,
                        then=F("prediction_result_file_size"),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                ) + Case(
                    When(
                        scoring_result_file_size__gt=0,
                        then=F("scoring_result_file_size"),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                ) + Case(
                    When(
                        detailed_result_file_size__gt=0,
                        then=F("detailed_result_file_size"),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )
    )

    users_submissions_details = (
        SubmissionDetails.objects.filter(submission__owner_id__isnull=False)
        .annotate(day=TruncDay("submission__created_when"))
        .values("day", "submission__owner_id")
        .annotate(
            size=Sum(
                Case(
                    When(file_size__gt=0, then=F("file_size")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )
    )

    last_user_storage_datapoint = UserStorageDataPoint.objects.order_by(
        "-at_date"
    ).first()
    last_user_storage_datapoint_date = (
        last_user_storage_datapoint.at_date
        if last_user_storage_datapoint
        else current_datetime - timedelta(days=max_history_days)
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    user_storage_days_count = int(
        (current_datetime - last_user_storage_datapoint_date).days
    )
    user_storage_day_range = [
        last_user_storage_datapoint_date + timedelta(day)
        for day in range(1, user_storage_days_count + 1)
    ]

    for date in user_storage_day_range:
        for user in User.objects.order_by("id"):
            datasets_usage = users_datasets.filter(
                Q(created_by_id=user.id) & Q(day__lt=date)
            ).aggregate(total=Sum("size"))["total"]
            submissions_usage = users_submissions.filter(
                Q(owner_id=user.id) & Q(day__lt=date)
            ).aggregate(total=Sum("size"))["total"]
            submissiondetails_usage = users_submissions_details.filter(
                Q(submission__owner_id=user.id) & Q(day__lt=date)
            ).aggregate(total=Sum("size"))["total"]
            defaults = {
                "datasets_total": datasets_usage or 0,
                "submissions_total": (submissions_usage or 0) + (submissiondetails_usage or 0),
            }
            lookup_params = {"user_id": user.id, "at_date": date}
            UserStorageDataPoint.objects.update_or_create(
                defaults=defaults, **lookup_params
            )

    # Admin
    last_admin_storage_datapoint = AdminStorageDataPoint.objects.order_by(
        "-at_date"
    ).first()
    last_admin_storage_datapoint_date = (
        last_admin_storage_datapoint.at_date
        if last_admin_storage_datapoint
        else current_datetime - timedelta(days=max_history_days)
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    admin_storage_days_count = int(
        (current_datetime - last_admin_storage_datapoint_date).days
    )
    admin_storage_day_range = [
        last_admin_storage_datapoint_date + timedelta(day)
        for day in range(1, admin_storage_days_count + 1)
    ]
    admin_storage_at_date = {
        last_admin_storage_datapoint_date + timedelta(day): 0
        for day in range(1, admin_storage_days_count + 1)
    }

    objects = BundleStorage.bucket.objects.filter(Prefix="backups")
    for object in objects:
        size = object.size
        last_modified = object.last_modified
        for date in admin_storage_day_range:
            if last_modified < date:
                admin_storage_at_date[date] += size

    for date in admin_storage_day_range:
        defaults = {"backups_total": admin_storage_at_date[date]}
        lookup_params = {"at_date": date}
        AdminStorageDataPoint.objects.update_or_create(
            defaults=defaults, **lookup_params
        )

    # Check for database <-> storage inconsistency
    inconsistencies = {"database": [], "storage": []}

    # Prepare some data
    last_storage_usage_history_point = (
        StorageUsageHistory.objects.filter(bucket_name=BundleStorage.bucket.name)
        .order_by("-at_date")
        .first()
    )
    last_storage_usage_history_date = (
        last_storage_usage_history_point.at_date
        if last_storage_usage_history_point
        else current_datetime - timedelta(days=max_history_days)
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    storage_usage_history_days_count = int(
        (current_datetime - last_storage_usage_history_date).days
    )
    storage_usage_history_days = range(1, storage_usage_history_days_count + 1)
    storage_usage_history_day_range = [
        last_storage_usage_history_date + timedelta(day)
        for day in range(1, storage_usage_history_days_count + 1)
    ]

    # Database
    nb_missing_files = 0

    # Datasets
    for dataset in Data.objects.all().order_by("id"):
        if (
            not dataset.data_file or not dataset.data_file.name or not BundleStorage.exists(dataset.data_file.name)
        ):
            inconsistencies["database"].append(
                {"model": "dataset", "field": "data_file", "id": dataset.id}
            )
            nb_missing_files += 1

    # Submissions
    for submission in Submission.objects.all().order_by("id"):
        if (
            not submission.prediction_result or not submission.prediction_result.name or not BundleStorage.exists(submission.prediction_result.name)
        ):
            inconsistencies["database"].append(
                {
                    "model": "submission",
                    "field": "prediction_result",
                    "id": submission.id,
                }
            )
            nb_missing_files += 1
        if (
            not submission.scoring_result or not submission.scoring_result.name or not BundleStorage.exists(submission.scoring_result.name)
        ):
            inconsistencies["database"].append(
                {"model": "submission", "field": "scoring_result", "id": submission.id}
            )
            nb_missing_files += 1
        if (
            submission.detailed_result and submission.detailed_result.name and not BundleStorage.exists(submission.detailed_result.name)
        ):
            inconsistencies["database"].append(
                {"model": "submission", "field": "detailed_result", "id": submission.id}
            )
            nb_missing_files += 1

    # Submission details
    for submissiondetails in SubmissionDetails.objects.all().order_by("id"):
        if (
            not submissiondetails.data_file or not submissiondetails.data_file.name or not BundleStorage.exists(submissiondetails.data_file.name)
        ):
            inconsistencies["database"].append(
                {
                    "model": "submissiondetails",
                    "field": "data_file",
                    "id": submissiondetails.id,
                }
            )
            nb_missing_files += 1

    # Storage
    nb_orphaned_files = 0
    orphaned_files_total_size = 0  # In bytes
    orphaned_files_size_per_date = {
        last_storage_usage_history_date + timedelta(day): 0
        for day in range(1, storage_usage_history_days_count + 1)
    }

    # Dataset
    db_dataset_paths = Data.objects.values_list("data_file", flat=True).distinct()
    storage_dataset_paths = [
        obj.key for obj in BundleStorage.bucket.objects.filter(Prefix="dataset")
    ]
    orphaned_dataset_files = [
        x for x in storage_dataset_paths if x not in set(db_dataset_paths)
    ]
    nb_orphaned_files += len(orphaned_dataset_files)
    for file in orphaned_dataset_files:
        size = BundleStorage.size(file)
        last_modified = BundleStorage.get_modified_time(file)
        inconsistencies["storage"].append({"path": file, "size": size})
        orphaned_files_total_size += size
        for date in storage_usage_history_day_range:
            if last_modified < date:
                orphaned_files_size_per_date[date] += size

    # Detailed result
    db_detailed_result_paths = Submission.objects.values_list(
        "detailed_result", flat=True
    ).distinct()
    storage_detailed_result_paths = [
        obj.key for obj in BundleStorage.bucket.objects.filter(Prefix="detailed_result")
    ]
    orphaned_detailed_result_files = [
        x
        for x in storage_detailed_result_paths
        if x not in set(db_detailed_result_paths)
    ]
    nb_orphaned_files += len(orphaned_detailed_result_files)
    for file in orphaned_detailed_result_files:
        size = BundleStorage.size(file)
        last_modified = BundleStorage.get_modified_time(file)
        inconsistencies["storage"].append({"path": file, "size": size})
        orphaned_files_total_size += size
        for date in storage_usage_history_day_range:
            if last_modified < date:
                orphaned_files_size_per_date[date] += size

    # Prediction result
    db_prediction_result_paths = Submission.objects.values_list(
        "prediction_result", flat=True
    ).distinct()
    storage_prediction_result_paths = [
        obj.key
        for obj in BundleStorage.bucket.objects.filter(Prefix="prediction_result")
    ]
    orphaned_prediction_result_files = [
        x
        for x in storage_prediction_result_paths
        if x not in set(db_prediction_result_paths)
    ]
    nb_orphaned_files += len(orphaned_prediction_result_files)
    for file in orphaned_prediction_result_files:
        size = BundleStorage.size(file)
        last_modified = BundleStorage.get_modified_time(file)
        inconsistencies["storage"].append({"path": file, "size": size})
        orphaned_files_total_size += size
        for date in storage_usage_history_day_range:
            if last_modified < date:
                orphaned_files_size_per_date[date] += size

    # Scoring result
    db_scoring_result_paths = Submission.objects.values_list(
        "scoring_result", flat=True
    ).distinct()
    storage_scoring_result_paths = [
        obj.key for obj in BundleStorage.bucket.objects.filter(Prefix="scoring_result")
    ]
    orphaned_scoring_result_files = [
        x for x in storage_scoring_result_paths if x not in set(db_scoring_result_paths)
    ]
    nb_orphaned_files += len(orphaned_scoring_result_files)
    for file in orphaned_scoring_result_files:
        size = BundleStorage.size(file)
        last_modified = BundleStorage.get_modified_time(file)
        inconsistencies["storage"].append({"path": file, "size": size})
        orphaned_files_total_size += size
        for date in storage_usage_history_day_range:
            if last_modified < date:
                orphaned_files_size_per_date[date] += size

    # Submission details
    db_submission_details_paths = SubmissionDetails.objects.values_list(
        "data_file", flat=True
    ).distinct()
    storage_submission_details_paths = [
        obj.key
        for obj in BundleStorage.bucket.objects.filter(Prefix="submission_details")
    ]
    orphaned_submission_details_files = [
        x
        for x in storage_submission_details_paths
        if x not in set(db_submission_details_paths)
    ]
    nb_orphaned_files += len(orphaned_submission_details_files)
    for file in orphaned_submission_details_files:
        size = BundleStorage.size(file)
        last_modified = BundleStorage.get_modified_time(file)
        inconsistencies["storage"].append({"path": file, "size": size})
        orphaned_files_total_size += size
        for date in storage_usage_history_day_range:
            if last_modified < date:
                orphaned_files_size_per_date[date] += size

    # Log the results
    log_file = (
        "/app/var/logs/" +
        "db_storage_inconsistency_" +
        current_datetime.strftime("%Y%m%d-%H%M%S") +
        ".log"
    )
    with open(log_file, "w") as file:
        file.write("Database <---> Storage Inconsistency\n\n")
        file.write(f"Bucket:   {BundleStorage.bucket.name}\n")
        file.write(f"Datetime: {current_datetime.isoformat()}\n\n")
        file.write(f"Missing files:    {nb_missing_files} files\n")
        for missing_file in inconsistencies["database"]:
            file.write(
                f'{missing_file["model"]} of id={missing_file["id"]} is missing its {missing_file["field"]}\n'
            )
        file.write(
            f"\nOrphaned files:    {nb_orphaned_files} files for a total of {pretty_bytes(orphaned_files_total_size)} ({orphaned_files_total_size}B)\n"
        )
        for orphaned_file in inconsistencies["storage"]:
            file.write(
                f'{orphaned_file["path"]}    {pretty_bytes(orphaned_file["size"])} ({orphaned_file["size"]}B)\n'
            )

    # Save the storage usage history points
    for date in [
        last_storage_usage_history_date + timedelta(day)
        for day in storage_usage_history_days
    ]:
        competitions_usage = (
            competitions_datasets.filter(day__lt=date).aggregate(total=Sum("size"))[
                "total"
            ] or 0
        )
        users_usage = (
            (
                users_datasets.filter(day__lt=date).aggregate(total=Sum("size"))[
                    "total"
                ] or 0
            ) +
            (
                users_submissions.filter(day__lt=date).aggregate(total=Sum("size"))[
                    "total"
                ] or 0
            ) +
            (
                users_submissions_details.filter(day__lt=date).aggregate(
                    total=Sum("size")
                )["total"] or 0
            )
        )
        admin_data_point = AdminStorageDataPoint.objects.filter(at_date=date).first()
        admin_usage = (admin_data_point.backups_total or 0) if admin_data_point else 0
        orphaned_file_usage = Decimal(orphaned_files_size_per_date[date])
        total_usage = (
            users_usage + admin_usage + orphaned_file_usage
        )  # competitions_usage is included inside users_usage
        storage_usage_history_point = {
            "bucket_name": BundleStorage.bucket.name,
            "total_usage": total_usage,
            "competitions_usage": competitions_usage,
            "users_usage": users_usage,
            "admin_usage": admin_usage,
            "orphaned_file_usage": orphaned_file_usage,
            "at_date": date,
        }
        StorageUsageHistory.objects.create(**storage_usage_history_point)

    # Stop the count!
    elapsed_time = time.process_time() - starting_time
    logger.info(
        "Task create_storage_analytics_snapshot stoped. Duration = {:.3f} seconds".format(
            elapsed_time
        )
    )


@app.task(queue="site-worker")
def update_home_page_counters():
    starting_time = time.process_time()
    logger.info("Task update_home_page_counters Started")

    # Count public competitions
    public_competitions = Competition.objects.filter(published=True).count()

    # Count active users
    users = User.objects.filter(is_deleted=False).count()

    # Count all submissions
    submissions = Submission.objects.all().count()

    # Create counters data
    counters_data = {
        "public_competitions": public_competitions,
        "users": users,
        "submissions": submissions,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

    # Save latest counters in the file
    log_file = "/app/home_page_counters.json"
    with open(log_file, "w") as f:
        json.dump(counters_data, f, indent=4)

    elapsed_time = time.process_time() - starting_time
    logger.info(
        "Task update_home_page_counters Completed. Duration = {:.3f} seconds".format(elapsed_time)
    )


@app.task(queue="site-worker")
def delete_orphan_files():
    logger.info("Task delete_orphan_files started")

    # Find most recent file
    most_recent_log_file = get_most_recent_storage_inconsistency_log_file(logger)
    if not most_recent_log_file:
        logger.warning("No storage inconsistency log file found. Nothing will be removed")
        raise Exception("No storage inconsistency log file found")

    # Get the list of orphan files from the content of the most recent log file
    log_folder = "/app/var/logs/"
    orphan_files_path = get_files_path_from_orphan_log_file(os.path.join(log_folder, most_recent_log_file), logger)

    # Delete those files in batch (max 1000 element at once)
    batch_size = 1000
    for i in range(0, len(orphan_files_path), batch_size):
        batch = orphan_files_path[i:i + batch_size]
        objects_formatted = [{'Key': path} for path in batch]
        BundleStorage.bucket.delete_objects(Delete={'Objects': objects_formatted})

    logger.info("Delete oprhan files finished")


def get_most_recent_storage_inconsistency_log_file(logger):
    log_folder = "/app/var/logs/"
    try:
        log_files = [f for f in os.listdir(log_folder) if os.path.isfile(os.path.join(log_folder, f))]
    except FileNotFoundError:
        logger.info(f"Folder '{log_folder}' does not exist.")
        return None

    most_recent_log_file = None
    most_recent_datetime = None
    datetime_format = "%Y%m%d-%H%M%S"
    for file in log_files:
        try:
            basename = os.path.basename(file)
            datetime_str = basename[len("db_storage_inconsistency_"):-len(".log")]
            file_datetime = datetime.strptime(datetime_str, datetime_format)
            if most_recent_datetime is None or file_datetime > most_recent_datetime:
                most_recent_datetime = file_datetime
                most_recent_log_file = file
        except ValueError:
            logger.warning(f"Filename '{file}' does not match the expected format and will be ignored.")

    return most_recent_log_file


def get_files_path_from_orphan_log_file(log_file_path, logger):
    files_path = []

    try:
        with open(log_file_path) as log_file:
            lines = log_file.readlines()
            orphan_files_lines = []
            for i, line in enumerate(lines):
                if "Orphaned files" in line:
                    orphan_files_lines = lines[i + 1:]
                    break

            for orphan_files_line in orphan_files_lines:
                files_path.append(orphan_files_line.split(maxsplit=1)[0])
    except FileNotFoundError:
        logger.error(f"File '{log_file_path}' does not exist.")
    except PermissionError:
        logger.error(f"Permission denied for reading the file '{log_file_path}'.")
    except IOError as e:
        logger.error(f"An I/O error occurred while accessing the file at {log_file_path}: {e}")

    return files_path
