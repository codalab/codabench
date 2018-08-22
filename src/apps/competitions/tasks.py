import os
import yaml
import zipfile

from tempfile import TemporaryDirectory

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

        # print(temp_directory)
        print("yaaaaaaaaaaaaaayy")

        # for r, d, f in os.walk(temp_directory):
        #     for file in f:
        #         print(os.path.join(r, file))

        yaml_path = os.path.join(temp_directory, "competition.yaml")
        yaml_data = open(yaml_path).read()
        competition_yaml = yaml.load(yaml_data)

        """

            title: Example Hello World Competition
            image: logo.jpg
            pages:
              - title: Welcome!
                content: welcome.md
              - title: Terms and conditions
                content: terms_and_conditions.md
            phases:
              - name: Test
                description: A test phase
                start: 08/01/2018
                end: 09/01/2018
                scoring_program: scoring_program.zip
            leaderboards:
              - title: Hello World Leaderboard!
                key: main
                columns:
                  - label: Correct?
                    key: correct
                    rank: 0

        """

        # Can maybe split this into a separate function
        image_path = os.path.join(temp_directory, competition_yaml.get('image'))
        image_base64 = open(image_path, "rb").read().encode("base64")

        competition = {
            "title": competition_yaml.get('title'),
            "image": image_base64,
            "pages": [],
            "phases": [],
            "leaderboards": [],
        }

        # print(competition)
        # for thing in competition_yaml['html']:
        #     print(thing)
        #
        #
        #
        #
        #
        # print("as")

        






