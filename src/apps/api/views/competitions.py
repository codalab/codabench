from rest_framework.viewsets import ModelViewSet

from api.serializers import competitions as serializers
from competitions.models import Competition, Phase, Submission


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = serializers.CompetitionSerializer

    # def post(self, *args, **kwargs):
    #     return super().post(*args, **kwargs)


class PhaseViewSet(ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = serializers.PhaseSerializer


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer
