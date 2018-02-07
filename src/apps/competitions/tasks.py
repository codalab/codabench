from celery import shared_task

from competitions import models


@shared_task
def score_submission(submission_pk):
    sub_to_score = models.Submission.objects.get(pk=submission_pk)
    sub_to_score.score = 1
    sub_to_score.save()
    return True # Do we need to do this?
