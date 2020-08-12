import json
import uuid

from django.db.models import Q, OuterRef
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

from api.serializers.submissions import SubmissionCreationSerializer, SubmissionSerializer, SubmissionFilesSerializer
from competitions.models import Submission, Phase, CompetitionParticipant
from leaderboards.models import SubmissionScore, Column


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all().order_by('-pk')
    permission_classes = []
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('phase__competition', 'phase', 'status')
    search_fields = ('data__data_file', 'description', 'name', 'owner__username')
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [renderers.CSVRenderer]

    def check_object_permissions(self, request, obj):
        if self.request and self.request.method in ('POST', 'PUT', 'PATCH'):
            try:
                if uuid.UUID(request.data.get('secret')) != obj.secret:
                    raise PermissionDenied("Submission secrets do not match")
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

            if not self.request.user.is_superuser and not self.request.user.is_staff:
                # if you're the creator of the submission or a collaborator on the competition
                qs = qs.filter(
                    Q(owner=self.request.user) |
                    Q(phase__competition__created_by=self.request.user) |
                    Q(phase__competition__collaborators__in=[self.request.user.pk])
                )
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
            )
        return qs

    def destroy(self, request, *args, **kwargs):
        submission = self.get_object()

        if request.user != submission.owner and not self.has_admin_permission(request.user, submission):
            raise PermissionDenied("Cannot interact with submission you did not make")

        self.perform_destroy(submission)
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        return user.is_superuser or user in competition.all_organizers

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

    @action(detail=True, methods=('GET',))
    def re_run_submission(self, request, pk):
        submission = self.get_object()
        if not self.has_admin_permission(request.user, submission):
            raise PermissionDenied('You do not have permission to re-run submissions')
        submission.re_run()
        return Response({})

    @action(detail=True, methods=('GET',))
    def get_details(self, request, pk):
        submission = super().get_object()

        if submission.phase.hide_output:
            if not self.has_admin_permission(self.request.user, submission):
                raise PermissionDenied("Cannot access submission details while phase marked to hide output.")

        data = SubmissionFilesSerializer(submission, context=self.get_serializer_context()).data
        return Response(data)

    @action(detail=True, methods=('GET',))
    def toggle_public(self, request, pk):
        submission = super().get_object()
        if not self.has_admin_permission(request.user, submission):
            raise PermissionDenied(f'You do not have permission to publish this submissions')
        is_public = not submission.is_public
        submission.data.is_public = is_public
        submission.data.save(send=False)
        submission.is_public = is_public
        submission.save()
        return Response({})


@api_view(['POST'])
@permission_classes((AllowAny, ))  # permissions are checked via the submission secret
def upload_submission_scores(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)

    data = json.loads(request.body)

    try:
        if uuid.UUID(data.get("secret")) != submission.secret:
            raise PermissionDenied("Submission secrets do not match")
    except TypeError:
        raise ValidationError("Secret not a valid UUID")

    competition_columns = submission.phase.competition.leaderboards.values_list('columns__key', flat=True)

    for column_key, score in data["scores"].items():
        if column_key not in competition_columns:
            continue
        score = SubmissionScore.objects.create(
            score=score,
            column=Column.objects.get(leaderboard__competition=submission.phase.competition, key=column_key)
        )
        submission.scores.add(score)
        if submission.parent:
            submission.parent.scores.add(score)
            submission.parent.calculate_scores()
        else:
            submission.calculate_scores()

    return Response()


@api_view(('GET',))
def can_make_submission(request, phase_id):
    phase = get_object_or_404(Phase, id=phase_id)
    user_is_approved = phase.competition.participants.filter(user=request.user, status=CompetitionParticipant.APPROVED).exists()

    if request.user.is_bot and phase.competition.allow_robot_submissions and not user_is_approved:
        CompetitionParticipant.objects.create(user=request.user, competition=phase.competition, status=CompetitionParticipant.APPROVED)
        user_is_approved = True

    if user_is_approved:
        can_make_submission, reason_why_not = phase.can_user_make_submissions(request.user)
    else:
        can_make_submission, reason_why_not = False, "User not approved to participate in this competition"

    return Response({
        "can": can_make_submission,
        "reason": reason_why_not,
    })
