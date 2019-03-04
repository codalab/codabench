import json
import uuid

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
from competitions.models import Submission, Phase
from leaderboards.models import SubmissionScore, Column


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all().order_by('-pk')
    permission_classes = []
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('phase__competition', 'phase', 'status')
    search_fields = ('data__data_file', 'description', 'name', 'owner__username')
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [renderers.CSVRenderer]
    # TODO! Security, who can access/delete/etc this?

    def check_object_permissions(self, request, obj):
        if self.request and self.request.method in ('POST', 'PUT', 'PATCH'):
            try:
                if uuid.UUID(request.data.get('secret')) != obj.secret:
                    raise PermissionDenied("Submission secrets do not match")
            except TypeError:
                raise ValidationError(f"Secret: ({request.data.get('secret')}) not a valid UUID")

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "owner": self.request.user
        }

    def get_serializer_class(self):
        if self.request and self.request.method in ('POST', 'PUT', 'PATCH'):
            return SubmissionCreationSerializer
        else:
            return SubmissionSerializer

    def get_queryset(self):
        # On GETs lets optimize the query to reduce DB calls
        qs = super().get_queryset()
        if self.request.method == 'GET':
            qs = qs.select_related('phase', 'participant')
            qs = qs.prefetch_related(
                'scores',
                'scores__column',
                'data'
            )
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user != instance.owner:
            raise PermissionDenied("Cannot interact with submission you did not make")

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_renderer_context(self):
        """We override this to pass some context to the CSV renderer"""
        context = super().get_renderer_context()
        # The CSV renderer will only include these fields in context["header"]
        context["header"] = (
            'owner',
            'created_when',
            'status',
            'score',
            'appear_on_leaderboards',
            'phase',
        )
        # Human names for the fields
        context["labels"] = {
            'owner': 'Owner',
            'created_when': 'Created When',
            'status': 'Status',
            'score': 'Score',
            'appear_on_leaderboards': 'Appears on Leaderboard',
            'phase': 'Phase',
        }
        return context

    @action(detail=True, methods=('GET',))
    def cancel_submission(self, request, pk):
        instance = self.get_object()
        instance.cancel()
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, methods=('GET',))
    def re_run_submission(self, request, pk):
        submission = self.get_object()
        competition = submission.phase.competition
        if not request.user.is_superuser and request.user != competition.created_by and request.user not in competition.collaborators.all():
            raise PermissionDenied('You do not have permission to re-run submissions')
        submission.re_run()
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, methods=('GET',))
    def get_logs(self, request, pk):
        instance = super().get_object()
        data = SubmissionFilesSerializer(instance).data
        return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny, ))  # permissions are checked via the submission secret
def upload_submission_scores(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)

    data = json.loads(request.body)
    print(request.body)

    try:
        if uuid.UUID(data.get("secret")) != submission.secret:
            raise PermissionDenied("Submission secrets do not match")
    except TypeError:
        raise ValidationError("Secret not a valid UUID")

    for column_key, score in data["scores"].items():
        SubmissionScore.objects.create(
            submission=submission,
            score=score,
            column=Column.objects.get(leaderboard__competition=submission.phase.competition, key=column_key)
        )

    return Response()


@api_view(('GET',))
def can_make_submission(request, phase_id):
    # TODO: Check that user is in competition

    phase = get_object_or_404(Phase, id=phase_id)

    can_make_submission, reason_why_not = phase.can_user_make_submissions(request.user)

    return Response({
        "can": can_make_submission,
        "reason": reason_why_not,
    })
