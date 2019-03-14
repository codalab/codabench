from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers.competitions import CompetitionSerializer, CompetitionSerializerSimple, PhaseSerializer, \
    CompetitionCreationTaskStatusSerializer
from competitions.models import Competition, Phase, CompetitionCreationTaskStatus


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
            qs = qs.filter(participants__user=self.request.user, participants__status="approved")

        # On GETs lets optimize the query to reduce DB calls
        if self.request.method == 'GET' and self.action != 'list':
            qs = qs.select_related('created_by')
            qs = qs.prefetch_related(
                'phases',
                'pages',
                'leaderboards',
                'leaderboards__columns',
                'collaborators',
            )

        qs = qs.order_by('created_when')

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return CompetitionSerializerSimple
        else:
            return CompetitionSerializer

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        # TODO: what is this doing? do we still need it?
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
        return Response({"published": competition.published})


class PhaseViewSet(ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    # TODO! Security, who can access/delete/etc this?

    @action(detail=True, url_name='rerun_submissions')
    def rerun_submissions(self, request, pk):
        phase = self.get_object()
        comp = phase.competition
        if request.user not in [comp.created_by] + list(comp.collaborators.all()) and not request.user.is_superuser:
            raise PermissionDenied('You do not have permission to re-run submissions')
        for submission in phase.submissions.all():
            submission.re_run()
        rerun_count = phase.submissions.count() / 2
        # Divide by 2 since we just re_ran everything by duplicating the submission, doubling the count
        return Response({"count": rerun_count})


class CompetitionCreationTaskStatusViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = CompetitionCreationTaskStatus.objects.all()
    serializer_class = CompetitionCreationTaskStatusSerializer
    lookup_field = 'dataset__key'
