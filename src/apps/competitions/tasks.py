from celery import task

from competitions import models
from competitions.compute_worker import predict


# @task
# def start_submission(submission_pk):
#     submission = models.Submission.objects.get(pk=submission_pk)
#     phase = submission.phase
#     # TODO: Sign these URLs and stdout/stderr
#     ingestion_program = phase.ingestion_program.data_file.name if phase.ingestion_program else None
#     input_data = phase.input_data.data_file.name if phase.input_data else None
#     predict(
#         submission.pk,
#         submission.secret,
#         submission.zip_file,
#         ingestion_program,
#         input_data,
#         submission.std
#     )

    # scoring_phase = models.Phase.objects.get(pk=phase_pk)
    # scoring_program = scoring_phase.scoring_program
    # file_to_score = sub_to_score.zip_file
    # print(scoring_program)
    # print(file_to_score)



@task
def update_status(submission_id, submission_secret, status):




    # Available statuses:
    #     Submitting
    #     Submitted
    #     Predicting
    #     Scoring
    #     Finished OR Failed
    #
    # If status goes to "Scoring" then we should kick off the "Score" task





    pass


@task
def update_output(submission_id, submission_secret, output):










    # A HAH! Send message to username channel!
    #
    # https://stackoverflow.com/questions/39322241/sending-a-message-to-a-single-user-using-django-channels
    #












    pass
