import time
import logging
from datetime import timedelta
from django.utils.timezone import now
from celery_config import app
from django.contrib.auth import get_user_model
from profiles.models import DeletedUser
from competitions.models import Competition, Submission

logger = logging.getLogger()


@app.task(queue="site-worker")
def clean_deleted_users():
    starting_time = time.process_time()
    logger.info("Task clean_deleted_users Started")

    # Calculate the threshold date (one month ago)
    one_month_ago = now() - timedelta(days=30)

    # Delete users who were deleted more than a month ago
    deleted_count, _ = DeletedUser.objects.filter(deleted_at__lt=one_month_ago).delete()

    logger.info(f"Deleted {deleted_count} users from DeletedUser table.")

    elapsed_time = time.process_time() - starting_time
    logger.info(
        "Task clean_deleted_users Completed. Duration = {:.3f} seconds".format(elapsed_time)
    )


@app.task(queue="site-worker")
def clean_non_activated_users():
    try:
        starting_time = time.process_time()
        logger.info("Task clean_non_activated_users Started")

        # Get User model
        User = get_user_model()

        # Calculate the threshold date (3 days ago)
        three_days_ago = now() - timedelta(days=3)

        # Filter users who are inactive, not deleted and created more than 3 days ago
        users_to_delete = User.objects.filter(
            is_active=False,
            is_deleted=False,
            date_joined__lt=three_days_ago
        )

        # Exclude users who have created any competitions or made submissions
        users_to_delete = users_to_delete.exclude(
            id__in=Competition.objects.values_list('created_by_id', flat=True)
        ).exclude(
            id__in=Submission.objects.values_list('owner_id', flat=True)
        )

        # Delete users
        deleted_count, _ = users_to_delete.delete()

        logger.info(f"Deleted {deleted_count} non activated users from User table.")

        elapsed_time = time.process_time() - starting_time
        logger.info(
            "Task clean_non_activated_users Completed. Duration = {:.3f} seconds".format(elapsed_time)
        )
    except Exception as e:
        logger.exception(f"Failed to clean non-activated users\n{e}")
