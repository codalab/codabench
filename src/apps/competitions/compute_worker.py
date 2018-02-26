import requests

from celery import Celery, task

app = Celery()
app.conf.update(
    broker_url='amqp://guest:guest@rabbitmq:5672//',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)


def _put(url, file_path):
    requests.put(
        url,
        data=open(file_path, 'rb'),
        headers={
            # Only for Azure but other services ignore this
            'x-ms-blob-type': 'BlockBlob',
        }
    )


def _send_update(submission_name, args, virtual_host='/'):
    # NOTE: This sends updates to be asynchronously processed
    with app.connection() as new_connection:
        # We need to send on the main virtual host, not whatever host we're currently
        # connected to.
        new_connection.virtual_host = virtual_host
        app.send_submission(submission_name, args=args, connection=new_connection, queue="updates")


def update_status(submission_id, submission_secret, status):
    _send_update('competition.submissions.update_status', (submission_id, submission_secret, status))


def update_output(submission_id, submission_secret, output):
    _send_update('competition.submissions.update_output', (submission_id, submission_secret, output))


@task
def predict(submission_id, submission_secret, submission_program, ingestion_program, input_data, stderr_path, stdout_path, output_path):
    """

    All of the following URLs are signed appropriately with ~24hr signatures for editing

    :param submission_id: id of submission in database
    :param submission_secret: 1 time communication token
    :param submission_program: the url to the submission
    :param ingestion_program: the url to the ingestion program
    :param input_data: the url to input data
    :param stderr_path: the writeable signed url for stderr
    :param stdout_path: the writable signed url for stdout
    :param output_path: the writable signed url for submission output results, whatever is in the output folder is
    written to this url
    :return:
    """
    print("predict")
    pass


@task
def score(submission_id, submission_secret, scoring_program, reference_data, stderr_path, stdout_path, output_path):
    """

    All of the following URLs are signed appropriately with ~24hr signatures for editing

    :param submission_id: id of submission in database
    :param submission_secret: 1 time communication token
    :param scoring_program: the url to the executable scoring program for evaluating student submission, which can be
    code (prediction) or results (not predicted upon, no prediction step)
    :param reference_data: the url to the reference data ("ground truth")
    :param stderr_path: the writeable signed url for stderr
    :param stdout_path: the writable signed url for stdout
    :param output_path: the writable signed url for scoring output results, whatever is in the output folder is written
    to this url
    :return:
    """
    print("score")
    pass
