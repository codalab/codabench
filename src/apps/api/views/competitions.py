from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import ViewSet, ModelViewSet, GenericViewSet
from rest_framework.views import APIView

from api import serializers
from competitions.models import Competition


# class CompetitionViewSet(ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView):
# class CompetitionViewSet(APIView):
class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = serializers.CompetitionSerializer

    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
