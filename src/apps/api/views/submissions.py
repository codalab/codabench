import json
import uuid
import logging

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet
from rest_framework_csv import renderers
from django.core.files.base import ContentFile
from django.http import StreamingHttpResponse

from profiles.models import Organization, Membership
from tasks.models import Task
from api.serializers.submissions import SubmissionCreationSerializer, SubmissionSerializer, SubmissionFilesSerializer
from competitions.models import Submission, SubmissionDetails, Phase, CompetitionParticipant
from leaderboards.strategies import put_on_leaderboard_by_submission_rule
from leaderboards.models import SubmissionScore, Column, Leaderboard


logger = logging.getLogger()


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all().order_by('-pk')
    permission_classes = []
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('phase__competition', 'phase', 'status', 'is_soft_deleted')
    search_fields = ('data__data_file', 'description', 'name', 'owner__username')
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [renderers.CSVRenderer]

    def check_object_permissions(self, request, obj):
        if self.action in ['submission_leaderboard_connection']:
            if obj.is_specific_task_re_run:
                raise PermissionDenied("Cannot add task-specific submission re-runs to leaderboards.")
            return
        if self.request and self.request.method in ('POST', 'PUT', 'PATCH'):
            dir(self.request)
            # Set hostname of submission
            if "status_details" in self.request.data.keys():
                # Check ingestion hostname
                if request.data['status_details'].find('ingestion_hostname') != -1:
                    hostname = request.data['status_details'].replace('ingestion_hostname-', '')
                    obj.ingestion_worker_hostname = hostname
                    obj.save()
                # Check socring hostname
                if request.data['status_details'].find('scoring_hostname') != -1:
                    hostname = request.data['status_details'].replace('scoring_hostname-', '')
                    obj.scoring_worker_hostname = hostname
                    obj.save()

            # check if type is in request data. type can have the following values
            # - Docker_Image_Pull_Fail
            # - Execution_Time_Limit_Exceeded
            if "type" in self.request.data.keys():

                if request.data["type"] in ["Docker_Image_Pull_Fail", "Execution_Time_Limit_Exceeded"]:

                    # Get the error message
                    error_message = request.data['error_message']

                    # Set file name to ingestion std error as default
                    error_file_name = "prediction_ingestion_stderr"

                    # Change error file name to scoring_stderr when error occurs during scoring
                    if request.data.get("is_scoring", "False") == "True":
                        error_file_name = "scoring_stderr"

                    try:
                        # Get submission detail for this submission
                        submission_detail = SubmissionDetails.objects.get(
                            name=error_file_name,
                            submission=obj,
                        )

                        # Read the existing content from the file
                        existing_content = submission_detail.data_file.read().decode("utf-8")

                        # Append the new error message to the existing content
                        modified_content = existing_content + "\n" + error_message

                        # write error message to the file
                        submission_detail.data_file.save(submission_detail.data_file.name, ContentFile(modified_content.encode("utf-8")))

                    except SubmissionDetails.DoesNotExist:
                        logger.warning("SubmissionDetails object not found.")

            not_bot_user = self.request.user.is_authenticated and not self.request.user.is_bot

            if self.action in ['update_fact_sheet', 'run_submission', 're_run_submission']:
                # get_queryset will stop us from re-running something we're not supposed to
                pass
            elif not self.request.user.is_authenticated or not_bot_user:
                try:
                    if request.data.get('secret') is None or uuid.UUID(request.data.get('secret')) != obj.secret:
                        raise PermissionDenied("Submission secrets do not match")
                    if request.data.get('task'):
                        raise PermissionDenied("Submission task cannot be updated")
                except TypeError:
                    raise ValidationError(f"Secret: ({request.data.get('secret')}) not a valid UUID")

    def get_serializer_class(self):
        if self.request and self.request.method in ('POST', 'PUT', 'PATCH'):
            return SubmissionCreationSerializer
        else:
            return SubmissionSerializer

    def get_queryset(self):
        # On GETs lets optimize the query to reduce DB calls
        qs = super().get_queryset()
        if self.request.method == 'GET':
            if not self.request.user.is_authenticated:
                return Submission.objects.none()

            # Check if admin is requesting to see soft-deleted submissions
            show_is_soft_deleted = self.request.query_params.get('show_is_soft_deleted', 'false').lower() == 'true'

            if not self.request.user.is_superuser and not self.request.user.is_staff and not self.request.user.is_bot:
                # if you're the creator of the submission or a collaborator on the competition
                qs = qs.filter(
                    Q(owner=self.request.user) |
                    Q(phase__competition__created_by=self.request.user) |
                    Q(phase__competition__collaborators__in=[self.request.user.pk])
                ).distinct()

            # By default, exclude soft-deleted submissions unless explicitly requested by an admin
            if not show_is_soft_deleted:
                qs = qs.filter(is_soft_deleted=False)

            qs = qs.select_related(
                'phase',
                'phase__competition',
                'participant',
                'participant__user',
                'owner',
                'data',
            ).prefetch_related(
                'children',
                'scores',
                'scores__column',
                'task',
            )
        elif self.action in ['delete_many', 're_run_many_submissions']:
            try:
                pks = list(self.request.data)
            except TypeError as err:
                raise ValidationError(f'Error {err}')
            qs = qs.filter(pk__in=pks)
            if not self.request.user.is_superuser and not self.request.user.is_staff:
                if qs.filter(
                    Q(owner=self.request.user) |
                    Q(phase__competition__created_by=self.request.user) |
                    Q(phase__competition__collaborators__in=[self.request.user.pk])
                ) is not qs:
                    ValidationError("Request Contained Submissions you don't have authorization for")
            if self.action in ['re_run_many_submissions']:
                print(f'debug {qs}')
                print(f'debug {qs.first().status}')
                qs = qs.filter(status__in=[Submission.FINISHED, Submission.FAILED, Submission.CANCELLED])
                print(f'debug {qs}')
        return qs

    def create(self, request, *args, **kwargs):
        if 'organization' in request.data and request.data['organization'] is not None:
            organization = get_object_or_404(Organization, pk=request.data['organization'])
            try:
                membership = organization.membership_set.get(user=request.user)
            except Membership.DoesNotExist:
                raise ValidationError('You must be apart of a organization to submit for them')
            if membership.group not in Membership.PARTICIPANT_GROUP:
                raise ValidationError('You do not have participant permissions for this group')
        return super(SubmissionViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        submission = self.get_object()

        if request.user != submission.owner and not self.has_admin_permission(request.user, submission):
            raise PermissionDenied("Cannot interact with submission you did not make")

        self.perform_destroy(submission)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('DELETE',))
    def soft_delete(self, request, pk):
        submission = self.get_object()

        # Check if submission exists
        if not submission:
            return Response({'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if owner is requesting soft delete
        if submission.owner != request.user:
            return Response({'error': 'You are not allowed to delete this submission'}, status=status.HTTP_403_FORBIDDEN)

        # Check if submission is finished and on the leaderboard
        if submission.status == Submission.FINISHED and submission.on_leaderboard:
            return Response({'error': 'You are not allowed to delete a leaderboard submission'}, status=status.HTTP_403_FORBIDDEN)

        # Check if submission is in running state
        if submission.status not in [Submission.FAILED, Submission.FINISHED, Submission.CANCELLED]:
            return Response({'error': 'You are not allowed to delete a running submission'}, status=status.HTTP_403_FORBIDDEN)

        # Check if submission is not already soft deleted
        if submission.is_soft_deleted:
            return Response({'error': 'Submission already deleted'}, status=status.HTTP_400_BAD_REQUEST)

        # soft delete submission and return success response
        submission.soft_delete()
        return Response({'message': 'Submission deleted successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=('DELETE',))
    def delete_many(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not qs:
            return Response({'Submission search returned empty'}, status=status.HTTP_404_NOT_FOUND)
        for submission in qs:
            submission.delete()  # This will trigger the model's `delete` method
        return Response({})

    def get_renderer_context(self):
        """We override this to pass some context to the CSV renderer"""
        context = super().get_renderer_context()
        # The CSV renderer will only include these fields in context["header"]
        # Human names for the fields
        context["labels"] = {
            'owner': 'Owner',
            'created_when': 'Created When',
            'status': 'Status',
            'phase_name': 'Phase',
        }
        context["header"] = [k for k in context["labels"].keys()]
        return context

    def has_admin_permission(self, user, submission):
        competition = submission.phase.competition
        return user.is_authenticated and (user.is_superuser or user in competition.all_organizers or user.is_bot)

    @action(detail=True, methods=('POST', 'DELETE'))
    def submission_leaderboard_connection(self, request, pk):

        # get submission
        submission = self.get_object()

        # get submission phase
        phase = submission.phase

        # only super user, owner of submission and competition organizer can proceed
        if not (
            request.user.is_superuser or
            request.user == submission.owner or
            request.user in phase.competition.all_organizers
        ):
            raise PermissionDenied("You cannot perform this action, contact the competition organizer!")

        # only super user and with these leaderboard rules (FORCE_LAST, FORCE_BEST, FORCE_LATEST_MULTIPLE) can proceed
        if submission.phase.leaderboard.submission_rule in Leaderboard.AUTO_SUBMISSION_RULES and not request.user.is_superuser:
            raise PermissionDenied("Users are not allowed to edit the leaderboard on this Competition")

        if request.method == 'POST':
            # Removing any existing submissions on leaderboard unless multiples are allowed
            if submission.phase.leaderboard.submission_rule != Leaderboard.ADD_DELETE_MULTIPLE:
                Submission.objects.filter(phase=phase, owner=submission.owner).update(leaderboard=None)
            leaderboard = phase.leaderboard
            if submission.has_children:
                Submission.objects.filter(parent=submission).update(leaderboard=leaderboard)
            else:
                submission.leaderboard = leaderboard
                submission.save()

        if request.method == 'DELETE':
            if submission.phase.leaderboard.submission_rule not in [Leaderboard.ADD_DELETE, Leaderboard.ADD_DELETE_MULTIPLE]:
                raise PermissionDenied("You are not allowed to remove a submission on this phase")
            submission.leaderboard = None
            submission.save()
            Submission.objects.filter(parent=submission).update(leaderboard=None)

        return Response({})

    @action(detail=True, methods=('GET',))
    def cancel_submission(self, request, pk):
        submission = self.get_object()
        if not self.has_admin_permission(request.user, submission):
            if submission.owner != request.user:
                raise PermissionDenied(f'You do not have permission to cancel submissions')
        for child in submission.children.all():
            child.cancel()
        canceled = submission.cancel()
        return Response({'canceled': canceled})

    @action(detail=True, methods=('POST',))
    def run_submission(self, request, pk):
        submission = self.get_object()

        # Only organizer of the competition can run the submission
        if not self.has_admin_permission(request.user, submission):
            raise PermissionDenied('You do not have permission to run this submission')

        # Allow only to run a submission with status `Submitting`
        if submission.status != Submission.SUBMITTING:
            raise PermissionDenied('Cannot run a submission which is not in submitting status')

        new_sub = submission.run()
        return Response({'id': new_sub.id})

    @action(detail=True, methods=('POST',))
    def re_run_submission(self, request, pk):
        submission = self.get_object()
        task_key = request.query_params.get('task_key')

        if not self.has_admin_permission(request.user, submission):
            raise PermissionDenied('You do not have permission to re-run submissions')

        # We want to avoid re-running a submission that isn't finished yet, because the tasks associated
        # with the submission and maybe other important details have not been finalized yet. I.e. if you
        # rapidly click the "re-run submission" button, a submission may not have been processed by a
        # site worker and be in a funky state (race condition) -- this should resolve that
        if submission.status not in (Submission.FINISHED, Submission.FAILED, Submission.CANCELLED):
            raise PermissionDenied('Cannot request a re-run on a submission that has not finished processing.')

        # Rerun submission on different task. Will flag submission with is_specific_task_re_run=True
        if task_key:
            rerun_kwargs = {
                'task': get_object_or_404(Task, key=task_key),
            }
        else:
            rerun_kwargs = {}

        new_sub = submission.re_run(**rerun_kwargs)
        if new_sub is None:
            # return error
            return Response({
                "error_msg": "You cannot rerun this submission because one or more tasks this submission was running are deleted, resubmit the submission or contact the competition organizer!"},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            return Response({'id': new_sub.id})

    @action(detail=False, methods=('POST',))
    def re_run_many_submissions(self, request):
        qs = self.get_queryset()
        for submission in qs:
            submission.re_run()
        return Response({})

    @action(detail=False, methods=['get'])
    def download_many(self, request):
        """
        Download a ZIP containing several submissions.
        """
        pks = request.query_params.get('pks')
        if pks:
            pks = json.loads(pks)  # Convert JSON string to list
        else:
            return Response({"error": "`pks` query parameter is required"}, status=400)

        # Get submissions
        submissions = Submission.objects.filter(pk__in=pks).select_related(
            "owner",
            "phase__competition",
            "phase__competition__created_by",
        ).prefetch_related("phase__competition__collaborators")
        if submissions.count() != len(pks):
            return Response({"error": "One or more submission IDs are invalid"}, status=404)

        # Check permissions
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to download submissions")
        # Allow admins
        if request.user.is_superuser or request.user.is_staff:
            allowed = True
        else:
            # Build one Q object for "owner OR organizer"
            organiser_q = (
                Q(phase__competition__created_by=request.user) |
                Q(phase__competition__collaborators=request.user)
            )
            # Submissions that violate the rule
            disallowed = submissions.exclude(Q(owner=request.user) | organiser_q)
            allowed = not disallowed.exists()
        if not allowed:
            raise PermissionDenied(
                "You do not have permission to download one or more of the requested submissions"
            )

        # Download
        from competitions.tasks import stream_batch_download
        in_memory_zip = stream_batch_download(pks)
        response = StreamingHttpResponse(in_memory_zip, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="bulk_submissions.zip"'
        return response

    @action(detail=True, methods=('GET',))
    def get_details(self, request, pk):
        submission = super().get_object()
        if submission.phase.hide_output:
            if not self.has_admin_permission(request.user, submission):
                raise PermissionDenied("Cannot access submission details while phase marked to hide output.")

        data = SubmissionFilesSerializer(submission, context=self.get_serializer_context()).data
        return Response(data)

    @action(detail=True, methods=('GET',))
    def get_detail_result(self, request, pk):
        submission = Submission.objects.get(pk=pk)
        # Check if competition show visualization is true
        if submission.phase.competition.enable_detailed_results:
            # get submission's competition approved participants
            approved_participants = submission.phase.competition.participants.filter(status=CompetitionParticipant.APPROVED)
            participant_usernames = [participant.user.username for participant in approved_participants]

            # check if in this competition
            # user is collaborator
            # or
            # user is approved participant
            # or
            # user is creator
            # or
            # user is super user
            if request.user in submission.phase.competition.collaborators.all() or\
                    request.user.username in participant_usernames or\
                    request.user == submission.phase.competition.created_by or\
                    request.user.is_superuser:

                data = SubmissionFilesSerializer(submission, context=self.get_serializer_context()).data
                return Response(data["detailed_result"], status=status.HTTP_200_OK)

            else:
                return Response({
                    "error_msg": "You do not have permission to see the detailed result. Participate in this competition to view result."},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response({
                "error_msg": "Detailed results are disable for this competition!"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=('GET',))
    def toggle_public(self, request, pk):
        submission = super().get_object()
        if not submission.phase.competition.can_participants_make_submissions_public:
            raise PermissionDenied("You do not have permission to make this submissions public/private")
        is_public = not submission.is_public
        submission.data.is_public = is_public
        submission.data.save(send=False)
        submission.is_public = is_public
        submission.save()
        return Response({})

    @action(detail=True, methods=('PATCH',))
    def update_fact_sheet(self, request, pk):
        if not isinstance(request.data, dict):
            if isinstance(request.data, str):
                try:
                    request_data = json.loads(request.data)
                except ValueError:
                    return ValidationError('Invalid JSON')
        else:
            request_data = request.data
        request_submission = super().get_object()
        top_level_submission = request_submission.parent or request_submission
        # Validate fact_sheet using serializer
        data = self.get_serializer(top_level_submission).data
        data['fact_sheet_answers'] = request.data
        serializer = self.get_serializer(data=data, instance=top_level_submission)
        serializer.is_valid(raise_exception=True)
        # Use Queryset to update Submissions
        Submission.objects.filter(Q(parent=top_level_submission) | Q(id=top_level_submission.id)).update(fact_sheet_answers=request_data)
        return Response({})


@api_view(['POST'])
@permission_classes((AllowAny,))  # permissions are checked via the submission secret
def upload_submission_scores(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)
    submission_rule = submission.phase.leaderboard.submission_rule

    try:
        if uuid.UUID(request.data.get("secret")) != submission.secret:
            raise PermissionDenied("Submission secrets do not match")
    except TypeError:
        raise ValidationError("Secret not a valid UUID")

    if "scores" not in request.data:
        raise ValidationError("'scores' required.")

    competition_columns = submission.phase.leaderboard.columns.values_list('key', flat=True)

    for column_key, score in request.data.get("scores").items():
        if column_key not in competition_columns:
            continue
        score = SubmissionScore.objects.create(
            score=score,
            column=Column.objects.get(leaderboard=submission.phase.leaderboard, key=column_key)
        )
        submission.scores.add(score)
        if submission.parent:
            submission.parent.scores.add(score)
            submission.parent.calculate_scores()
        else:
            submission.calculate_scores()

    put_on_leaderboard_by_submission_rule(request, submission_pk, submission_rule)
    return Response()


@api_view(('GET',))
def can_make_submission(request, phase_id):
    phase = get_object_or_404(Phase, id=phase_id)
    user_is_approved = phase.competition.participants.filter(
        user=request.user,
        status=CompetitionParticipant.APPROVED
    ).exists()

    if request.user.is_bot and phase.competition.allow_robot_submissions and not user_is_approved:
        CompetitionParticipant.objects.create(
            user=request.user,
            competition=phase.competition,
            status=CompetitionParticipant.APPROVED
        )
        user_is_approved = True

    if user_is_approved:
        can_make_submission, reason_why_not = phase.can_user_make_submissions(request.user)
    else:
        can_make_submission, reason_why_not = False, "User not approved to participate in this competition"

    return Response({
        "can": can_make_submission,
        "reason": reason_why_not,
    })
