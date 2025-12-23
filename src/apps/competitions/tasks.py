import asyncio
import os
import re
import traceback
import zipfile
from datetime import timedelta, datetime

from io import BytesIO
from tempfile import TemporaryDirectory, NamedTemporaryFile

import oyaml as yaml
import requests
from celery._state import app_or_default
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db.models import Subquery, OuterRef, Count, Case, When, Value, F
from django.utils.text import slugify
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from celery_config import app
from competitions.models import Submission, CompetitionCreationTaskStatus, SubmissionDetails, Competition, \
    CompetitionDump, Phase
from competitions.unpackers.utils import CompetitionUnpackingException
from competitions.unpackers.v1 import V15Unpacker
from competitions.unpackers.v2 import V2Unpacker
from leaderboards.models import Leaderboard
from tasks.models import Task
from datasets.models import Data
from utils.data import make_url_sassy
from utils.email import codalab_send_markdown_email

import logging
logger = logging.getLogger(__name__)

COMPETITION_FIELDS = [
    "title",
    "description",
    "docker_image",
    "queue",
    "registration_auto_approve",
    "enable_detailed_results",
    "show_detailed_results_in_submission_panel",
    "show_detailed_results_in_leaderboard",
    "auto_run_submissions",
    "can_participants_make_submissions_public",
    "make_programs_available",
    "make_input_data_available",
    "competition_type",
    "reward",
    "contact_email",
    "fact_sheet",
    "forum_enabled"
]

TASK_FIELDS = [
    'name',
    'description',
    'key',
    'is_public',
]
SOLUTION_FIELDS = [
    'name',
    'description',
    'tasks',
    'key',
]

PHASE_FIELDS = [
    'index',
    'name',
    'description',
    'start',
    'end',
    'max_submissions_per_day',
    'max_submissions_per_person',
    'execution_time_limit',
    'auto_migrate_to_this_phase',
    'hide_output',
    'hide_prediction_output',
    'hide_score_output',
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
]
LEADERBOARD_FIELDS = [
    'title',
    'key',
    'hidden',
    'submission_rule',

    # For later
    # 'force_submission_to_leaderboard',
    # 'force_best_submission_to_leaderboard',
    # 'disallow_leaderboard_modifying',
]

COLUMN_FIELDS = [
    'title',
    'key',
    'index',
    'sorting',
    'computation',
    'computation_indexes',
    'hidden',
    'precision',
]
MAX_EXECUTION_TIME_LIMIT = int(os.environ.get('MAX_EXECUTION_TIME_LIMIT', 600))  # time limit of the default queue


def _send_to_compute_worker(submission, is_scoring):
    run_args = {
        "user_pk": submission.owner.pk,
        "submissions_api_url": settings.SUBMISSIONS_API_URL,
        "secret": submission.secret,
        "docker_image": submission.phase.competition.docker_image,
        "execution_time_limit": min(MAX_EXECUTION_TIME_LIMIT, submission.phase.execution_time_limit),
        "id": submission.pk,
        "is_scoring": is_scoring,
    }

    if not submission.detailed_result.name and submission.phase.competition.enable_detailed_results:
        submission.detailed_result.save('detailed_results.html', ContentFile(''.encode()))  # must encode here for GCS
        submission.save(update_fields=['detailed_result'])
    if not submission.prediction_result.name:
        submission.prediction_result.save('prediction_result.zip', ContentFile(''.encode()))  # must encode here for GCS
        submission.save(update_fields=['prediction_result'])
    if not submission.scoring_result.name:
        submission.scoring_result.save('scoring_result.zip', ContentFile(''.encode()))  # must encode here for GCS
        submission.save(update_fields=['scoring_result'])

    submission = Submission.objects.get(id=submission.id)
    task = submission.task

    # priority of scoring tasks is higher, we don't want to wait around for
    # many submissions to be scored while we're waiting for results
    if is_scoring:
        # higher numbers are higher priority
        priority = 10
    else:
        priority = 0

    if not is_scoring:
        run_args['prediction_result'] = make_url_sassy(
            path=submission.prediction_result.name,
            permission='w'
        )
    else:
        if submission.phase.competition.enable_detailed_results:
            run_args['detailed_results_url'] = make_url_sassy(
                path=submission.detailed_result.name,
                permission='w',
                content_type='text/html'
            )
        run_args['prediction_result'] = make_url_sassy(
            path=submission.prediction_result.name,
            permission='r'
        )
        run_args['scoring_result'] = make_url_sassy(
            path=submission.scoring_result.name,
            permission='w'
        )

    if task.ingestion_program:
        if (task.ingestion_only_during_scoring and is_scoring) or (not task.ingestion_only_during_scoring and not is_scoring):
            run_args['ingestion_program'] = make_url_sassy(task.ingestion_program.data_file.name)

    if task.input_data and (not is_scoring or task.ingestion_only_during_scoring):
        run_args['input_data'] = make_url_sassy(task.input_data.data_file.name)

    if is_scoring and task.reference_data:
        run_args['reference_data'] = make_url_sassy(task.reference_data.data_file.name)

    run_args['ingestion_only_during_scoring'] = task.ingestion_only_during_scoring

    run_args['program_data'] = make_url_sassy(
        path=submission.data.data_file.name if not is_scoring else task.scoring_program.data_file.name
    )

    if not is_scoring:
        detail_names = SubmissionDetails.DETAILED_OUTPUT_NAMES_PREDICTION
    else:
        detail_names = SubmissionDetails.DETAILED_OUTPUT_NAMES_SCORING

    for detail_name in detail_names:
        run_args[detail_name] = create_detailed_output_file(detail_name, submission)

    logger.info(f"Task data for submission id = {submission.id}")
    logger.info(run_args)

    # Pad timelimit so worker has time to cleanup
    time_padding = 60 * 20  # 20 minutes
    time_limit = submission.phase.execution_time_limit + time_padding

    if submission.phase.competition.queue:  # if the competition is running on a custom queue, not the default queue
        submission.queue_name = submission.phase.competition.queue.name or ''
        run_args['execution_time_limit'] = submission.phase.execution_time_limit  # use the competition time limit
        submission.save()

        # Send to special queue? Using `celery_app` var name here since we'd be overriding the imported `app`
        # variable above
        celery_app = app_or_default()
        with celery_app.connection() as new_connection:
            new_connection.virtual_host = str(submission.phase.competition.queue.vhost)
            task = celery_app.send_task(
                'compute_worker_run',
                args=(run_args,),
                queue='compute-worker',
                soft_time_limit=time_limit,
                connection=new_connection,
                priority=priority,
            )
    else:
        task = app.send_task(
            'compute_worker_run',
            args=(run_args,),
            queue='compute-worker',
            soft_time_limit=time_limit,
            priority=priority,
        )
    submission.celery_task_id = task.id

    if submission.status == Submission.SUBMITTING:
        # Don't want to mark an already-prepared submission as "submitted" again, so
        # only do this if we were previously "SUBMITTING"
        submission.status = Submission.SUBMITTED

    submission.save()


def create_detailed_output_file(detail_name, submission):
    # Detail logs like stdout/etc.
    new_details = SubmissionDetails.objects.create(submission=submission, name=detail_name)
    new_details.data_file.save(f'{detail_name}.txt', ContentFile(''.encode()))  # must encode here for GCS
    return make_url_sassy(new_details.data_file.name, permission="w")


def run_submission(submission_pk, tasks=None, is_scoring=False):
    task_ids = [t.id for t in tasks] if tasks else None
    return _run_submission.apply_async((submission_pk, task_ids, is_scoring))


def send_submission_message(submission, data):
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    user = submission.owner
    asyncio.get_event_loop().run_until_complete(channel_layer.group_send(f"submission_listening_{user.pk}", {
        'type': 'submission.message',
        'text': data,
        'submission_id': submission.pk,
    }))


def send_parent_status(submission):
    """Helper function we can mock in tests, instead of having to do async mocks"""
    send_submission_message(submission, {
        "kind": "status_update",
        "status": "Running"
    })


def send_child_id(submission, child_id):
    """Helper function we can mock in tests, instead of having to do async mocks"""
    send_submission_message(submission, {
        "kind": "child_update",
        "child_id": child_id
    })


@app.task(queue='site-worker', soft_time_limit=60)
def _run_submission(submission_pk, task_pks=None, is_scoring=False):
    """This function is wrapped so that when we run tests we can run this function not
    via celery"""
    select_models = (
        'phase',
        'phase__competition',
    )
    prefetch_models = (
        'details',
        'phase__tasks__input_data',
        'phase__tasks__reference_data',
        'phase__tasks__scoring_program',
        'phase__tasks__ingestion_program',
    )
    qs = Submission.objects.select_related(*select_models).prefetch_related(*prefetch_models)
    submission = qs.get(pk=submission_pk)

    if submission.is_specific_task_re_run:
        # Should only be one task for a specified task submission
        tasks = Task.objects.filter(pk__in=task_pks)
    elif task_pks is None:
        tasks = submission.phase.tasks.all()
    else:
        tasks = submission.phase.tasks.filter(pk__in=task_pks)

    tasks = tasks.order_by('pk')

    if len(tasks) > 1:
        # The initial submission object becomes the parent submission and we create children for each task
        submission.has_children = True
        submission.save()

        send_parent_status(submission)

        for task in tasks:
            # TODO: make a duplicate submission method and use it here
            child_sub = Submission(
                owner=submission.owner,
                phase=submission.phase,
                data=submission.data,
                participant=submission.participant,
                parent=submission,
                task=task,
                fact_sheet_answers=submission.fact_sheet_answers
            )
            child_sub.save(ignore_submission_limit=True)
            _send_to_compute_worker(child_sub, is_scoring=False)
            send_child_id(submission, child_sub.id)
    else:
        # The initial submission object is the only submission
        if not submission.task:
            submission.task = tasks[0]
            submission.save()
        _send_to_compute_worker(submission, is_scoring)


@app.task(queue='site-worker', soft_time_limit=60 * 60)  # 1 hour timeout
def unpack_competition(status_pk):
    logger.info(f"Starting unpack with status pk = {status_pk}")
    status = CompetitionCreationTaskStatus.objects.get(pk=status_pk)
    competition_dataset = status.dataset
    creator = competition_dataset.created_by

    def mark_status_as_failed_and_delete_dataset(competition_creation_status, details):
        competition_creation_status.details = details
        competition_creation_status.status = CompetitionCreationTaskStatus.FAILED
        competition_creation_status.save()

        # Cleans up associated data if competition unpacker fails
        competition_creation_status.dataset.delete()

    try:
        with TemporaryDirectory() as temp_directory:
            # ---------------------------------------------------------------------
            # Extract bundle
            try:
                with NamedTemporaryFile(mode="w+b") as temp_file:
                    logger.info(f"Download competition bundle: {competition_dataset.data_file.name}")
                    competition_bundle_url = make_url_sassy(competition_dataset.data_file.url)
                    with requests.get(competition_bundle_url, stream=True) as r:
                        r.raise_for_status()
                        for chunk in r.iter_content(chunk_size=8192):
                            temp_file.write(chunk)
                        r.close()

                    # seek back to the start of the tempfile after writing to it..
                    temp_file.seek(0)

                    with zipfile.ZipFile(temp_file.name, 'r') as zip_pointer:
                        zip_pointer.extractall(temp_directory)
            except zipfile.BadZipFile:
                raise CompetitionUnpackingException("Bad zip file uploaded.")

            # ---------------------------------------------------------------------
            # Read metadata (competition.yaml)
            yaml_path = os.path.join(temp_directory, "competition.yaml")
            if not os.path.exists(yaml_path):
                raise CompetitionUnpackingException("competition.yaml is missing from zip, check your folder structure "
                                                    "to make sure it is in the root directory.")
            with open(yaml_path) as f:
                competition_yaml = yaml.load(f.read())

            yaml_version = str(competition_yaml.get('version', '1'))

            logger.info(f"The YAML version is: {yaml_version}")
            if yaml_version in ['1', '1.5']:
                unpacker_class = V15Unpacker
            elif yaml_version == '2':
                unpacker_class = V2Unpacker
            else:
                raise CompetitionUnpackingException(
                    'A suitable version could not be found for this competition. Make sure one is supplied in the yaml.'
                )

            unpacker = unpacker_class(
                competition_yaml=competition_yaml,
                temp_directory=temp_directory,
                creator=creator,
            )

            unpacker.unpack()
            try:
                competition = unpacker.save()
            except ValidationError as e:
                def _get_error_string(error_dict):
                    """Helps us nicely print out a ValidationError"""
                    for key, errors in error_dict.items():
                        try:
                            return f'{key}: {"; ".join(errors)}\n'
                        except TypeError:
                            # We ran into a list of nested dictionaries, start recursing!
                            nested_errors = []
                            for e in errors:
                                error_text = _get_error_string(e)
                                if error_text:
                                    nested_errors.append(error_text)
                            return f'{key}: {"; ".join(nested_errors)}\n'

                raise CompetitionUnpackingException(_get_error_string(e.detail))

            status.status = CompetitionCreationTaskStatus.FINISHED
            status.resulting_competition = competition
            status.save()
            logger.info("Competition saved!")
            status.dataset.name += f" - {competition.title}"
            status.dataset.save()

    except CompetitionUnpackingException as e:
        # We want to catch well handled exceptions and display them to the user
        message = str(e)
        logger.info(message)
        mark_status_as_failed_and_delete_dataset(status, message)
        raise e

    except Exception as e:  # noqa: E722
        # These are critical uncaught exceptions, make sure the end user is at least informed
        # that unpacking has failed -- do not share unhandled exception details
        logger.error(traceback.format_exc())
        message = "Unpacking the bundle failed. Here is the error log: {}".format(e)
        mark_status_as_failed_and_delete_dataset(status, message)


@app.task(queue='site-worker', soft_time_limit=60 * 10)
def create_competition_dump(competition_pk, keys_instead_of_files=False):
    yaml_data = {"version": "2"}
    try:
        # -------- SetUp -------

        logger.info(f"Finding competition {competition_pk}")
        comp = Competition.objects.get(pk=competition_pk)
        zip_buffer = BytesIO()
        current_date_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        zip_name = f"{comp.title}-{current_date_time}.zip"
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        # -------- Main Competition Details -------
        for field in COMPETITION_FIELDS:
            if hasattr(comp, field):
                value = getattr(comp, field, "")
                if field == 'queue' and value is not None:
                    value = str(value.vhost)
                yaml_data[field] = value
        if comp.logo:
            logger.info("Checking logo")
            try:
                yaml_data['image'] = re.sub(r'.*/', '', comp.logo.name)
                zip_file.writestr(yaml_data['image'], comp.logo.read())
                logger.info(f"Logo found for competition {comp.pk}")
            except OSError:
                logger.warning(
                    f"Competition {comp.pk} has no file associated with the logo, even though the logo field is set."
                )

        # -------- Competition Terms -------
        if comp.terms:
            yaml_data['terms'] = 'terms.md'
            zip_file.writestr('terms.md', comp.terms)

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

        # -------- Competition Tasks/Solutions -------

        yaml_data['tasks'] = []
        yaml_data['solutions'] = []

        task_solution_pairs = {}
        tasks = [task for phase in comp.phases.all() for task in phase.tasks.all()]

        index_two = 0

        # Go through all tasks
        for index, task in enumerate(tasks):

            task_solution_pairs[task.id] = {
                'index': index,
                'solutions': {
                    'ids': [],
                    'indexes': []
                }
            }

            temp_task_data = {
                'index': index
            }

            for field in TASK_FIELDS:
                data = getattr(task, field, "")
                # If keys_instead of files is not true and field is key, then skip this filed
                if not keys_instead_of_files and field == 'key':
                    continue
                if field == 'key':
                    data = str(data)
                temp_task_data[field] = data

            for file_type in PHASE_FILES:
                if hasattr(task, file_type):
                    temp_dataset = getattr(task, file_type)
                    if temp_dataset:
                        if temp_dataset.data_file:
                            if keys_instead_of_files:
                                temp_task_data[file_type] = str(temp_dataset.key)
                            else:
                                try:
                                    temp_task_data[file_type] = f"{file_type}-{task.pk}.zip"
                                    zip_file.writestr(temp_task_data[file_type], temp_dataset.data_file.read())
                                except OSError:
                                    logger.error(
                                        f"The file field is set, but no actual"
                                        f" file was found for dataset: {temp_dataset.pk} with name {temp_dataset.name}"
                                    )
                        else:
                            logger.warning(f"Could not find data file for dataset object: {temp_dataset.pk}")
            # Now for all of our solutions for the tasks, write those too
            for solution in task.solutions.all():
                # for index_two, solution in enumerate(task.solutions.all()):
                #     temp_index = index_two
                # IF OUR SOLUTION WAS ALREADY ADDED
                if solution.id in task_solution_pairs[task.id]['solutions']['ids']:
                    for solution_data in yaml_data['solutions']:
                        if solution_data['key'] == solution.key:
                            solution_data['tasks'].append(task.id)
                            break
                    break
                # Else if our index is already taken
                elif index_two in task_solution_pairs[task.id]['solutions']['indexes']:
                    index_two += 1
                task_solution_pairs[task.id]['solutions']['indexes'].append(index_two)
                task_solution_pairs[task.id]['solutions']['ids'].append(solution.id)

                temp_solution_data = {
                    'index': index_two
                }
                for field in SOLUTION_FIELDS:
                    if hasattr(solution, field):
                        data = getattr(solution, field, "")
                        if field == 'key':
                            data = str(data)
                        temp_solution_data[field] = data
                if solution.data:
                    temp_dataset = getattr(solution, 'data')
                    if temp_dataset:
                        if temp_dataset.data_file:
                            try:
                                temp_solution_data['path'] = f"solution-{solution.pk}.zip"
                                zip_file.writestr(temp_solution_data['path'], temp_dataset.data_file.read())
                            except OSError:
                                logger.error(
                                    f"The file field is set, but no actual"
                                    f" file was found for dataset: {temp_dataset.pk} with name {temp_dataset.name}"
                                )
                        else:
                            logger.warning(f"Could not find data file for dataset object: {temp_dataset.pk}")
                # TODO: Make sure logic here is right. Needs to be outputted as a list, but what others can we tie to?
                temp_solution_data['tasks'] = [index]
                yaml_data['solutions'].append(temp_solution_data)
                index_two += 1
            # End for loop for solutions; Append tasks data
            yaml_data['tasks'].append(temp_task_data)

        # -------- Competition Phases -------

        yaml_data['phases'] = []
        for phase in comp.phases.all():
            temp_phase_data = {}
            for field in PHASE_FIELDS:
                if hasattr(phase, field):
                    if field == 'start' or field == 'end':
                        temp_date = getattr(phase, field)
                        if not temp_date:
                            continue
                        temp_date = temp_date.strftime("%Y-%m-%d")
                        temp_phase_data[field] = temp_date
                    elif field == 'max_submissions_per_person':
                        temp_phase_data['max_submissions'] = getattr(phase, field)
                    else:
                        temp_phase_data[field] = getattr(phase, field, "")
            task_indexes = [task_solution_pairs[task.id]['index'] for task in phase.tasks.all()]
            temp_phase_data['tasks'] = task_indexes
            temp_phase_solutions = []
            for task in phase.tasks.all():
                temp_phase_solutions += task_solution_pairs[task.id]['solutions']['indexes']
            temp_phase_data['solutions'] = temp_phase_solutions
            yaml_data['phases'].append(temp_phase_data)
        yaml_data['phases'] = sorted(yaml_data['phases'], key=lambda phase: phase['index'])

        # -------- Leaderboards -------

        yaml_data['leaderboards'] = []
        # Have to grab leaderboards from phases
        leaderboards = Leaderboard.objects.filter(id__in=comp.phases.all().values_list('leaderboard', flat=True))
        for index, leaderboard in enumerate(leaderboards):
            ldb_data = {
                'index': index
            }
            for field in LEADERBOARD_FIELDS:
                if hasattr(leaderboard, field):
                    ldb_data[field] = getattr(leaderboard, field, "")
            ldb_data['columns'] = []
            for column in leaderboard.columns.all():
                col_data = {}
                for field in COLUMN_FIELDS:
                    if hasattr(column, field):
                        value = getattr(column, field, "")
                        if field == 'computation_indexes' and value is not None:
                            value = value.split(',')
                        if value is not None:
                            col_data[field] = value
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
            name=f"{comp.title} Dump #{bundle_count} Created {current_date_time}",
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
        logger.error("Could not find competition with pk {} to create a competition dump".format(competition_pk))


@app.task(queue='site-worker', soft_time_limit=60 * 5)
def do_phase_migrations():
    # Update phase statuses
    previous_subquery = Phase.objects.filter(
        competition=OuterRef('competition'),
        end__lte=now()
    ).order_by('-index').values('index')[:1]

    current_subquery = Phase.objects.filter(
        competition=OuterRef('competition'),
        start__lte=now(),
        end__gt=now(),
    ).values('index')[:1]

    next_subquery = Phase.objects.filter(
        competition=OuterRef('competition'),
        start__gt=now()
    ).order_by('index').values('index')[:1]

    Phase.objects.annotate(
        previous_index=Subquery(previous_subquery),
        current_index=Subquery(current_subquery),
        next_index=Subquery(next_subquery),
    ).update(status=Case(
        When(index=F('previous_index'), then=Value(Phase.PREVIOUS)),
        When(index=F('current_index'), then=Value(Phase.CURRENT)),
        When(index=F('next_index'), then=Value(Phase.NEXT)),
        default=None
    ))

    # Updating Competitions whose phases have finished migrating to `is_migrating=False`
    completed_statuses = [Submission.FINISHED, Submission.FAILED, Submission.CANCELLED, Submission.NONE]

    running_subs_query = Submission.objects.filter(
        created_by_migration=OuterRef('pk')
    ).exclude(
        status__in=completed_statuses
    ).values_list('pk')[:1]

    Competition.objects.filter(
        pk__in=Phase.objects.annotate(
            running_subs=Count(Subquery(running_subs_query))
        ).filter(
            running_subs=0,
            competition__is_migrating=True,
            status=Phase.PREVIOUS
        ).values_list('competition__pk', flat=True)
    ).update(is_migrating=False)

    # Checking for new phases to start migrating
    new_phases = Phase.objects.filter(
        auto_migrate_to_this_phase=True,
        start__lte=now(),
        competition__is_migrating=False,
        has_been_migrated=False
    )

    logger.info(f"Checking {len(new_phases)} phases for phase migrations.")

    for p in new_phases:
        p.check_future_phase_submissions()


@app.task(queue='site-worker', soft_time_limit=60 * 5)
def manual_migration(phase_id):
    try:
        source_phase = Phase.objects.get(id=phase_id)
    except Phase.DoesNotExist:
        logger.error(f'Could not manually migrate phase with id: {phase_id}. Phase could not be found.')
        return

    try:
        destination_phase = source_phase.competition.phases.get(index=source_phase.index + 1)
    except Phase.DoesNotExist:
        logger.error(f'Could not manually migrate phase with id: {phase_id}. The next phase could not be found.')
        return
    destination_phase.competition.apply_phase_migration(source_phase, destination_phase, force_migration=True)


@app.task(queue='site-worker', soft_time_limit=60 * 5)
def batch_send_email(comp_id, content):
    try:
        competition = Competition.objects.prefetch_related('participants__user').get(id=comp_id)
    except Competition.DoesNotExist:
        logger.error(f'Not sending emails because competition with id {comp_id} could not be found')
        return

    codalab_send_markdown_email(
        subject=f'A message from the admins of {competition.title}',
        markdown_content=content,
        recipient_list=[participant.user.email for participant in competition.participants.all()]
    )


@app.task(queue='site-worker', soft_time_limit=60 * 5)
def update_phase_statuses():
    competitions = Competition.objects.exclude(phases__in=Phase.objects.filter(is_final_phase=True, end__lt=now()))
    for comp in competitions:
        comp.update_phase_statuses()


@app.task(queue='site-worker')
def submission_status_cleanup():
    submissions = Submission.objects.filter(status=Submission.RUNNING, has_children=False).select_related('phase', 'parent')

    for sub in submissions:
        # Check if the submission has been running for 24 hours longer than execution_time_limit
        if sub.started_when < now() - timedelta(milliseconds=(3600000 * 24) + sub.phase.execution_time_limit):
            if sub.parent is not None:
                sub.parent.cancel(status=Submission.FAILED)
            else:
                sub.cancel(status=Submission.FAILED)
