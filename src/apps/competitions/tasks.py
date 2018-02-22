from celery import task

from competitions import models


@task
def score_submission_lazy(submission_pk):
    sub_to_score = models.Submission.objects.get(pk=submission_pk)
    sub_to_score.score = 1
    sub_to_score.save()


@task
def score_submission(submission_pk, phase_pk):
    sub_to_score = models.Submission.objects.get(pk=submission_pk)
    scoring_phase = models.Phase.objects.get(pk=phase_pk)
    scoring_program = scoring_phase.scoring_program
    file_to_score = sub_to_score.zip_file
    print(scoring_program)
    print(file_to_score)


@task
def update_status(submission_id, submission_secret, status):
    pass


@task
def update_output(submission_id, submission_secret, output):










    # A HAH! Send message to username channel!
    #
    # https://stackoverflow.com/questions/39322241/sending-a-message-to-a-single-user-using-django-channels
    #












    pass
