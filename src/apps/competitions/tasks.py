import base64
import json
import logging
import os

import oyaml as yaml
import zipfile

from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.utils.text import slugify

from celery_config import app
from dateutil import parser
from django.core.files import File
from django.utils.timezone import now

from tempfile import TemporaryDirectory

from api.serializers.competitions import CompetitionSerializer
from api.serializers.tasks import TaskSerializer, SolutionSerializer, IngestionModuleSerializer, ScoringModuleSerializer
from competitions.models import Submission, CompetitionCreationTaskStatus, SubmissionDetails, Competition, \
    CompetitionDump
from datasets.models import Data
from tasks.models import Task, Solution
from utils.data import make_url_sassy

logger = logging.getLogger()

# TODO: Double check fields; computation, computation_indexes, etc will be implemented in the future
COMPETITION_FIELDS = [
    "title"
]

PHASE_FIELDS = [
    "index",
    "name",
    "description",
    "start",
    "end"
]
PHASE_FILES = [
    "input_data",
    "reference_data",
    "scoring_program",
    "ingestion_program",
    "public_data",
    "starting_kit",
]
PAGE_FIELDS = [
    "title"
    # "index"
]
LEADERBOARD_FIELDS = [
    # 'primary_index',
    'title',
    'key'
]

COLUMN_FIELDS = [
    # 'computation',
    # 'computation_indexes',
    'title',
    'key',
    'index',
    'sorting'
]


@app.task(queue='site-worker', soft_time_limit=60)
def run_submission(submission_pk, is_scoring=False):
    related_models = (
        'phase',
        'phase__competition',
        'phase__input_data',
        'phase__reference_data',
        'phase__scoring_program',
        'phase__ingestion_program',
        'phase__public_data',
        'phase__starting_kit',
    )
    submission = Submission.objects.select_related(*related_models).prefetch_related('details').get(pk=submission_pk)

    run_arguments = {
        # TODO! Remove this hardcoded api url...
        "api_url": "http://django/api",
        # "program_data": make_url_sassy(submission.data.data_file.name),
        # "scoring_program": make_url_sassy(submission.phase.scoring_program.data_file.name),
        # "ingestion_program": make_url_sassy(submission.phase.ingestion_program.data_file.name),
        "secret": submission.secret,
        "docker_image": "python:3.7",
        "execution_time_limit": submission.phase.execution_time_limit,
        "id": submission.pk,
        "is_scoring": is_scoring,
    }

    if not is_scoring:
        # Pre-generate file path by setting empty file here
        submission.result.save('result.zip', ContentFile(''.encode()))  # must encode here for GCS
        # Run the submission
        run_arguments["program_data"] = make_url_sassy(submission.data.data_file.name)
        run_arguments["result"] = make_url_sassy(submission.result.name, permission='w')
    else:
        # Run the scoring_program
        run_arguments["program_data"] = make_url_sassy(submission.phase.scoring_program.data_file.name)
        run_arguments["result"] = make_url_sassy(submission.result.name)
        # run_arguments["ingestion_program"] = make_url_sassy(submission.phase.ingestion_program.data_file.name)

    # Inputs like reference data/etc.
    inputs = (
        'input_data',
        'reference_data',
    )
    for input in inputs:
        if getattr(submission.phase, input) is not None:
            run_arguments[input] = make_url_sassy(getattr(submission.phase, input).data_file.name)

    # Detail logs like stdout/etc.
    for detail_name in SubmissionDetails.DETAILED_OUTPUT_NAMES:
        new_details = SubmissionDetails.objects.create(submission=submission, name=detail_name)
        new_details.data_file.save(f'{detail_name}.txt', ContentFile(''.encode()))  # must encode here for GCS
        run_arguments[detail_name] = make_url_sassy(new_details.data_file.name, permission="w")

    print("Task data:")
    print(run_arguments)

    # Pad timelimit so worker has time to cleanup
    time_padding = 60 * 20  # 20 minutes
    time_limit = submission.phase.execution_time_limit + time_padding

    task = app.send_task('compute_worker_run', args=(run_arguments,), queue='compute-worker', soft_time_limit=time_limit)
    submission.task_id = task.id
    submission.status = Submission.SUBMITTED
    submission.save()


class CompetitionUnpackingException(Exception):
    pass


def get_data_key(obj, file_type, temp_directory, creator):
    file_name = obj.get(file_type)
    if not file_name:
        return

    file_path = os.path.join(temp_directory, file_name)
    if os.path.exists(file_path):
        new_dataset = Data(
            created_by=creator,
            type=file_type,
            name=f"{file_type} @ {now().strftime('%m-%d-%Y %H:%M')}",
            was_created_by_competition=True,
        )
        new_dataset.data_file.save(os.path.basename(file_path), File(open(file_path, 'rb')))
        return new_dataset.key
    elif len(file_name) in (32, 36):
        # UUID are 32 or 36 characters long
        # TODO send error message if invalid UUID or invalid filename
        # if filename is 32 or 36 chars long but isn't present,
        # it processes like UUID and then breaks but doesn't inform user.
        return file_name
    else:
        raise CompetitionUnpackingException(f'Cannot find dataset: "{file_name}" for task: "{obj["name"]}"')


@app.task(queue='site-worker', soft_time_limit=60 * 60)  # 1 hour timeout
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
                # Hold these here and pop them off before saving comp so that phases can reference the as needed
                "tasks": {},
                "solutions": {},
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
            # Tasks
            tasks = competition_yaml.get('tasks')
            if tasks:
                for task in tasks:
                    if 'index' not in task:
                        # TODO this may be duplicate code from the yaml validator that may eventually exist?
                        raise CompetitionUnpackingException(f'ERROR: No index for task: {task["name"] if "name" in task else task["key"]}')

                    index = task['index']

                    if index in competition['tasks']:
                        raise CompetitionUnpackingException(f'ERROR: Duplicate task indexes. Index: {index}')

                    if 'key' in task:
                        # just add the {index: key} to competition tasks
                        competition['tasks'][index] = task['key']
                    else:
                        # must create task object so we can add {index: key} to competition tasks
                        new_task = {
                            'name': task['name'],
                            'description': task['description'] if 'description' in task else None,
                            'created_by': creator.id,
                        }
                        ingestion_module = task.get('ingestion_module')
                        if ingestion_module:
                            if 'key' in ingestion_module:
                                new_task['ingestion_module'] = ingestion_module['key']
                            else:
                                new_ingestion_module = {
                                    'name': ingestion_module['name'],
                                    'description': ingestion_module['description'] if 'description' in ingestion_module else None,
                                    'created_by': creator.id,
                                    'only_during_scoring': ingestion_module['only_during_scoring'] if 'only_during_scoring' in ingestion_module else None,
                                }
                                for file_type in ['ingestion_program', 'input_data']:
                                    new_ingestion_module[file_type] = get_data_key(
                                        obj=ingestion_module,
                                        file_type=file_type,
                                        temp_directory=temp_directory,
                                        creator=creator)
                                serializer = IngestionModuleSerializer(data=new_ingestion_module)
                                serializer.is_valid(raise_exception=True)
                                new_ingestion_module = serializer.save()
                                new_task['ingestion_module'] = new_ingestion_module.key

                        scoring_module = task.get('scoring_module')
                        if scoring_module:
                            if 'key' in scoring_module:
                                new_task['scoring_module'] = scoring_module['key']
                            else:
                                new_scoring_module = {
                                    'name': scoring_module['name'],
                                    'description': scoring_module['description'] if 'description' in scoring_module else None,
                                    'created_by': creator.id,
                                }
                                for file_type in ['reference_data', 'scoring_program']:
                                    new_scoring_module[file_type] = get_data_key(
                                        obj=scoring_module,
                                        file_type=file_type,
                                        temp_directory=temp_directory,
                                        creator=creator
                                    )
                                serializer = ScoringModuleSerializer(data=new_scoring_module)
                                serializer.is_valid(raise_exception=True)
                                new_scoring_module = serializer.save()
                                new_task['scoring_module'] = new_scoring_module.key
                        serializer = TaskSerializer(
                            data=new_task,
                        )
                        serializer.is_valid(raise_exception=True)
                        new_task = serializer.save()
                        competition["tasks"][index] = new_task.key

            # ---------------------------------------------------------------------
            # Solutions
            solutions = competition_yaml.get('solutions')
            if solutions:
                for solution in solutions:
                    if 'index' not in solution:
                        raise CompetitionUnpackingException(f"ERROR: No index for solution: {solution['name'] if 'name' in solution else solution['key']}")

                    index = solution['index']
                    task_keys = [competition['tasks'][task_index] for task_index in solution.get('tasks')]

                    # TODO: Pretty sure some of this will be done by yaml validator?

                    if not task_keys:
                        raise CompetitionUnpackingException(f"ERROR: Solution: {solution['key']} missing task index pointers")

                    if index in competition['solutions']:
                        raise CompetitionUnpackingException(f"ERROR: Duplicate indexes. Index: {index}")

                    if 'key' in solution:
                        # add {index: {'key': key, 'tasks': task_index}} to competition solutions
                        # TODO:// raise an exception if solution matching key doesn't exist
                        Solution.objects.get(key=solution['key']).tasks.add(*Task.objects.filter(key__in=task_keys))

                        competition['solutions'][index] = solution['key']

                    else:
                        # create solution object and then add {index: {'key': key, 'tasks': task_indexes}} to competition solutions
                        name = solution['name'] if 'name' in solution else f"solution @ {now().strftime('%m-%d-%Y %H:%M')}"
                        description = solution['description'] if 'description' in solution else None
                        file_name = solution['path']
                        file_path = os.path.join(temp_directory, file_name)
                        if os.path.exists(file_path):
                            new_solution_data = Data(
                                created_by=creator,
                                type='solution',
                                name=name,
                                description=description,
                                was_created_by_competition=True,
                            )
                            new_solution_data.data_file.save(os.path.basename(file_path), File(open(file_path, 'rb')))
                            new_solution = {
                                'data': new_solution_data.key,
                                'tasks': task_keys,
                            }
                            serializer = SolutionSerializer(data=new_solution)
                            serializer.is_valid(raise_exception=True)
                            new_solution = serializer.save()
                            competition['solutions'][index] = new_solution.key
                        else:
                            pass
                            # TODO: add processing for using a key to data for a solution?
                            # new_task[file_type] = new_dataset.key

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
                    "name": phase_data.get('name'),
                    "description": phase_data.get('description') if 'description' in phase_data else None,
                    "start": parser.parse(str(phase_data.get('start'))) if 'start' in phase_data else None,
                    "end": parser.parse(phase_data.get('end')) if 'end' in phase_data else None,
                    'max_submissions_per_day': phase_data.get('max_submissions_per_day') if 'max_submissions_per_day' in phase_data else None,
                    'max_submissions_per_phase': phase_data.get('max_submissions') if 'max_submissions' in phase_data else None,
                }

                if 'max_submissions_per_day' in phase_data or 'max_submissions' in phase_data:
                    new_phase['has_max_submissions'] = True

                tasks = phase_data.get('tasks')
                if tasks:
                    new_phase['is_task_and_solution'] = True
                    new_phase['tasks'] = [competition['tasks'][index] for index in tasks]

                    solutions = phase_data.get('solutions')
                    if solutions:
                        new_phase['solutions'] = [competition['solutions'][index] for index in solutions]

                else:
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

                            # verify as UUID?

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


@app.task(queue='site-worker', soft_time_limit=60 * 10)
def create_competition_dump(competition_pk):
    yaml_data = {}
    try:
        # -------- SetUp -------

        logger.info(f"Finding competition {competition_pk}")
        comp = Competition.objects.get(pk=competition_pk)
        zip_buffer = BytesIO()
        zip_name = f"{comp.title}-{comp.created_when.isoformat()}.zip"
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        # -------- Main Competition Details -------
        for field in COMPETITION_FIELDS:
            if hasattr(comp, field):
                yaml_data[field] = getattr(comp, field, "")
        if comp.logo:
            logger.info("Checking logo")
            try:
                yaml_data['image'] = 'logo.png'
                zip_file.writestr(yaml_data['image'], comp.logo.read())
                logger.info(f"Logo found for competition {comp.pk}")
            except OSError:
                logger.warning(
                    f"Competition {comp.pk} has no file associated with the logo, even though the logo field is set."
                )

        # -------- Competition Pages -------
        yaml_data['pages'] = []
        for page in comp.pages.all():
            temp_page_data = {}
            for field in PAGE_FIELDS:
                if hasattr(page, field):
                    temp_page_data[field] = getattr(page, field, "")
            page_file_name = f"{slugify(page.title)}-{page.pk}.md"
            temp_page_data['file'] = page_file_name
            yaml_data['pages'].append(temp_page_data)
            zip_file.writestr(temp_page_data['file'], page.content)

        # -------- Competition Phases -------

        yaml_data['phases'] = []
        for phase in comp.phases.all():
            temp_phase_data = {}
            for field in PHASE_FIELDS:
                if hasattr(phase, field):
                    if field == 'start' or field == 'end':
                        temp_date = str(getattr(phase, field).strftime("%m-%d-%Y"))
                        temp_phase_data[field] = temp_date
                    else:
                        temp_phase_data[field] = getattr(phase, field, "")
            for file_type in PHASE_FILES:
                if hasattr(phase, file_type):
                    temp_dataset = getattr(phase, file_type)
                    if temp_dataset:
                        if temp_dataset.data_file:
                            try:
                                temp_phase_data[file_type] = f"{file_type}-{phase.pk}.zip"
                                zip_file.writestr(temp_phase_data[file_type], temp_dataset.data_file.read())
                            except OSError:
                                logger.error(
                                    f"The file field is set, but no actual"
                                    f" file was found for dataset: {temp_dataset.pk} with name {temp_dataset.name}"
                                )
                        else:
                            logger.warning(f"Could not find data file for dataset object: {temp_dataset.pk}")
            yaml_data['phases'].append(temp_phase_data)

        # -------- Leaderboards -------

        yaml_data['leaderboards'] = []
        for leaderboard in comp.leaderboards.all():
            ldb_data = {}
            for field in LEADERBOARD_FIELDS:
                if hasattr(leaderboard, field):
                    ldb_data[field] = getattr(leaderboard, field, "")
            ldb_data['columns'] = []
            for column in leaderboard.columns.all():
                col_data = {}
                for field in COLUMN_FIELDS:
                    if hasattr(column, field):
                        col_data[field] = getattr(column, field, "")
                ldb_data['columns'].append(col_data)
            yaml_data['leaderboards'].append(ldb_data)

        # ------- Finalize --------
        logger.info(f"YAML data to be written is: {yaml_data}")
        comp_yaml = yaml.safe_dump(yaml_data, default_flow_style=False, allow_unicode=True, encoding="utf-8")
        logger.info(f"YAML output: {comp_yaml}")
        zip_file.writestr("competition.yaml", comp_yaml)
        zip_file.close()
        logger.info("Creating ZIP file")
        competition_dump_file = ContentFile(zip_buffer.getvalue())
        logger.info("Creating new Data object with type competition_bundle")
        bundle_count = CompetitionDump.objects.count() + 1
        temp_dataset_bundle = Data.objects.create(
            created_by=comp.created_by,
            name=f"{comp.title} Dump #{bundle_count} Created {comp.created_when.date()}",
            type='competition_bundle',
            description='Automatically created competition dump',
            # 'data_file'=,
        )
        logger.info("Saving zip to Competition Bundle")
        temp_dataset_bundle.data_file.save(zip_name, competition_dump_file)
        logger.info("Creating new CompetitionDump object")
        temp_comp_dump = CompetitionDump.objects.create(
            dataset=temp_dataset_bundle,
            status="Finished",
            details="Competition Bundle {0} for Competition {1}".format(temp_dataset_bundle.pk, comp.pk),
            competition=comp
        )
        logger.info(f"Finished creating competition dump: {temp_comp_dump.pk} for competition: {comp.pk}")
    except ObjectDoesNotExist:
        logger.info("Could not find competition with pk {} to create a competition dump".format(competition_pk))
