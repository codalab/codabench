from django.db.models import Subquery, OuterRef, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers.competitions import CompetitionSerializer, CompetitionSerializerSimple, PhaseSerializer, \
    CompetitionCreationTaskStatusSerializer, CompetitionDetailSerializer, CompetitionParticipantSerializer
from competitions.models import Competition, Phase, CompetitionCreationTaskStatus, Submission, CompetitionParticipant
from competitions.utils import get_popular_competitions, get_featured_competitions
from profiles.models import User
from utils.data import make_url_sassy
from utils.email import codalab_send_mail


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
            sub_query = CompetitionParticipant.objects.filter(
                competition=OuterRef('pk'),
                user=self.request.user
            ).values_list('status')[:1]
            qs = qs.annotate(participant_status=Subquery(sub_query))

        qs = qs.order_by('created_when')

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return CompetitionSerializerSimple
        elif self.request.method == 'GET':
            return CompetitionDetailSerializer
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

    @action(detail=True, methods=('POST',))
    def register(self, request, pk):
        competition = self.get_object()
        user = request.user
        participant = CompetitionParticipant.objects.create(competition=competition, user=user)
        if competition.registration_auto_approve:
            participant.status = 'approved'
        else:
            to = [competition.created_by.email] + [collab.email for collab in competition.collaborators.all()]
            subject = f'Registration request for {competition.title}'
            message = f'{user.username} has requested permission to join your competition: {competition.title}.'
            codalab_send_mail(subject=subject, message=message, recipient_list=to)
            participant.status = 'pending'

        participant.save()
        return Response({'participant_status': participant.status}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('GET',))
    def get_files(self, request, pk):
        qs_helper = Competition.objects.select_related(
            'created_by'
        ).prefetch_related(
            'dumps__dataset',
        )
        competition = qs_helper.get(id=pk)
        if request.user != competition.created_by and request.user not in competition.collaborators.all():
            raise PermissionDenied("You don't have access to the competition files")
        bundle = competition.bundle_dataset
        files = {
            'dumps': []
        }
        if bundle:
            files['bundle'] = {
                'name': bundle.name,
                'url': bundle.make_url_sassy(bundle.data_file.name)
            }
        for dump in competition.dumps.all():
            files['dumps'].append({'name': dump.dataset.name, 'url': make_url_sassy(dump.dataset.data_file.name)})
        return Response(files)


@api_view(['GET'])
@permission_classes((AllowAny,))
def front_page_competitions(request):
    popular_comps = get_popular_competitions()
    featured_comps = get_featured_competitions(excluded_competitions=popular_comps)
    popular_comps_serializer = CompetitionSerializerSimple(popular_comps, many=True)
    featured_comps_serializer = CompetitionSerializerSimple(featured_comps, many=True)
    return Response(data={
        "popular_comps": popular_comps_serializer.data,
        "featured_comps": featured_comps_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny,))
def by_the_numbers(request):
    data = Competition.objects.aggregate(
        count=Count('*'),
        published_comps=Count('pk', filter=Q(published=True)),
        unpublished_comps=Count('pk', filter=Q(published=False)),
    )

    total_competitions = data['count']
    public_competitions = data['published_comps']
    private_competitions = data['unpublished_comps']
    users = User.objects.all().count()
    competition_participants = CompetitionParticipant.objects.all().count()
    submissions = Submission.objects.all().count()

    return Response([
        {'label': "Total Competitions", 'count': total_competitions},
        {'label': "Public Competitions", 'count': public_competitions},
        {'label': "Private Competitions", 'count': private_competitions},
        {'label': "Users", 'count': users},
        {'label': "Competition Participants", 'count': competition_participants},
        {'label': "Submissions", 'count': submissions},
    ])


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
        submissions = phase.submissions.all()
        for submission in submissions:
            submission.re_run()
        rerun_count = len(submissions)
        return Response({"count": rerun_count})


class CompetitionCreationTaskStatusViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = CompetitionCreationTaskStatus.objects.all()
    serializer_class = CompetitionCreationTaskStatusSerializer
    lookup_field = 'dataset__key'


class CompetitionParticipantViewSet(ModelViewSet):
    queryset = CompetitionParticipant.objects.all()
    serializer_class = CompetitionParticipantSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('user__username', 'user__email', 'status', 'competition')
    search_fields = ('user__username', 'user__email',)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('user').order_by('user__username')
        return qs
