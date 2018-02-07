from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.serializers import competitions as serializers
from competitions.models import Competition, Phase, Submission


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
        return {
            "created_by": self.request.user
        }


class PhaseViewSet(ReadOnlyModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = serializers.PhaseSerializer


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter to only see competitions you own
        # mine = self.request.query_params.get('mine', None)

        # if mine:
        qs = qs.filter(owner=self.request.user)

        return qs

    def get_serializer_context(self):
        return {
            "owner": self.request.user
        }
