from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers.competitions import CompetitionSerializer, CompetitionSerializerSimple, PhaseSerializer, \
    CompetitionCreationTaskStatusSerializer
from competitions.models import Competition, Phase, CompetitionCreationTaskStatus

User = get_user_model()


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter to only see competitions you own
        mine = self.request.query_params.get('mine', None)

        if mine:
            qs = qs.filter(created_by=self.request.user)

        participating_in = self.request.query_params.get('participating_in', None)

        if participating_in:
            qs = qs.filter(id__in=User.objects.get(id=self.request.user.id).submission.all().values('phase__competition'))


        # On GETs lets optimize the query to reduce DB calls
        if self.request.method == 'GET':
            qs = qs.select_related('created_by')
            qs = qs.prefetch_related(
                'phases',
                'pages',
                'leaderboards',
                'leaderboards__columns',
                'collaborators',
            )

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return CompetitionSerializerSimple
        else:
            return CompetitionSerializer

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "created_by": self.request.user
        }

    def destroy(self, request, *args, **kwargs):
        if request.user != self.get_object().created_by:
            raise PermissionDenied("You cannot delete competitions that you didn't create")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=('POST',))
    def toggle_publish(self, request, pk):
        competition = self.get_object()
        if request.user != competition.created_by and request.user not in competition.collaborators.all():
            raise PermissionDenied("You don't have access to publish this competition")
        competition.published = not competition.published
        competition.save()
        return Response('done')


class PhaseViewSet(ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    # TODO! Security, who can access/delete/etc this?


class CompetitionCreationTaskStatusViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = CompetitionCreationTaskStatus.objects.all()
    serializer_class = CompetitionCreationTaskStatusSerializer
    lookup_field = 'dataset__key'
