import zipfile
import json
import csv
from collections import Counter, OrderedDict
from io import StringIO
from django.http import HttpResponse
from tempfile import SpooledTemporaryFile
from django.db import IntegrityError
from django.db.models import Subquery, OuterRef, Q, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer
from api.pagination import DynamicChoicePagination, LargePagination
from api.renderers import ZipRenderer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from api.serializers.competitions import TagSerializer, CompetitionSerializerSimple, PhaseSerializer, \
    CompetitionCreationTaskStatusSerializer, CompetitionDetailSerializer, CompetitionParticipantSerializer, \
    PhaseResultsSerializer, CompetitionUpdateSerializer, CompetitionCreateSerializer
from api.serializers.leaderboards import LeaderboardPhaseSerializer, LeaderboardSerializer
from competitions.emails import send_participation_requested_emails, send_participation_accepted_emails, \
    send_participation_denied_emails, send_direct_participant_email

from competitions.models import Tag, Competition, Phase, CompetitionCreationTaskStatus, CompetitionParticipant, Submission, PhaseTaskInstance
from competitions.public_competitions import DEFAULT_FILTER_MODE, DEFAULT_ORDERING, FILTER_MODE_AND, FILTER_MODE_OR, \
    ORDERINGS, get_public_competitions, read_tag_ids, read_date
from datasets.models import Data
from competitions.tasks import batch_send_email, manual_migration, create_competition_dump
from leaderboards.models import Leaderboard, Column
from leaderboards.ranking import inject_average_ranks
from utils.data import make_url_sassy
from api.permissions import IsOrganizerOrCollaborator
from django.db import transaction
from django.conf import settings
from django.utils.timezone import now


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LargePagination

    def get_queryset(self):

        qs = super().get_queryset().prefetch_related('tags__category')

        # Dashboard visibility filter
        visibility = self.request.query_params.get('visibility', None)
        if visibility:
            # If the visibility is not 'public' and the user is not a staff or superuser, raise a permission denied error
            if visibility != 'public' and not (self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)):
                raise PermissionDenied("You cannot view private competitions if you are not a superuser.")

            if visibility == 'public':
                qs = qs.filter(published=True)
            elif visibility == 'private':
                qs = qs.filter(published=False)
            # else visibility == 'all' and no filter is applied

        # filter by competition_type first, 'competition' by default
        competition_type = self.request.query_params.get('type', Competition.COMPETITION)
        if competition_type != 'any' and self.detail is False:
            qs = qs.filter(competition_type=competition_type)

        # Filter for search bar
        search_query = self.request.query_params.get('search')

        # Competition Secret key check
        secret_key = self.request.query_params.get('secret_key')

        # If user is logged in
        if self.request.user.is_authenticated:

            # `mine` is true when this is called from "Organizing" tab of benchmark management
            # Filter to only see competitions you own
            mine = self.request.query_params.get('mine', None)
            if mine:
                # either competition is mine
                # or
                # I am one of the collaborator
                qs = Competition.objects.filter(
                    (Q(created_by=self.request.user)) |
                    (Q(collaborators__in=[self.request.user]))
                ).distinct()

            # `participating_in` is true when this is called from "Participating" tab of benchmark management
            participating_in = self.request.query_params.get('participating_in', None)
            if participating_in:
                # Exclude competitions the user organizes: creators/collaborators are auto-added
                # as approved participants (see Competition.save()), but they belong in "Organizing" tab, not here.
                qs = qs.filter(
                    participants__user=self.request.user, participants__status="approved"
                ).exclude(
                    Q(created_by=self.request.user) | Q(collaborators=self.request.user)
                )

            participant_status_query = CompetitionParticipant.objects.filter(
                competition=OuterRef('pk'),
                user=self.request.user
            ).values_list('status')[:1]
            qs = qs.annotate(participant_status=Subquery(participant_status_query))

            # if `secret_key` is true, this is called for a secret competition
            if secret_key:
                qs = qs.filter(Q(secret_key=secret_key))

            # Default condition
            # not called from my competitions tab
            # not called from i'm participating in tab
            # not called from search bar
            # not called with a valid secret key
            if (not mine) and (not participating_in) and (not secret_key) and (not search_query) and (not visibility):
                # If authenticated user is not super user
                if not self.request.user.is_superuser:
                    # Return the following ---
                    # All competitions which belongs to you (private or public)
                    # And competitions where you are admin
                    # And public competitions
                    # And competitions where you are approved participant
                    # this filters out all private competitions from other users
                    base_qs = qs.filter(
                        (Q(created_by=self.request.user)) |
                        (Q(collaborators__in=[self.request.user])) |
                        (Q(published=True) & ~Q(created_by=self.request.user)) |
                        (Q(participants__user=self.request.user) & Q(participants__status="approved"))
                    )

                    # Additional condition of action
                    # allow private competition when action is register and has valid secret key
                    if self.request.method == 'POST' and self.action == 'register':
                        # get secret_key from request data
                        register_secret_key = self.request.data.get('secret_key', None)
                        # use secret key if available
                        if register_secret_key:
                            qs = base_qs | qs.filter(Q(secret_key=register_secret_key))
                        else:
                            qs = base_qs
                    else:
                        qs = base_qs

                # select distinct competitions
                qs = qs.distinct()

        else:
            # if user is not authenticated only show
            # public competitions
            # or
            # competition with valid secret key
            qs = qs.filter(
                (Q(published=True)) |
                (Q(secret_key=secret_key))
            )

        # if `search_query` is true, this is called form search bar
        if search_query:
            if self.request.user.is_authenticated:
                # competitions which this user owns
                # or
                # competitions in which this user is collaborator
                # or
                # competitions is published and belongs to someone else
                # or
                # competitions in which this user is participant and status is approved
                qs = qs.filter(
                    (
                        Q(title__icontains=search_query)
                        | Q(description__icontains=search_query)
                    )
                    & (
                        Q(created_by=self.request.user)
                        | Q(collaborators=self.request.user)
                        | Q(published=True)
                        | Q(
                            participants__user=self.request.user,
                            participants__status="approved",
                        )
                    )
                ).distinct()
            else:
                qs = qs.filter(
                    Q(title__icontains=search_query)
                    | Q(description__icontains=search_query)
                )

        # On GETs lets optimize the query to reduce DB calls
        if self.request.method == 'GET':
            qs = qs.select_related('created_by')
            if self.action == 'retrieve':
                task_instances = PhaseTaskInstance.objects.select_related(
                    'task',
                    'task__input_data', 'task__input_data__created_by', 'task__input_data__competition',
                    'task__reference_data', 'task__reference_data__created_by', 'task__reference_data__competition',
                    'task__ingestion_program', 'task__ingestion_program__created_by', 'task__ingestion_program__competition',
                    'task__scoring_program', 'task__scoring_program__created_by', 'task__scoring_program__competition',
                ).prefetch_related('task__solutions__data', 'task__solutions__tasks')

                qs = qs.select_related('queue').prefetch_related(
                    Prefetch('phases', queryset=Phase.objects.select_related('public_data', 'starting_kit', 'leaderboard').prefetch_related('leaderboard__columns')
                             ),
                    Prefetch('phases__task_instances', queryset=task_instances),
                    'pages',
                    'collaborators',
                    'whitelist_emails',
                )
            elif self.action != 'list':
                qs = qs.prefetch_related('phases')

        qs = qs.order_by('-created_when')
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
        if self.action == 'public':
            return CompetitionSerializerSimple
        elif self.action in ['get_phases', 'results', 'get_leaderboard_frontend_object']:
            return LeaderboardPhaseSerializer
        elif self.request.method == 'GET':
            return CompetitionDetailSerializer
        elif self.request.method == 'PATCH':
            return CompetitionUpdateSerializer
        else:
            # Really just CompetitionSerializer with queue = None
            return CompetitionCreateSerializer

    def create(self, request, *args, **kwargs):
        """Mostly a copy of the underlying base create, however we return some additional data
        in the response to remove a GET from the frontend"""

        for phase in request.data['phases']:
            for index in range(len(phase['tasks'])):
                phase['tasks'][index] = phase['tasks'][index]['task']

        # TODO - This is Temporary. Need to change Leaderboard to Phase connect to M2M and handle this correctly.
        # save leaderboard individually, then pass pk to each phase
        data = request.data
        if 'leaderboards' in data:
            leaderboard_data = data['leaderboards'][0]
            if leaderboard_data['id']:
                leaderboard_instance = Leaderboard.objects.get(id=leaderboard_data['id'])
                leaderboard = LeaderboardSerializer(leaderboard_instance, data=data['leaderboards'][0])
            else:
                leaderboard = LeaderboardSerializer(data=data['leaderboards'][0])
            leaderboard.is_valid()
            leaderboard.save()
            leaderboard_id = leaderboard["id"].value

            # Set leaderboard id, starting kit and public data for phases
            for phase in data['phases']:
                phase['leaderboard'] = leaderboard_id

                try:
                    phase['public_data'] = Data.objects.filter(key=phase['public_data']['value'])[0].id
                except TypeError:
                    phase['public_data'] = None
                try:
                    phase['starting_kit'] = Data.objects.filter(key=phase['starting_kit']['value'])[0].id
                except TypeError:
                    phase['starting_kit'] = None

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Re-do serializer in detail version (i.e. for Collaborator data)
        context = self.get_serializer_context()
        serializer = CompetitionDetailSerializer(serializer.instance, context=context)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # Execute everything inside atomic transaction
        with transaction.atomic():
            """Mostly a copy of the underlying base update, however we return some additional data
            in the response to remove a GET from the frontend"""
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            data = request.data
            # TODO - This is Temporary. Need to change Leaderboard to Phase connect to M2M and handle this correctly.
            # save leaderboard individually, then pass pk to each phase
            if 'leaderboards' in data:
                leaderboard_data = data['leaderboards'][0]
                if leaderboard_data['id']:
                    leaderboard_instance = Leaderboard.objects.get(id=leaderboard_data['id'])
                    leaderboard = LeaderboardSerializer(leaderboard_instance, data=data['leaderboards'][0])
                else:
                    leaderboard = LeaderboardSerializer(data=data['leaderboards'][0])
                leaderboard.is_valid()
                leaderboard.save()
                leaderboard_id = leaderboard["id"].value

                for phase in data['phases']:
                    # Newly added phase from front-end has no id
                    # Add a phase first to get id
                    # add this phase id in each task
                    if 'id' not in phase:
                        # Create Phase object
                        new_phase_obj = Phase.objects.create(
                            status=phase["status"],
                            index=phase["index"],
                            start=phase['start'],
                            end=phase['end'] if phase['end'] else None,
                            name=phase["name"],
                            description=phase["description"],
                            hide_output=phase["hide_output"],
                            hide_prediction_output=phase["hide_prediction_output"],
                            hide_score_output=phase["hide_score_output"],
                            competition=Competition.objects.get(id=data['id'])
                        )
                        # Get phase id
                        new_phase_id = new_phase_obj.id
                        # loop over phase tasks to add phase id in each task
                        for task in phase["tasks"]:
                            task['phase'] = new_phase_id

                    phase['leaderboard'] = leaderboard_id

                # Get public_data and starting_kit
                for phase in data['phases']:
                    # We just need to know what public_data and starting_kit go with this phase
                    # We don't need to serialize the whole object
                    try:
                        phase['public_data'] = Data.objects.filter(key=phase['public_data']['value'])[0].id
                    except TypeError:
                        phase['public_data'] = None
                    try:
                        phase['starting_kit'] = Data.objects.filter(key=phase['starting_kit']['value'])[0].id
                    except TypeError:
                        phase['starting_kit'] = None

            # Get whitelist emails from data
            whitelist_emails = data['whitelist_emails']
            # Delete white_list emails from data because it is not in a list of dict format, it is just list of emails
            data.pop('whitelist_emails', None)
            # Loop over whitelist emails and add them back to whitelist emails in dict format
            for email in whitelist_emails:
                # user lower case email because some emails in the whitelist may have upper case letters
                data.setdefault('whitelist_emails', []).append({'email': email.lower()})

            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

        # Re-do serializer in detail version (i.e. for Collaborator data)
        context = self.get_serializer_context()
        serializer = CompetitionUpdateSerializer(serializer.instance, context=context)
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
            send_participation_accepted_emails(participant, request)
        else:
            # check if user is in whitelist emails then approve directly
            # Using lower case because some users have used uppercased emails addresses
            if user.email.lower() in list(competition.whitelist_emails.values_list('email', flat=True)):
                participant.status = 'approved'
                send_participation_accepted_emails(participant, request)
            else:
                participant.status = 'pending'
                send_participation_requested_emails(participant, request)

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
        # TODO: Replace this auth check with user_has_admin_permission
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

    def collect_leaderboard_data(self, competition, phase_pk=None, all_submissions=False):
        # Only competition admins get here, so hidden columns are included
        context = {**self.get_serializer_context(), 'show_hidden': True, 'all_submissions': all_submissions}
        if phase_pk:
            phase = get_object_or_404(competition.phases.all(), id=phase_pk)
            submission_query = [self.get_serializer(phase, context=context).data]
            phase_id = phase.id
        else:
            phases = competition.phases.all()
            submission_query = self.get_serializer(phases, many=True, context=context).data
            if not len(phases):
                raise ValidationError(f"No Phases found on competition id:{competition.id}")
            phase_id = phases[0].id

        leaderboard = Leaderboard.objects.prefetch_related('columns').get(phases=phase_id)
        leaderboard_titles = {
            phase['id']: f'{leaderboard.title} - {phase["name"]}({phase["id"]})'
            for phase in submission_query
        }
        leaderboard_data = {title: {} for title in leaderboard_titles.values()}

        for phase in submission_query:
            generated_columns = OrderedDict()
            for task in phase['tasks']:
                for col in leaderboard.columns.all():
                    generated_columns.update({
                        f'{col.key}-{task["id"]}': f'{task["name"]}({task["id"]})-{col.title}'
                    })

            for submission in phase['submissions']:
                queue_name = submission.get('queue_name') or ''
                submission_key = f'{submission["owner"]}-{submission["id"]}'
                if queue_name:
                    submission_key = f'{submission_key}-{queue_name}'

                if submission_key not in leaderboard_data[leaderboard_titles[phase['id']]]:
                    leaderboard_data[leaderboard_titles[phase['id']]][submission_key] = OrderedDict()

                    if all_submissions:
                        leaderboard_data[leaderboard_titles[phase['id']]][submission_key].update({
                            'created_when': submission['created_when'],
                            'on_leaderboard': submission['leaderboard_id'] is not None,
                        })

                    if submission.get('fact_sheet_answers'):
                        leaderboard_data[leaderboard_titles[phase['id']]][submission_key].update({
                            'fact_sheet_answers': submission['fact_sheet_answers']
                        })

                    for col_title in generated_columns.values():
                        leaderboard_data[leaderboard_titles[phase['id']]][submission_key].update({col_title: ""})

                for score in submission['scores']:
                    score_column = generated_columns[f'{score["column_key"]}-{submission["task"]}']
                    leaderboard_data[leaderboard_titles[phase['id']]][submission_key].update({
                        score_column: score['score']
                    })

        return leaderboard_data

    @action(detail=True, methods=['GET'], renderer_classes=[JSONRenderer, CSVRenderer, ZipRenderer])
    def results(self, request, pk, format='json'):
        competition = self.get_object()
        if not competition.user_has_admin_permission(request.user):
            raise PermissionDenied("You are not a competition admin or superuser")
        selected_phase = request.GET.get('phase')
        # Every finished submission instead of the leaderboard entries only
        all_submissions = request.GET.get('all_submissions', 'false').lower() == 'true'
        data = self.collect_leaderboard_data(competition, selected_phase, all_submissions)
        if format == 'zip':
            with SpooledTemporaryFile() as tmp:
                with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                    for leaderboard in data:

                        # Check if the leaderboard is empty
                        if not data[leaderboard]:
                            continue

                        stringIO = StringIO()
                        columns = list(data[leaderboard][list(data[leaderboard].keys())[0]])
                        dict_writer = csv.DictWriter(stringIO, fieldnames=(["Username", "fact_sheet_answers"] + columns))
                        dict_writer.writeheader()
                        for submission in data[leaderboard]:
                            line = {"Username": submission}
                            line.update(data[leaderboard][submission])
                            dict_writer.writerow(line)
                        archive.writestr(f'{leaderboard}.csv', stringIO.getvalue())
                tmp.seek(0)
                response = HttpResponse(tmp.read(), content_type="application/x-zip-compressed")
                response['Content-Disposition'] = 'attachment; filename={}.zip'.format(competition.title)
                return response

        if format == 'json':
            return HttpResponse(json.dumps(data, indent=4), content_type="application/json")

        elif format == 'csv':
            if len(data) > 1:
                raise ValidationError("More than one matching leaderboard. Try selecting phase or get a .zip?")
            elif len(data) == 0:
                raise ValidationError("No Matching Leaderboard")
            leaderboard_title = list(data.keys())[0]

            # Check if the leaderboard data is empty
            if not data[leaderboard_title]:
                # Return an empty CSV
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{leaderboard_title}.csv"'
                return response

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{leaderboard_title}.csv"'
            columns = list(data[leaderboard_title][list(data[leaderboard_title].keys())[0]].keys())
            dict_writer = csv.DictWriter(response, fieldnames=(["Username", "fact_sheet_answers"] + columns))

            dict_writer.writeheader()
            for submission in data[leaderboard_title]:
                row = {"Username": submission}
                row.update(data[leaderboard_title][submission])
                dict_writer.writerow(row)
            return response

    # @swagger_auto_schema(responses={200: CompetitionCreationTaskStatusSerializer()})
    @extend_schema(responses={200: CompetitionCreationTaskStatusSerializer})
    @action(detail=True, methods=('GET',))
    def creation_status(self, request, pk):
        """This endpoint gets the creation status for a competition during upload"""
        competition_creation_status = get_object_or_404(
            CompetitionCreationTaskStatus,
            created_by=request.user,
            pk=pk,
        )
        serializer = CompetitionCreationTaskStatusSerializer(competition_creation_status)

        return Response(serializer.data)

    # @swagger_auto_schema(request_body=no_body, responses={201: CompetitionCreationTaskStatusSerializer()})
    @extend_schema(request=None, responses={201: CompetitionCreationTaskStatusSerializer})
    @action(detail=True, methods=('POST',), serializer_class=CompetitionCreationTaskStatusSerializer)
    def create_dump(self, request, pk=None):
        competition = self.get_object()
        if not competition.user_has_admin_permission(request.user):
            raise PermissionDenied("You don't have access")

        # get keys_instead_of_files from request data
        keys_instead_of_files = request.data.get('keys_instead_of_files', False)

        # arg 1: pk: competition primary key
        # arg 2: keys_instead_of_files (if false: files will be dowloaded in dumps, if true: only keys)
        create_competition_dump.delay(pk, keys_instead_of_files)

        serializer = CompetitionCreationTaskStatusSerializer({"status": "Success. Competition dump is being created."})
        return Response(serializer.data, status=201)

    # Each filter is listed as a parameter, so the API docs show its type, values and an example
    @extend_schema(parameters=[
        OpenApiParameter(
            name='search', type=OpenApiTypes.STR,
            description="Text to find in the title, or in the username or display name of the organizer.",
            examples=[OpenApiExample('Search', value='vision')],
        ),
        OpenApiParameter(
            name='tags', type=OpenApiTypes.INT, many=True,
            description="Ids of tags. Send them repeated (tags=1&tags=3) or with commas (tags=1,3). "
                        "How several tags combine depends on filter_mode.",
        ),
        OpenApiParameter(
            name='filter_mode', type=OpenApiTypes.STR, enum=[FILTER_MODE_OR, FILTER_MODE_AND], default=DEFAULT_FILTER_MODE,
            description=f"How tags, has_a_prize, participating_in and organizing combine. "
                        f"{FILTER_MODE_OR}: a competition must match at least one of them. "
                        f"{FILTER_MODE_AND}: a competition must match all of them.",
        ),
        OpenApiParameter(
            name='has_a_prize', type=OpenApiTypes.BOOL,
            description="true: only competitions with a prize.",
        ),
        OpenApiParameter(
            name='participating_in', type=OpenApiTypes.BOOL,
            description="true: only competitions you take part in, without the ones you organize. Needs a login, otherwise 401.",
        ),
        OpenApiParameter(
            name='organizing', type=OpenApiTypes.BOOL,
            description="true: only competitions you created or co-organize. Needs a login, otherwise 401.",
        ),
        OpenApiParameter(
            name='start_date', type=OpenApiTypes.DATE,
            description="Only competitions created on or after this day, as YYYY-MM-DD.",
            examples=[OpenApiExample('Start date', value='2026-01-01')],
        ),
        OpenApiParameter(
            name='end_date', type=OpenApiTypes.DATE,
            description="Only competitions created on or before this day, the whole day included, as YYYY-MM-DD.",
            examples=[OpenApiExample('End date', value='2026-03-31')],
        ),
        OpenApiParameter(
            name='ordering', type=OpenApiTypes.STR, enum=list(ORDERINGS), default=DEFAULT_ORDERING,
            description="Sort. recent: newest first. popular: most participants first. "
                        "with_most_submissions: most submissions first. Ties are sorted newest first.",
        ),
    ])
    @action(detail=False, methods=('GET',), pagination_class=LargePagination)
    def public(self, request):
        """
        List the published competitions, with optional search, filters and sort.
        The same filters and sort as the public competitions page.

        How the filters combine:
        - search, start_date and end_date always make the list shorter.
        - tags, has_a_prize, participating_in and organizing are combined by filter_mode:
          or (default): a competition must match at least one of them.
          and: a competition must match all of them.

        participating_in and organizing need a logged-in user, otherwise the response is 401.
        Invalid values (for example tags=abc or start_date=2026-13-45) are ignored.
        """

        # Receive filters from request query params
        search = request.query_params.get("search")
        tag_values = request.query_params.getlist("tags")
        filter_mode = request.query_params.get("filter_mode", DEFAULT_FILTER_MODE).lower()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        ordering = request.query_params.get("ordering")
        participating_in = request.query_params.get("participating_in", "false").lower() == "true"
        organizing = request.query_params.get("organizing", "false").lower() == "true"
        has_a_prize = request.query_params.get("has_a_prize", "false").lower() == "true"

        # If user is not authenticated but trying to use filters that require authentication
        if not request.user.is_authenticated and (participating_in or organizing):
            return Response(
                {"detail": "Authentication required for filtering by participating in or organizing."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Same filters and sorting as the public competitions page
        qs = get_public_competitions(
            user=request.user,
            search=(search or '').strip(),
            ordering=ordering,
            participating_in=participating_in,
            organizing=organizing,
            has_a_prize=has_a_prize,
            tag_ids=read_tag_ids(tag_values),
            filter_mode=filter_mode,
            start_date=read_date(start_date),
            end_date=read_date(end_date, end_of_day=True),
        )

        queryset = self.filter_queryset(qs)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def run_new_task_submissions(self, phase, tasks):
        tasks_ids = set([task.id for task in tasks])
        submissions = phase.submissions.filter(has_children=True).prefetch_related("children").all()

        for submission in submissions:
            child_tasks_ids = set(submission.children.values_list('task__id', flat=True))
            missing_tasks = tasks_ids - child_tasks_ids
            for task in filter(lambda t: t.id in missing_tasks, tasks):
                sub = Submission(
                    owner=submission.owner,
                    phase=submission.phase,
                    parent=submission,
                    task=task,
                    appear_on_leaderboards=submission.appear_on_leaderboards,
                    leaderboard=submission.children.first().leaderboard,
                    data=submission.data,
                )
                sub.save(ignore_submission_limit=True)
                sub.start(tasks=[task])

    def _ensure_organizer_participants_accepted(self, instance):
        CompetitionParticipant.objects.filter(
            user__in=instance.collaborators.all()
        ).update(status=CompetitionParticipant.APPROVED)

    def perform_create(self, serializer):
        instance = serializer.save()
        self._ensure_organizer_participants_accepted(instance)

    def perform_update(self, serializer):
        instance = self.get_object()
        initial_tasks = {phase.id: set(phase.tasks.all()) for phase in instance.phases.all().prefetch_related('tasks')}
        instance = serializer.save()
        self._ensure_organizer_participants_accepted(instance)

        saved_tasks = {phase.id: set(phase.tasks.all()) for phase in instance.phases.filter(pk__in=initial_tasks.keys()).prefetch_related('tasks')}
        for phase_id in saved_tasks:
            new_tasks = list(saved_tasks[phase_id] - initial_tasks[phase_id])
            if new_tasks:
                self.run_new_task_submissions(instance.phases.get(pk=phase_id), new_tasks)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all().select_related('category')
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class PhaseViewSet(ModelViewSet):
    serializer_class = PhaseSerializer

    def get_queryset(self):
        qs = Phase.objects.select_related('competition', 'leaderboard')
        if self.action == 'get_leaderboard':
            qs = qs.prefetch_related(
                Prefetch('task_instances', queryset=PhaseTaskInstance.objects.select_related('task'))
            )
        return qs

    def list(self, request, *args, **kwargs):
        # Check if it's a direct request to /api/phases/
        # i.e without a pk
        direct_request = 'pk' not in kwargs or kwargs['pk'] == 'list'

        if direct_request:
            # return empty response in direct request
            return Response([], status=status.HTTP_200_OK)

        # Otherwise, allow other functions to use the list functionality as usual
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # TODO! Security, who can access/delete/etc this?

    @action(detail=True, methods=('POST',), url_name='manually_migrate')
    def manually_migrate(self, request, pk):
        """Manually migrates _from_ this phase to `destination_phase` (id), or to the next index if omitted."""
        phase = self.get_object()
        if not phase.competition.user_has_admin_permission(request.user):
            return Response(
                {"detail": "You do not have administrative permissions for this competition"},
                status=status.HTTP_403_FORBIDDEN
            )

        destination_id = request.data.get('destination_phase')
        if destination_id:
            try:
                destination = phase.competition.phases.get(pk=destination_id)
            except (Phase.DoesNotExist, ValueError, TypeError):
                return Response({"detail": "Destination phase not found in this competition."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            destination = phase.competition.phases.filter(index=phase.index + 1).first()
            if destination is None:
                return Response({"detail": "There is no next phase to migrate to."},
                                status=status.HTTP_400_BAD_REQUEST)

        if destination.pk == phase.pk:
            return Response({"detail": "Source and destination phases must be different."},
                            status=status.HTTP_400_BAD_REQUEST)
        if destination.end and destination.end < now():
            return Response({"detail": "The destination phase has ended."},
                            status=status.HTTP_400_BAD_REQUEST)

        manual_migration.apply_async((pk, destination.pk))
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, url_name='rerun_submissions')
    def rerun_submissions(self, request, pk):

        phase = self.get_object()
        comp = phase.competition

        # Get submissions with no parent
        submissions = phase.submissions.filter(parent__isnull=True, is_soft_deleted=False, data__isnull=False)

        can_re_run_submissions = False
        error_message = ""

        # Super admin can rerun without any restrictions
        if request.user.is_superuser:
            can_re_run_submissions = True

        # competition admin can run only if
        elif request.user in comp.all_organizers:

            # submissions are in limit
            if len(submissions) <= int(settings.RERUN_SUBMISSION_LIMIT):
                can_re_run_submissions = True

            # submissions are not in limit
            else:
                # Codabemch public queue
                if comp.queue is None:
                    can_re_run_submissions = False
                    error_message = f"You cannot rerun more than {settings.RERUN_SUBMISSION_LIMIT} submissions on Codabench public queue! Contact us on `{settings.CONTACT_EMAIL}` to request a rerun."

                # Other queue where user is not owner and not organizer
                elif request.user != comp.queue.owner and request.user not in comp.queue.organizers.all():
                    can_re_run_submissions = False
                    error_message = f"You cannot rerun more than {settings.RERUN_SUBMISSION_LIMIT} submissions on a queue which is not yours! Contact us on `{settings.CONTACT_EMAIL}` to request a rerun."

                # User can rerun submissions where he is owner or organizer
                else:
                    can_re_run_submissions = True

        else:
            can_re_run_submissions = False
            error_message = 'You do not have permission to re-run submissions'

        # error when user is not super user or admin of the competition
        if can_re_run_submissions:
            rerunnable = [s for s in submissions if s.status in Submission.RERUNNABLE_STATUSES]
            for submission in rerunnable:
                submission.re_run()
            return Response({"count": len(rerunnable)})
        else:
            raise PermissionDenied(error_message)

    # @swagger_auto_schema(responses={200: PhaseResultsSerializer})
    @extend_schema(responses={200: PhaseResultsSerializer})
    @action(detail=True, methods=['GET'], permission_classes=[AllowAny])
    def get_leaderboard(self, request, pk):
        phase = self.get_object()

        def _clean_group_label(raw_name, submission_parent_id=None):
            if not raw_name:
                return None

            label = str(raw_name)

            if submission_parent_id is not None:
                prefix = f"{submission_parent_id}_"
                if label.startswith(prefix):
                    label = label[len(prefix):]

            if "__" in label:
                label = label.rsplit("__", 1)[1]

            return label or None

        if phase.competition.fact_sheet:
            fact_sheet_keys = [
                (
                    phase.competition.fact_sheet[question]['key'],
                    phase.competition.fact_sheet[question]['title']
                )
                for question in phase.competition.fact_sheet
                if phase.competition.fact_sheet[question]['is_on_leaderboard'] == 'true'
            ]
        else:
            fact_sheet_keys = None

        # Hidden columns are private to the competition admins
        show_hidden = phase.competition.user_has_admin_permission(request.user)
        query = LeaderboardPhaseSerializer(phase, context={'show_hidden': show_hidden}).data
        response = {
            'title': query['leaderboard']['title'],
            'id': phase.id,
            'submissions': [],
            'tasks': [],
            'fact_sheet_keys': fact_sheet_keys or None,
            'primary_index': query['leaderboard']['primary_index'],
            'has_group_queues': False,
        }

        columns = list(query['columns'])
        submissions_keys = {}
        submission_detailed_results = {}

        group_name_by_user_queue = {}
        for group in phase.competition.participant_groups.filter(
            queue__isnull=False
        ).select_related('queue').prefetch_related('user_set'):
            cleaned_group_name = _clean_group_label(group.name)
            for user in group.user_set.all():
                group_name_by_user_queue[(user.username, group.queue_id)] = cleaned_group_name

        parent_ids = {
            s['parent']
            for s in query['submissions']
            if s['parent'] is not None
        }
        parent_task_counts = Counter(
            (s['parent'], s['task'])
            for s in query['submissions']
            if s['parent'] is not None
        )

        for submission in query['submissions']:
            if submission['id'] in parent_ids:
                continue

            submission_parent_id = submission.get('parent') or submission.get('id')
            raw_queue_name = submission.get('queue_name') or ''
            queue_id = submission.get('queue_id')

            group_name = group_name_by_user_queue.get(
                (submission['owner'], queue_id)
            ) if queue_id else None

            group_label = _clean_group_label(
                group_name or raw_queue_name,
                submission_parent_id=submission_parent_id
            )

            display_group = (
                f"{submission_parent_id}_{group_label}"
                if group_label
                else None
            )

            parent_id = submission['parent']
            task_id = submission.get('task')

            # Cas particulier: plusieurs submissions d'un même parent sans queue explicite
            is_multi_group_null_queue = (
                parent_id is not None
                and not queue_id
                and parent_task_counts.get((parent_id, task_id), 0) > 1
            )

            if is_multi_group_null_queue:
                submission_key = f"{submission['owner']}{parent_id}_{submission['id']}"
            else:
                submission_key = f"{submission['owner']}{submission_parent_id}_{group_label or ''}"

            # gather detailed result from submissions for each task
            submission_detailed_results.setdefault(submission_key, []).append({
                'task': submission['task'],
                'id': submission['id']
            })

            if submission_key not in submissions_keys:
                submissions_keys[submission_key] = len(response['submissions'])
                response['submissions'].append({
                    'id': submission_parent_id,
                    'owner': submission['display_name'] or submission['owner'],
                    'scores': [],
                    'detailed_results': [],
                    'fact_sheet_answers': submission['fact_sheet_answers'],
                    'slug_url': submission['slug_url'],
                    'organization': submission['organization'],
                    'created_when': submission['created_when'],
                    'queue_name': display_group,
                })

                if queue_id or is_multi_group_null_queue:
                    response['has_group_queues'] = True

            for score in submission['scores']:
                column_found = False
                precision = 2

                for col in columns:
                    if col["index"] == score["index"]:
                        precision = col["precision"]
                        column_found = True
                        break

                tempScore = score
                tempScore['task_id'] = submission['task']
                tempScore['score'] = str(round(float(tempScore["score"]), precision))

                if column_found:
                    response['submissions'][submissions_keys[submission_key]]['scores'].append(tempScore)

        # put detailed results in its submission
        for k, v in submissions_keys.items():
            response['submissions'][v]['detailed_results'] = submission_detailed_results[k]

        # Compute average rank for any AVERAGE_RANK columns and inject into response.
        col_by_index = {col['index']: col for col in columns}
        avg_rank_cols = [col for col in columns if col.get('computation') == Column.AVERAGE_RANK]
        if avg_rank_cols:
            inject_average_ranks(response['submissions'], avg_rank_cols, col_by_index, response['primary_index'])

        # --- pagination addition ---
        total_count = len(response['submissions'])
        paginator = DynamicChoicePagination()
        paginated_submissions = paginator.paginate_queryset(response['submissions'], request, view=self)
        if paginated_submissions is None:
            paginated_submissions = response['submissions']

        response['submissions'] = paginated_submissions
        response['count'] = total_count
        response['page_size'] = getattr(paginator, 'requested_page_size', request.query_params.get('page_size', 50))
        response['next'] = paginator.get_next_link()
        response['previous'] = paginator.get_previous_link()
        response['allowed_page_sizes'] = [50, 100, 500, 'all']
        # --- end pagination addition ---

        for task in query['tasks']:
            tempTask = {
                'name': task['name'],
                'id': task['id'],
                'colWidth': len(columns),
                'columns': [],
            }
            for col in columns:
                tempTask['columns'].append(col)
            response['tasks'].append(tempTask)

        return Response(response)


class CompetitionParticipantViewSet(ModelViewSet):
    queryset = CompetitionParticipant.objects.all()
    serializer_class = CompetitionParticipantSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ('user__username', 'user__email', 'status', 'competition', 'user__is_deleted')
    search_fields = ('user__username', 'user__email',)

    def get_queryset(self):

        # a boolean set to true if the request is considered valid
        # i.e. it is either GET request with `competition``
        # or patch request with `status`
        # or post request with `message`
        is_valid_request = False

        if self.request.method == "PATCH":
            # PATCH request is considered valid if it has `status`
            if 'status' in self.request.data:
                is_valid_request = True

        if self.request.method == "POST":
            # POST request is considered valid if it has `message`
            if 'message' in self.request.data:
                is_valid_request = True

        if self.request.method == "GET":
            # GET request is considered valid if it has `competition``
            # if there is no competition then it si called from /api/participants/
            # URL which is not considered valid
            if 'competition' in self.request.GET:
                is_valid_request = True

        if is_valid_request:
            # API to act normally i.e return participants
            qs = super().get_queryset()
            user = self.request.user
            if not user.is_superuser:
                qs = qs.filter(competition__in=user.competitions.all() | user.collaborations.all())
            qs = qs.select_related('user').order_by('user__username')
            return qs
        else:
            # API will work but will return empty participants list
            return CompetitionParticipant.objects.none()

    def update(self, request, *args, **kwargs):
        if request.method == 'PATCH' and 'status' in request.data:
            participation_status = request.data['status']
            participant = self.get_object()

            # Check if the new status is the same as the current status
            if participation_status == participant.status:
                return Response(
                    {"error": f"Status is already set to `{participation_status}`"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            emails = {
                'approved': send_participation_accepted_emails,
                'denied': send_participation_denied_emails,
            }
            if participation_status in emails:
                emails[participation_status](participant, request)

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
