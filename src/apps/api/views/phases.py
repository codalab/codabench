from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from rest_framework.viewsets import ModelViewSet
from api.serializers.competitions import PhaseSerializer, PhaseResultsSerializer
from competitions.models import Phase, Submission
from competitions.tasks import manual_migration
from leaderboards.models import Column
from django.conf import settings
import logging

logger = logging.getLogger()


class PhaseViewSet(ModelViewSet):
    serializer_class = PhaseSerializer

    def get_queryset(self):
        qs = Phase.objects.all()
        return qs

    def list(self, request, *args, **kwargs):
        # Check if it's a direct request to /api/phases/
        # i.e without a pk
        direct_request = 'pk' not in kwargs or kwargs['pk'] == 'list'

        if direct_request:
            # return empty response in direct request
            return Response([], status=status.HTTP_200_OK)

        # Otherwise, allow other functions to use the list functionality as usual
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # TODO! Security, who can access/delete/etc this?

    @action(detail=True, methods=('POST',), url_name='manually_migrate')
    def manually_migrate(self, request, pk):
        """Manually migrates _from_ this phase. The destination phase does not need auto migration set to True"""
        phase = self.get_object()
        if not phase.competition.user_has_admin_permission(request.user):
            return Response(
                {"detail": "You do not have administrative permissions for this competition"},
                status=status.HTTP_403_FORBIDDEN
            )
        manual_migration.apply_async((pk,))
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, url_name='rerun_submissions')
    def rerun_submissions(self, request, pk):

        phase = self.get_object()
        comp = phase.competition

        # Get submissions with no parent
        submissions = phase.submissions.filter(parent__isnull=True)

        can_re_run_submissions = False
        error_message = ""

        # Super admin can rerun without any restrictions
        if request.user.is_superuser:
            can_re_run_submissions = True

        # competition admin can run only if
        elif request.user in comp.all_organizers:

            # submissions are in limit
            if len(submissions) <= int(settings.RERUN_SUBMISSION_LIMIT):
                can_re_run_submissions = True

            # submissions are not in limit
            else:
                # Codabemch public queue
                if comp.queue is None:
                    can_re_run_submissions = False
                    error_message = f"You cannot rerun more than {settings.RERUN_SUBMISSION_LIMIT} submissions on Codabench public queue! Contact us on `info@codalab.org` to request a rerun."

                # Other queue where user is not owner and not organizer
                elif request.user != comp.queue.owner and request.user not in comp.queue.organizers.all():
                    can_re_run_submissions = False
                    error_message = f"You cannot rerun more than {settings.RERUN_SUBMISSION_LIMIT} submissions on a queue which is not yours! Contact us on `info@codalab.org` to request a rerun."

                # User can rerun submissions where he is owner or organizer
                else:
                    can_re_run_submissions = True

        else:
            can_re_run_submissions = False
            error_message = 'You do not have permission to re-run submissions'

        # error when user is not super user or admin of the competition
        if can_re_run_submissions:
            # rerun all submissions
            for submission in submissions:
                submission.re_run()
            rerun_count = len(submissions)
            return Response({"count": rerun_count})
        else:
            raise PermissionDenied(error_message)

    @swagger_auto_schema(responses={200: PhaseResultsSerializer})
    @action(detail=True, methods=['GET'])
    def get_leaderboard(self, request, pk):

        """
        This is an API function that returns leaderboard
        NOTE: To simplify things, each part of this big function is divided into sub functions
        TODO: modify this function to return multiple leaderboards
        """
        def _get_factsheet_keys(_phase):
            """
            Get Factsheet keys from the competition

            - This function iterates through the competition's factsheet questions.
            - It selects only those questions where `is_on_leaderboard` is set to 'true'.
            - Returns a list of key-title pairs for display on the leaderboard.
            """
            fact_sheet_keys = []

            # Check if the competition has fact sheet
            if _phase.competition.fact_sheet:
                for question in _phase.competition.fact_sheet:
                    # Include only fact sheet questions marked as "is_on_leaderboard"
                    if _phase.competition.fact_sheet[question]['is_on_leaderboard'] == 'true':
                        fact_sheet_keys.append({
                            "key": _phase.competition.fact_sheet[question]['key'],
                            "title": _phase.competition.fact_sheet[question]['title']
                        })
            return fact_sheet_keys

        def _get_leaderboard_columns(_leaderboard):
            """
            Get the visible (non-hidden) columns from the leaderboard.

            - Filters columns associated with the given leaderboard where `hidden=False`.
            - Raises a ValidationError if no columns are found.
            - Returns serialized column query set.

            """
            # Get non-hidden columns
            columns = Column.objects.filter(
                leaderboard=_leaderboard,
                hidden=False
            )
            # Raise an error if num columns == 0
            if len(columns) == 0:
                raise ValidationError("No columns exist on the leaderboard")
            return columns

        def _get_phase_tasks(_phase):
            """
            Retrieve the tasks associated with a given competition phase.

            - Fetches the `id` and `name` of all tasks linked to the phase.
            - Returns a QuerySet containing the relevant task data.
            """

            # Get tasks linked to the phase, selecting only id and name
            tasks = _phase.tasks.values("id", "name")
            return tasks

        def _get_detailed_result_settings(_phase):
            """
            Retrieve detailed result settings for the competition phase.

            - Fetches whether detailed results are enabled.
            - Checks if detailed results should be displayed on the leaderboard.
            - Returns a dictionary containing these settings.

            """
            return {
                "enable_detailed_results": _phase.competition.enable_detailed_results,
                "show_detailed_results_in_leaderboard": _phase.competition.show_detailed_results_in_leaderboard
            }

        def _get_phase_leaderboard(_phase):
            """
            Retrieve the leaderboard for a given competition phase.

            - Checks if the phase's leaderboard is hidden.
            - Raises a ValidationError if no visible leaderboard exists.
            - Returns the leaderboard instance if it is visible.
            """

            # Raise an error if leaderboard is hidden
            if _phase.leaderboard.hidden:
                raise ValidationError("No visible leaderboard for this phase")

            return _phase.leaderboard

        def _get_leaderboard_submissions(_phase, _leaderboard, _columns):
            """
            Retrieve submissions for the leaderboard.

            - Fetches submissions with no children or parents
            - Fetches submissions with children
            - Orders results using the primary column and other leaderboard columns.

            Raturns an ordered querySet of leaderboard submissions.
            """
            # Intialize ordering as an empty list
            ordering = []

            # Get primary column from leaderboard columns
            # We use the primary column for ordering
            primary_col = _phase.leaderboard.columns.get(index=_phase.leaderboard.primary_index)

            # If there is a primary column
            # - add first order by this primary column
            # Note: annotate submissions by primary_col so that the ordering is applied
            if primary_col:
                ordering.append(f'{"-" if primary_col.sorting == "desc" else ""}primary_col')

            # Fetch all the leaderboard submissions that include:
            # - standalone submissions: submissions that has no parent and no children
            # - parent submissions with children
            # Fetch the owner, task, child task, and scores of the submissions
            # Annotate by primary_col for ordering
            # TODO: to check why sometimes the parent submission is not on the leaderboard but a child is on the leaderboard
            submissions = Submission.objects.filter(Q(
                # Case 1: Standalone submissions
                Q(
                    phase=_phase,
                    has_children=False,
                    parent__isnull=True,
                    leaderboard__isnull=False,
                    is_specific_task_re_run=False,
                    is_soft_deleted=False
                ) |
                # Case 2: Parent submissions with children in given tasks
                Q(
                    phase=_phase,
                    has_children=True,
                    # leaderboard__isnull=False,  # TODO: uncomment this when the problem with parent submission not on leaderboard is resolved
                    is_specific_task_re_run=False,
                    is_soft_deleted=False
                )
            )).select_related(
                'owner', 'task'
            ).prefetch_related(
                'scores', 'children__task'
            ).annotate(
                primary_col=Coalesce(Sum('scores__score', filter=Q(scores__column=primary_col)), Value(0))
            )

            # Loop over all the leaderboard columns
            # skip the primary column because we have already used it for the annotation
            # add to ordering each column
            # annotate submissions with these columns
            for column in _columns:
                if column.index != _leaderboard.primary_index:  # Skip primary column (already added)
                    col_name = f'col{column.index}'
                    ordering.append(f'{"-" if column.sorting == "desc" else ""}{col_name}')
                    kwargs = {
                        col_name: Sum('scores__score', filter=Q(scores__column__index=column.index))
                    }
                    submissions = submissions.annotate(**kwargs)

            return submissions

        def _prepare_leaderboard_tasks(_tasks):
            """
            This function prepares leaderboard tasks for the front-end
            Returns formatted leaderboard tasks with task id and task name
            """
            leaderboard_tasks = []
            for task in _tasks:
                leaderboard_tasks.append({
                    "id": task["id"],
                    "name": task["name"]
                })
            return leaderboard_tasks

        def _prepare_leaderboard_columns(_columns):
            """
            This function prepares leaderboard columns for the front-end
            Returns formatted leaderboard columns with column title and column key
            """
            leaderboard_columns = []
            for column in _columns:
                leaderboard_columns.append({
                    "title": column.title,
                    "key": column.key
                })
            return leaderboard_columns

        def _prepare_leaderboard_submissions(_fact_sheet_keys, _tasks, _columns, _submissions):
            """
            This function prepares leaderboard submissions for the front-end
            Returns formatted submissions with id, owner, organization, created_when, slug_url, fact_sheet_answers, scores, detailed_results
            """

            # Arrange columns in a lookup dict so that it is easy
            # to get required data without an additional loop
            # key in the dict is col id and value is a dict with column data (title, key, index, precision)
            columns_lookup_dict = {}
            for col in _columns:
                columns_lookup_dict[col.id] = {
                    "title": col.title,
                    "key": col.key,
                    "index": col.index,
                    "precision": col.precision
                }

            # Create an empty list for leaderboard submissions
            leaderboard_submissions = []

            # Loop over submissions to prepare submission data that include:
            # id, owner, organization, created_when, factsheet answers, scores, detailed_results
            for submission in _submissions:

                # Organize submission data
                submisison_data = {
                    "id": submission.id,
                    "owner": submission.owner.display_name or submission.owner.username,
                    "organization": submission.organization,
                    "created_when": submission.created_when,
                    "slug_url": submission.owner.slug_url
                }

                # Organize submission fact_sheet_answers
                fact_sheet_answers = None
                if _fact_sheet_keys:
                    fact_sheet_answers = {}
                    for fact_sheet_item in _fact_sheet_keys:
                        fact_sheet_answers[fact_sheet_item["key"]] = submission.fact_sheet_answers[fact_sheet_item["key"]]
                submisison_data["fact_sheet_answers"] = fact_sheet_answers

                # Arrange submission ids and scores in a dict for each task so that it is easy to fetch
                # the scores for score calulations and submission id for detailed result
                # When a submission has children, it means each child submission is run on a different task and for each task, submission(child) has different scores
                # On the leaderboard we show the parent submission ID but scores are shown from child submissions
                submission_ids_and_scores_per_task = {}
                if submission.has_children:
                    # each child task is fetched from the child submission along with its scores and id
                    for child in submission.children.all():
                        submission_ids_and_scores_per_task[child.task.id] = {
                            "scores": child.scores.all(),
                            "submission_id": child.id
                        }
                else:
                    submission_ids_and_scores_per_task[submission.task.id] = {
                        "scores": submission.scores.all(),
                        "submission_id": submission.id
                    }

                # Create a dict to store detailed result ids per task
                submission_detailed_results = {task["id"]: {} for task in _tasks}

                # Create a dict to store scores as key-value pairs
                # where key is the column key and value is the score value rounded to a precise value
                # scores are stored per task, this is helpful when we have scores for multiple tasks
                submission_scores = {task["id"]: {} for task in _tasks}
                # Loop over the scores and assign them to each task
                for task in _tasks:

                    # Initialize detailed result for this task with None
                    submission_detailed_results[task["id"]] = None

                    # Fetch submission id and score dict from the `submission_ids_and_scores_per_task` dict
                    # If there is an entry for this task then detailed result is set otherwise the
                    # default value is already stored as `None``
                    submission_id_and_score = submission_ids_and_scores_per_task.get(task["id"], None)
                    if submission_id_and_score:
                        submission_detailed_results[task["id"]] = submission_id_and_score["submission_id"]

                    # Fetch score for the task from `submission_ids_and_scores_per_task``
                    # If score is found for this task then:
                    # Loop over the scores to fetch the correct score for each task.
                    # If submission_id_and_score is not found for a task then we do nothing
                    if submission_id_and_score:
                        for score in submission_id_and_score["scores"]:
                            # get column key and column precision from the lookup dict using column_id in each score
                            col_key = columns_lookup_dict[score.column_id]["key"]
                            col_precision = columns_lookup_dict[score.column_id]["precision"]
                            # round the score value to `precision`
                            score_value = round(float(score.score), col_precision)
                            # Store scores under the respective task
                            submission_scores[task["id"]][col_key] = score_value

                # Assign the structured scores to submission data
                submisison_data["scores"] = submission_scores

                # Assign detailed results to submission data
                submisison_data["detailed_results"] = submission_detailed_results

                # At this point submission data is ready and is added to the leaderboard submissions list
                leaderboard_submissions.append(submisison_data)

            # Return the prepared submissions
            return leaderboard_submissions

        # Compute everything in try catch to catch any issues
        try:
            # Get Phase
            phase = self.get_object()

            # Get Competition factsheet
            fact_sheet_keys = _get_factsheet_keys(phase)

            # Get Leaderboard
            leaderboard = _get_phase_leaderboard(phase)

            # Get leaderboard columns
            columns = _get_leaderboard_columns(leaderboard)

            # Get phase tasks
            tasks = _get_phase_tasks(phase)

            # Get detailed result settings
            detailed_result_settings = _get_detailed_result_settings(phase)

            # Get Leaderboard Submissions
            submissions = _get_leaderboard_submissions(phase, leaderboard, columns)

            # Prepare leaderboard tasks
            leaderboard_tasks = _prepare_leaderboard_tasks(tasks)

            # Prepare Leaderboard columns
            leaderboard_columns = _prepare_leaderboard_columns(columns)

            # Prepare leaderboard submissions
            leaderboard_submissions = _prepare_leaderboard_submissions(fact_sheet_keys, tasks, columns, submissions)

            response = {
                "title": leaderboard.title,
                "fact_sheet_keys": fact_sheet_keys,
                "tasks": leaderboard_tasks,
                "columns": leaderboard_columns,
                "submissions": leaderboard_submissions,
                "show_detailed_result": detailed_result_settings["enable_detailed_results"] and detailed_result_settings["show_detailed_results_in_leaderboard"]
            }

            return Response(response)

        except ValidationError as e:
            logger.error(f"Leaderboard Error --- {e}")
            return Response({"error": str(e.detail[0])}, status=status.HTTP_400_BAD_REQUEST)  # Extract first error message
        except Exception as e:
            logger.error(f"Leaderboard Error --- {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
