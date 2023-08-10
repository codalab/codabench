import time
import logging
from celery_config import app

from competitions.models import Submission, SubmissionDetails
from datasets.models import Data

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
