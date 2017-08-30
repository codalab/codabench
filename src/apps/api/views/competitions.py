from rest_framework.generics import CreateAPIView, RetrieveAPIView, ListAPIView, DestroyAPIView
from rest_framework.viewsets import GenericViewSet

from api import serializers
from competitions.models import Competition, Phase, Submission


class CompetitionViewSet(ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView, GenericViewSet):
    queryset = Competition.objects.all()
    serializer_class = serializers.CompetitionSerializer

    # def post(self, *args, **kwargs):
    #     return super().post(*args, **kwargs)


class PhaseViewSet(ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView, GenericViewSet):
    queryset = Phase.objects.all()
    serializer_class = serializers.PhaseSerializer


class SubmissionViewSet(ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView, GenericViewSet):
    queryset = Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer
