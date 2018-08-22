import base64
import json
import os
import yaml
import zipfile

from tempfile import TemporaryDirectory

from api.serializers.competitions import CompetitionSerializer
from comp_worker import app
from competitions.models import Submission, Phase, CompetitionCreationTaskStatus

from datasets.models import Data


@app.task
def score_submission_lazy(submission_pk):
    sub_to_score = Submission.objects.get(pk=submission_pk)
    sub_to_score.score = 1
    sub_to_score.save()


@app.task
def score_submission(submission_pk, phase_pk):
    sub_to_score = Submission.objects.get(pk=submission_pk)
    scoring_phase = Phase.objects.get(pk=phase_pk)
    scoring_program = scoring_phase.scoring_program
    file_to_score = sub_to_score.zip_file
    print(scoring_program)
    print(file_to_score)


@app.task
def unpack_competition(competition_dataset_pk):
    competition_dataset = Data.objects.get(pk=competition_dataset_pk)

    status = CompetitionCreationTaskStatus.objects.create(
        dataset=competition_dataset,
        status=CompetitionCreationTaskStatus.STARTING,
    )

    # unpack zip to temp directory
    # read the competition.yaml file
    # validate YAML
    #    - uhhhhhhhhhhhhhhhhhhhh
    # for each dataset in each phase, upload them. -- DO NOT DO DUPLICATES! Be smaht about it
    # create JSON pointing to the datasets properly
    # send it to the serializer + save it
    # return errors to user if any
    # IF ERRORS DESTROY BABY DATASETS!

    with TemporaryDirectory() as temp_directory:
        zip_pointer = zipfile.ZipFile(competition_dataset.data_file.path, 'r')
        zip_pointer.extractall(temp_directory)
        zip_pointer.close()

        yaml_path = os.path.join(temp_directory, "competition.yaml")
        yaml_data = open(yaml_path).read()
        competition_yaml = yaml.load(yaml_data)

        # Turn image into base64 version for easy uploading
        # (Can maybe split this into a separate function)
        image_path = os.path.join(temp_directory, competition_yaml.get('image'))
        with open(image_path, "rb") as image:
            image_json = json.dumps({
                "file_name": os.path.basename(competition_yaml.get('image')),
                # Converts to b64 then to string
                "data": base64.b64encode(image.read()).decode()
            })

        competition = {
            "title": competition_yaml.get('title'),
            # NOTE! We use 'logo' instead of 'image' here....
            "logo": image_json,
            "pages": [],
            "phases": [],
            "leaderboards": [],
        }

        # Pages
        for index, page in enumerate(competition_yaml.get('pages')):
            competition['pages'].append({
                "title": page["title"],
                "content": open(os.path.join(temp_directory, page["file"])).read(),
                "index": index
            })

        # Phases

        # Leaderboards
        for leaderboard in competition_yaml.get('leaderboards'):
            competition['leaderboards'].append(leaderboard)

        # SAVE IT!
        serializer = CompetitionSerializer(
            data=competition,
            # We have to pass the creator here this special way, because this is how the API
            # takes the request.user
            context={"created_by": competition_dataset.created_by}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        






