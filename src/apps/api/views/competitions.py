import zipfile

from django.http import HttpResponse
from tempfile import SpooledTemporaryFile, NamedTemporaryFile

from django.db import IntegrityError
from django.db.models import Subquery, OuterRef, Count, Q, F, Case, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers.competitions import CompetitionSerializer, CompetitionSerializerSimple, PhaseSerializer, \
    CompetitionCreationTaskStatusSerializer, CompetitionDetailSerializer, CompetitionParticipantSerializer
from competitions.emails import send_participation_requested_emails, send_participation_accepted_emails, \
    send_participation_denied_emails, send_direct_participant_email
from competitions.models import Competition, Phase, CompetitionCreationTaskStatus, CompetitionParticipant, Submission
from competitions.tasks import batch_send_email, manual_migration
from competitions.utils import get_popular_competitions, get_featured_competitions
from leaderboards.models import Column, Leaderboard
from profiles.models import User
from utils.data import make_url_sassy

from api.permissions import IsOrganizerOrCollaborator


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_authenticated:

            # filter by competition_type first, 'competition' by default
            competition_type = self.request.query_params.get('type', Competition.COMPETITION)
            qs = qs.filter(competition_type=competition_type)

            # Filter to only see competitions you own
            mine = self.request.query_params.get('mine', None)

            if mine:
                qs = qs.filter(created_by=self.request.user)

            participating_in = self.request.query_params.get('participating_in', None)

            if participating_in:
                qs = qs.filter(participants__user=self.request.user, participants__status="approved")

            participant_status_query = CompetitionParticipant.objects.filter(
                competition=OuterRef('pk'),
                user=self.request.user
            ).values_list('status')[:1]
            qs = qs.annotate(participant_status=Subquery(participant_status_query))

        # On GETs lets optimize the query to reduce DB calls
        if self.request.method == 'GET':
            qs = qs.select_related('created_by')
            if self.action != 'list':
                qs = qs.select_related('created_by')
                qs = qs.prefetch_related(
                    'phases',
                    'phases__submissions',
                    'phases__tasks',
                    'phases__tasks__solutions',
                    'phases__tasks__solutions__data',
                    'pages',
                    'leaderboards',
                    'leaderboards__columns',
                    'collaborators',
                )
                qs = qs.annotate(participant_count=Count(F('participants'), distinct=True))
                qs = qs.annotate(submission_count=Count(
                    # Filtering out children submissions so we only count distinct submissions
                    Case(
                        When(phases__submissions__parent__isnull=True, then='phases__submissions__pk')
                    ), distinct=True)
                )

        search_query = self.request.query_params.get('search')
        if search_query:
            qs = qs.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

        qs = qs.order_by('created_when')
        return qs

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOrganizerOrCollaborator]
        elif self.action in ['create']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['retrieve', 'list']:
            self.permission_classes = [AllowAny]
        return [permission() for permission in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'list':
            return CompetitionSerializerSimple
        elif self.request.method == 'GET':
            return CompetitionDetailSerializer
        else:
            return CompetitionSerializer

    def create(self, request, *args, **kwargs):
        """Mostly a copy of the underlying base create, however we return some additional data
        in the response to remove a GET from the frontend"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Re-do serializer in detail version (i.e. for Collaborator data)
        context = self.get_serializer_context()
        serializer = CompetitionDetailSerializer(serializer.instance, context=context)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Mostly a copy of the underlying base update, however we return some additional data
        in the response to remove a GET from the frontend"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # Re-do serializer in detail version (i.e. for Collaborator data)
        context = self.get_serializer_context()
        serializer = CompetitionDetailSerializer(serializer.instance, context=context)
        return Response(serializer.data)

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
        try:
            participant = CompetitionParticipant.objects.create(competition=competition, user=user)
        except IntegrityError:
            raise ValidationError("You already applied for participation in this competition!")

        if user in competition.all_organizers:
            participant.status = 'approved'
        elif competition.registration_auto_approve:
            participant.status = 'approved'
            send_participation_accepted_emails(participant)
        else:
            participant.status = 'pending'
            send_participation_requested_emails(participant)

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
        if request.user != competition.created_by and request.user not in competition.collaborators.all() and not request.user.is_superuser:
            raise PermissionDenied("You don't have access to the competition files")
        bundle = competition.bundle_dataset
        files = {
            'dumps': []
        }
        if bundle:
            files['bundle'] = {
                'name': bundle.name,
                'url': make_url_sassy(bundle.data_file.name)
            }
        for dump in competition.dumps.all():
            files['dumps'].append({'name': dump.dataset.name, 'url': make_url_sassy(dump.dataset.data_file.name)})
        return Response(files)

    @action(detail=True, methods=('POST',))
    def email_all_participants(self, request, pk):
        comp = self.get_object()
        if not comp.user_has_admin_permission(self.request.user):
            raise PermissionDenied('You do not have permission to email these competition participants')
        try:
            content = request.data['message']
        except KeyError:
            return Response({'detail': 'A message is required to send an email'}, status=status.HTTP_400_BAD_REQUEST)
        batch_send_email.apply_async((comp.pk, content))
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def get_csv(self, request, pk):
        # TODO: Need to differentiate between leaderboards on different phases
        #  (after there are different leaderboards on each phase)

        competition = self.get_object()
        if request.user != competition.created_by and request.user not in competition.collaborators.all() and not request.user.is_superuser:
            raise PermissionDenied("You don't have access to the competition leaderboard as a CSV")

        # Query Needed data and filter to what is needed.
        phase_pks = [phase.id for phase in Phase.objects.filter(competition_id=competition.id)]
        submission_query = Submission.objects.filter(Q(phase_id__in=phase_pks) & Q(has_children=False) & Q(leaderboard_id__isnull=False))
        if not submission_query.exists():
            raise ValidationError("There are no submissions on the leaderboard")

        # Build the data needed for the csv's into a dictionary
        csv = {}
        user_id = set()
        for sub in submission_query:
            if sub.leaderboard_id not in csv.keys():
                csv[sub.leaderboard_id] = {}
                csv[sub.leaderboard_id]["user"] = ["Username"]
                columns = Column.objects.filter(leaderboard_id=sub.leaderboard_id)
                for col in columns:
                    csv[sub.leaderboard_id][col.id] = [col.title]
            for score in sub.scores.all():
                csv[sub.leaderboard_id][score.column_id].append(float(score.score))
            csv[sub.leaderboard_id]["user"].append(sub.owner_id)
            user_id.add(sub.owner_id)

        # Replace user_id with usernames
        users = {x.id: x.username for x in User.objects.filter(id__in=user_id)}
        for leaderboard in csv:
            csv[leaderboard]['user'] = csv[leaderboard]["user"][:1] + [users[x] for x in csv[leaderboard]["user"][1:]]

        # Take the data from the dict, put them into csv files and add them to the archive
        with SpooledTemporaryFile() as tmp:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                for lb_id in csv.keys():
                    tempFile = NamedTemporaryFile()
                    csvCols = [x for x in csv[lb_id].keys()]
                    for entry in range(len(csv[lb_id][csvCols[0]])):
                        line = ""
                        for col in csvCols:
                            line += "{},".format(csv[lb_id][col][entry])
                        line = line[:-1] + "\n"
                        tempFile.write(str.encode(line))
                    tempFile.seek(0)
                    archive.write(tempFile.name, "{}.csv".format(Leaderboard.objects.get(id=lb_id).title))
            tmp.seek(0)
            response = HttpResponse(tmp.read(), content_type="application/x-zip-compressed")
            response['Content-Disposition'] = 'attachment; filename={}.zip'.format(competition.title)
            return response

    def _ensure_organizer_participants_accepted(self, instance):
        CompetitionParticipant.objects.filter(
            user__in=instance.collaborators.all()
        ).update(status=CompetitionParticipant.APPROVED)

    def perform_create(self, serializer):
        instance = serializer.save()
        self._ensure_organizer_participants_accepted(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._ensure_organizer_participants_accepted(instance)


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


class PhaseViewSet(ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer

    # TODO! Security, who can access/delete/etc this?

    @action(detail=True, methods=('POST',), url_name='manually_migrate')
    def manually_migrate(self, request, pk):
        """Manually migrates _from_ this phase. The destination phase does not need auto migration set to True"""
        phase = self.get_object()
        if not phase.competition.user_has_admin_permission(request.user):
            return Response(
                {"detail": "You do not have administrative permissions for this competition"},
                status=status.HTTP_403_FORBIDDEN
            )
        manual_migration.apply_async((pk,))
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, url_name='rerun_submissions')
    def rerun_submissions(self, request, pk):
        phase = self.get_object()
        comp = phase.competition
        if request.user not in comp.all_organizers and not request.user.is_superuser:
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
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(competition__in=user.competitions.all() | user.collaborations.all())
        qs = qs.select_related('user').order_by('user__username')
        return qs

    def update(self, request, *args, **kwargs):
        if request.method == 'PATCH':
            if 'status' in request.data:
                participation_status = request.data['status']
                participant = self.get_object()
                emails = {
                    'approved': send_participation_accepted_emails,
                    'denied': send_participation_denied_emails,
                }
                if participation_status in emails:
                    emails[participation_status](participant)

        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=('POST',))
    def send_email(self, request, pk):
        participant = self.get_object()
        competition = participant.competition
        if not competition.user_has_admin_permission(self.request.user):
            raise PermissionDenied('You do not have permission to email participants')
        try:
            message = request.data['message']
        except KeyError:
            return Response({'detail': 'A message is required to send an email'}, status=status.HTTP_400_BAD_REQUEST)
        send_direct_participant_email(participant=participant, content=message)
        return Response({}, status=status.HTTP_200_OK)
