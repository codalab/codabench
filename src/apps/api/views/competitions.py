from rest_framework.viewsets import ModelViewSet

from api import serializers
from competitions.models import Competition


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = serializers.CompetitionSerializer

    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
