import base64
import json
import os
import yaml
import zipfile

from django.core.files.base import ContentFile

from celery_config import app
from dateutil import parser
from django.core.files import File
from django.utils.timezone import now

from tempfile import TemporaryDirectory

from api.serializers.competitions import CompetitionSerializer
from competitions.models import Submission, CompetitionCreationTaskStatus, SubmissionDetails, SubmissionDetails
from datasets.models import Data
from utils.data import make_url_sassy


@app.task(queue='site-worker')
def run_submission(submission_pk):
    submission = Submission.objects.get(pk=submission_pk)

    submission.status = Submission.SUBMITTED
    submission.save()

    # Pre-generate file path by setting empty file here
    submission.result.save('result.zip', ContentFile(''))

    run_arguments = {
        "submission_data_file": make_url_sassy(submission.data.data_file.name),
        "result": make_url_sassy(submission.result.name),
        "api_key": submission.api_key,
    }

    for detail_name in SubmissionDetails.DETAILED_OUTPUT_NAMES:
        new_details = SubmissionDetails.objects.create(submission=submission, name=detail_name)
        new_details.data_file.save(f'{detail_name}.txt', ContentFile(''))
        run_arguments[detail_name] = make_url_sassy(new_details.data_file.name, permission="w")

    print("Task data:")
    print(run_arguments)
    app.send_task('compute_worker_run', args=(run_arguments,), queue='compute-worker')


class CompetitionUnpackingException(Exception):
    pass


@app.task(queue='site-worker')
def unpack_competition(competition_dataset_pk):
    competition_dataset = Data.objects.get(pk=competition_dataset_pk)
    creator = competition_dataset.created_by

    # Children datasets are those that are created specifically for this "parent" competition.
    # They will be deleted if the competition creation fails
    children_datasets = []

    status = CompetitionCreationTaskStatus.objects.create(
        dataset=competition_dataset,
        status=CompetitionCreationTaskStatus.STARTING,
    )

    try:
        with TemporaryDirectory() as temp_directory:
            # ---------------------------------------------------------------------
            # Extract bundle
            try:
                with zipfile.ZipFile(competition_dataset.data_file, 'r') as zip_pointer:
                    zip_pointer.extractall(temp_directory)
            except zipfile.BadZipFile:
                raise CompetitionUnpackingException("Bad zip file uploaded.")

            # ---------------------------------------------------------------------
            # Read metadata (competition.yaml)
            yaml_path = os.path.join(temp_directory, "competition.yaml")

            if not os.path.exists(yaml_path):
                raise CompetitionUnpackingException("competition.yaml is missing from zip, check your folder structure "
                                                    "to make sure it is in the root directory.")

            yaml_data = open(yaml_path).read()
            competition_yaml = yaml.load(yaml_data)

            # ---------------------------------------------------------------------
            # Initialize the competition dict
            competition = {
                "title": competition_yaml.get('title'),
                # NOTE! We use 'logo' instead of 'image' here....
                "logo": None,
                "pages": [],
                "phases": [],
                "leaderboards": [],
            }

            # ---------------------------------------------------------------------
            # Logo
            # Turn image into base64 version for easy uploading
            # (Can maybe split this into a separate function)
            image_path = os.path.join(temp_directory, competition_yaml.get('image'))

            if not os.path.exists(image_path):
                raise CompetitionUnpackingException(f"Unable to find image: {competition_yaml.get('image')}")

            with open(image_path, "rb") as image:
                competition['logo'] = json.dumps({
                    "file_name": os.path.basename(competition_yaml.get('image')),
                    # Converts to b64 then to string
                    "data": base64.b64encode(image.read()).decode()
                })

            # ---------------------------------------------------------------------
            # Pages
            for index, page in enumerate(competition_yaml.get('pages')):
                try:
                    competition['pages'].append({
                        "title": page.get("title"),
                        "content": open(os.path.join(temp_directory, page["file"])).read(),
                        "index": index
                    })
                except FileNotFoundError:
                    raise CompetitionUnpackingException(f"Unable to find page: {page['file']}")

            # ---------------------------------------------------------------------
            # Phases
            file_types = [
                "input_data",
                "reference_data",
                "scoring_program",
                "ingestion_program",
                "public_data",
                "starting_kit",
            ]

            for index, phase_data in enumerate(competition_yaml.get('phases')):
                new_phase = {
                    "index": index,
                    "name": phase_data['name'],
                    "description": phase_data.get('description') if 'description' in phase_data else None,
                    "start": parser.parse(phase_data.get('start')) if 'start' in phase_data else None,
                    "end": parser.parse(phase_data.get('end')) if 'end' in phase_data else None,
                }

                for file_type in file_types:
                    # File names can be existing dataset keys OR they can be actual files uploaded with the bundle
                    file_name = phase_data.get(file_type)

                    if not file_name:
                        continue

                    file_path = os.path.join(temp_directory, file_name)
                    if os.path.exists(file_path):
                        # We have a file, not UUID, needs to be uploaded
                        new_dataset = Data(
                            created_by=creator,
                            type=file_type,
                            name=f"{file_type} @ {now().strftime('%m-%d-%Y %H:%M')}",
                            was_created_by_competition=True,
                        )
                        # This saves the file AND saves the model
                        new_dataset.data_file.save(os.path.basename(file_path), File(open(file_path, 'rb')))

                        children_datasets.append(new_dataset)

                        new_phase[file_type] = new_dataset.key
                    elif len(file_name) in (32, 36):
                        # Keys are length 32 or 36, so check if we can find a dataset matching this already
                        new_phase[file_type] = file_name
                    else:
                        raise CompetitionUnpackingException(f"Cannot find dataset: \"{file_name}\" for phase \"{new_phase['name']}\"")

                competition['phases'].append(new_phase)

            # ---------------------------------------------------------------------
            # Leaderboards
            for leaderboard in competition_yaml.get('leaderboards'):
                competition['leaderboards'].append(leaderboard)

            # SAVE IT!
            print("Saving competition....")

            # ---------------------------------------------------------------------
            # Finalize
            serializer = CompetitionSerializer(
                data=competition,
                # We have to pass the creator here this special way, because this is how the API
                # takes the request.user
                context={"created_by": creator}
            )
            serializer.is_valid(raise_exception=True)
            competition = serializer.save()

            status.status = CompetitionCreationTaskStatus.FINISHED
            status.resulting_competition = competition
            status.save()
            print("Competition saved!")

            # TODO: If something fails delete baby datasets and such!!!!
    except CompetitionUnpackingException as e:
        status.details = str(e)
        status.status = CompetitionCreationTaskStatus.FAILED
        status.save()

        print("FAILED!")
        print(status.details)
