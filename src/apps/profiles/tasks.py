import time
import logging
from datetime import timedelta
from django.utils.timezone import now
from celery_config import app

from profiles.models import DeletedUser

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
