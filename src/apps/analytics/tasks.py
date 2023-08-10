import time
import logging
from celery_config import app

logger = logging.getLogger()


@app.task(queue="site-worker", soft_time_limit=60 * 60 * 12)  # 12 hours
def create_storage_analytics_snapshot():
    logger.info("Task create_storage_analytics_snapshot started")
    starting_time = time.process_time()

    # TODO Insert valuable code here

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

    # TODO Insert valuable code here

    elapsed_time = time.process_time() - starting_time
    logger.info(
        "Task reset_computed_storage_analytics stoped. Duration = {:.3f} seconds".format(
            elapsed_time
        )
    )
