import uuid

from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers import competitions as serializers
from competitions.models import Competition, Phase, Submission, CompetitionCreationTaskStatus


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = serializers.CompetitionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter to only see competitions you own
        mine = self.request.query_params.get('mine', None)

        if mine:
            qs = qs.filter(created_by=self.request.user)

        return qs

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "created_by": self.request.user
        }


class PhaseViewSet(ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = serializers.PhaseSerializer
    # TODO! Security, who can access/delete/etc this?


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all()
    permission_classes = []
    # TODO! Security, who can access/delete/etc this?

    def check_object_permissions(self, request, obj):
        print(request.data.get('secret'))
        print(obj.secret)
        try:
            if uuid.UUID(request.data.get('secret')) != obj.secret:
                raise PermissionDenied("Submission secrets do not match")
        except TypeError:
            raise ValidationError("Secret not a valid UUID")

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "owner": self.request.user
        }

    def get_serializer_class(self):
        if self.request and self.request.method == 'POST':
            return serializers.SubmissionCreationSerializer
        else:
            return serializers.SubmissionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user != instance.owner:
            raise PermissionDenied("Cannot interact with submission you did not make")

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompetitionCreationTaskStatusViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = CompetitionCreationTaskStatus.objects.all()
    serializer_class = serializers.CompetitionCreationTaskStatusSerializer
    lookup_field = 'dataset__key'
