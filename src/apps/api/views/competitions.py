from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers.competitions import CompetitionSerializer, PhaseSerializer, CompetitionCreationTaskStatusSerializer
from competitions.models import Competition, Phase, CompetitionCreationTaskStatus


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

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
    serializer_class = PhaseSerializer
    # TODO! Security, who can access/delete/etc this?


class CompetitionCreationTaskStatusViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = CompetitionCreationTaskStatus.objects.all()
    serializer_class = CompetitionCreationTaskStatusSerializer
    lookup_field = 'dataset__key'
