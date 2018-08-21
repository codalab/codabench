from comp_worker import app

from competitions import models
from datasets.models import Data


@app.task
def score_submission_lazy(submission_pk):
    sub_to_score = models.Submission.objects.get(pk=submission_pk)
    sub_to_score.score = 1
    sub_to_score.save()


@app.task
def score_submission(submission_pk, phase_pk):
    sub_to_score = models.Submission.objects.get(pk=submission_pk)
    scoring_phase = models.Phase.objects.get(pk=phase_pk)
    scoring_program = scoring_phase.scoring_program
    file_to_score = sub_to_score.zip_file
    print(scoring_program)
    print(file_to_score)


@app.task
def unpack_competition(competition_dataset_pk):
    competition_dataset = Data.objects.get(pk=competition_dataset_pk)

    status = models.CompetitionCreationTaskStatus.objects.create(
        dataset=competition_dataset,
        status=models.CompetitionCreationTaskStatus.STARTING,
    )
    # competition_creation_task = CompetitionCreationTaskStatus.objects.get(pk=competition_creation_task_pk)
