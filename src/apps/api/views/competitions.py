import zipfile
import json
import csv
from collections import OrderedDict
from io import StringIO
from django.http import HttpResponse
from tempfile import SpooledTemporaryFile
from django.db import IntegrityError
from django.db.models import Subquery, OuterRef, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer
from api.pagination import LargePagination
from api.renderers import ZipRenderer
from rest_framework.viewsets import ModelViewSet
from api.serializers.competitions import CompetitionSerializerSimple, PhaseSerializer, \
    CompetitionCreationTaskStatusSerializer, CompetitionDetailSerializer, CompetitionParticipantSerializer, \
    FrontPageCompetitionsSerializer, PhaseResultsSerializer, CompetitionUpdateSerializer, CompetitionCreateSerializer
from api.serializers.leaderboards import LeaderboardPhaseSerializer, LeaderboardSerializer
from competitions.emails import send_participation_requested_emails, send_participation_accepted_emails, \
    send_participation_denied_emails, send_direct_participant_email
from competitions.models import Competition, Phase, CompetitionCreationTaskStatus, CompetitionParticipant, Submission
from datasets.models import Data
from competitions.tasks import batch_send_email, manual_migration, create_competition_dump
from competitions.utils import get_popular_competitions, get_recent_competitions
from leaderboards.models import Leaderboard
from utils.data import make_url_sassy
from api.permissions import IsOrganizerOrCollaborator
from django.db import transaction
from django.conf import settings


class CompetitionViewSet(ModelViewSet):
    queryset = Competition.objects.all()
    permission_classes = (AllowAny,)

    def get_queryset(self):

        qs = super().get_queryset()

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

            # `mine` is true when this is called from "Benchmarks I'm Running"
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

            # `participating_in` is true when this is called from "Benchmarks I'm in"
            participating_in = self.request.query_params.get('participating_in', None)
            if participating_in:
                qs = qs.filter(participants__user=self.request.user, participants__status="approved")

            participant_status_query = CompetitionParticipant.objects.filter(
                competition=OuterRef('pk'),
                user=self.request.user
            ).values_list('status')[:1]
            qs = qs.annotate(participant_status=Subquery(participant_status_query))

            # if `search_query` is true, this is called form search bar
            if search_query:
                # competitions which this user owns
                # or
                # competitions in which this user is collaborator
                # or
                # competitions is published and belongs to someone else
                # or
                # competitions in which this user is participant and status is approved
                qs = qs.filter(
                    (Q(created_by=self.request.user)) |
                    (Q(collaborators__in=[self.request.user])) |
                    (Q(published=True) & ~Q(created_by=self.request.user)) |
                    (Q(participants__user=self.request.user) & Q(participants__status="approved"))
                ).distinct()

            # if `secret_key` is true, this is called for a secret competition
            if secret_key:
                qs = qs.filter(Q(secret_key=secret_key))

            # Default condition
            # not called from my competitions tab
            # not called from i'm participating in tab
            # not called from search bar
            # not called with a valid secret key
            if (not mine) and (not participating_in) and (not secret_key) and (not search_query):
                # If authenticated user is not super user
                if not self.request.user.is_superuser:
                    # Return the following ---
                    # All competitions which belongs to you (private or public)
                    # And competitions where you are admin
                    # And public competitions
                    # And competitions where you are approved participant
                    # this filters out all private compettions from other users
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
                    'phases__leaderboard',
                    'phases__leaderboard__columns',
                    'collaborators',
                )
                # qs = qs.annotate(participant_count=Count(F('participants'), distinct=True))
                # qs = qs.annotate(submission_count=Count(
                #     # Filtering out children submissions so we only count distinct submissions
                #     Case(
                #         When(phases__submissions__parent__isnull=True, then='phases__submissions__pk')
                #     ), distinct=True)
                # )

        # search_query is true when called from searchbar
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
            send_participation_accepted_emails(participant)
        else:
            # check if user is in whitelist emails then approve directly
            # Using lower case because some users have used uppercased emails addresses
            if user.email.lower() in list(competition.whitelist_emails.values_list('email', flat=True)):
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

    def collect_leaderboard_data(self, competition, phase_pk=None):
        if phase_pk:
            phase = get_object_or_404(competition.phases.all(), id=phase_pk)
            submission_query = [self.get_serializer(phase).data]
            phase_id = phase.id
        else:
            phases = competition.phases.all()
            submission_query = self.get_serializer(phases, many=True).data
            if not len(phases):
                raise ValidationError(f"No Phases found on competition id:{competition.id}")
            phase_id = phases[0].id

        leaderboard = Leaderboard.objects.prefetch_related('columns').get(phases=phase_id)
        leaderboard_titles = {phase['id']: f'{leaderboard.title} - {phase["name"]}({phase["id"]})' for phase in submission_query}
        leaderboard_data = {title: {} for title in leaderboard_titles.values()}

        for phase in submission_query:
            generated_columns = OrderedDict()
            for task in phase['tasks']:
                for col in leaderboard.columns.all():
                    generated_columns.update({f'{col.key}-{task["id"]}': f'{task["name"]}({task["id"]})-{col.title}'})
            for submission in phase['submissions']:
                submission_key = f'{submission["owner"]}-{submission["parent"] or submission["id"]}'
                if submission_key not in leaderboard_data[leaderboard_titles[phase['id']]].keys():
                    leaderboard_data[leaderboard_titles[phase['id']]].update({submission_key: OrderedDict()})
                    if 'fact_sheet_answers' in submission.keys() and submission['fact_sheet_answers']:
                        leaderboard_data[leaderboard_titles[phase['id']]][submission_key]\
                            .update({'fact_sheet_answers': submission['fact_sheet_answers']})
                    for col_title in generated_columns.values():
                        leaderboard_data[leaderboard_titles[phase['id']]][submission_key].update({col_title: ""})
                for score in submission['scores']:
                    score_column = generated_columns[f'{score["column_key"]}-{submission["task"]}']
                    leaderboard_data[leaderboard_titles[phase['id']]][submission_key].update({score_column: score['score']})
        return leaderboard_data

    @action(detail=True, methods=['GET'], renderer_classes=[JSONRenderer, CSVRenderer, ZipRenderer])
    def results(self, request, pk, format='json'):
        competition = self.get_object()
        if not competition.user_has_admin_permission(request.user):
            raise PermissionDenied("You are not a competition admin or superuser")
        selected_phase = request.GET.get('phase')
        data = self.collect_leaderboard_data(competition, selected_phase)
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

    # @swagger_auto_schema(responses={200: FrontPageCompetitionsSerializer()})
    @extend_schema(responses={200: FrontPageCompetitionsSerializer})
    @action(detail=False, methods=('GET',), permission_classes=(AllowAny,))
    def front_page(self, request):
        popular_comps = get_popular_competitions()
        recent_comps = get_recent_competitions(exclude_comps=popular_comps)
        popular_comps_serializer = CompetitionSerializerSimple(popular_comps, many=True)
        recent_comps_serializer = CompetitionSerializerSimple(recent_comps, many=True)
        return Response(data={
            "popular_comps": popular_comps_serializer.data,
            "recent_comps": recent_comps_serializer.data
        })

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

    @action(detail=False, methods=('GET',), pagination_class=LargePagination)
    def public(self, request):
        """
        Retrieve a public list of published competitions with optional filtering and ordering.

        This endpoint returns a paginated list of competitions that are publicly published.
        It supports several optional query parameters for filtering and sorting the results.
        Some filters require the user to be authenticated.

        Query Parameters:
        -----------------
        - search (str, optional): A search term to filter competitions by their title.
        - ordering (str, optional): Specifies the order of the results. Supported values:
            * "recent" - Most recently created competitions.
            * "popular" - Competitions with the most participants.
            * "with_most_submissions" - Competitions with the highest number of submissions.
            Defaults to "recent" if not provided or invalid.
        - participating_in (bool, optional): If "true", filters competitions where the user
        is an approved participant. Requires authentication.
        - organizing (bool, optional): If "true", filters competitions organized by the user
        (either created or as a collaborator). Requires authentication.
        - has_reward (bool, optional): If "true", includes only competitions that have a
        non-empty reward field.

        Returns:
        --------
        - 200 OK: A paginated or full list of serialized competitions matching the filter criteria. The response is serialized using `CompetitionSerializerSimple`.
        - 401 Unauthorized: If the user tries to use filters requiring authentication while not logged in.
        """

        # Receive filters from request query params
        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering")
        participating_in = request.query_params.get("participating_in", "false").lower() == "true"
        organizing = request.query_params.get("organizing", "false").lower() == "true"
        has_reward = request.query_params.get("has_reward", "false").lower() == "true"

        # If user is not authenticated but trying to use filters that require authentication
        if not request.user.is_authenticated and (participating_in or organizing):
            return Response(
                {"detail": "Authentication required for filtering by participating in or organizing."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        qs = Competition.objects.filter(published=True)

        # Filter by title (search)
        if search:
            qs = qs.filter(title__icontains=search)

        # Filter by participation
        if participating_in:
            participant_comp_ids = CompetitionParticipant.objects.filter(
                user=request.user,
                status="approved"
            ).values_list("competition_id", flat=True)
            qs = qs.filter(id__in=participant_comp_ids)

        # Filter by organizing (created_by or collaborator)
        if organizing:
            qs = qs.filter(Q(created_by=request.user) | Q(collaborators=request.user))

        # Apply ordering
        if ordering == "recent":
            qs = qs.order_by("-id")  # most recently created
        elif ordering == "popular":
            qs = qs.order_by("-participants_count")
        elif ordering == "with_most_submissions":
            qs = qs.order_by("-submissions_count")
        else:
            qs = qs.order_by("-id")  # default fallback

        # Applying has reward
        if has_reward:
            qs = qs.exclude(reward__isnull=True).exclude(reward__exact='')

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
        instance.make_programs_available
        instance.make_input_data_available
        initial_tasks = {phase.id: set(phase.tasks.all()) for phase in instance.phases.all().prefetch_related('tasks')}
        instance = serializer.save()
        self._ensure_organizer_participants_accepted(instance)

        saved_tasks = {phase.id: set(phase.tasks.all()) for phase in instance.phases.filter(pk__in=initial_tasks.keys()).prefetch_related('tasks')}
        for phase_id in saved_tasks:
            new_tasks = list(saved_tasks[phase_id] - initial_tasks[phase_id])
            if new_tasks:
                self.run_new_task_submissions(instance.phases.get(pk=phase_id), new_tasks)


class PhaseViewSet(ModelViewSet):
    serializer_class = PhaseSerializer

    def get_queryset(self):
        qs = Phase.objects.all()
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
        """Manually migrates _from_ this phase. The destination phase does not need auto migration set to True"""
        phase = self.get_object()
        if not phase.competition.user_has_admin_permission(request.user):
            return Response(
                {"detail": "You do not have administrative permissions for this competition"},
                status=status.HTTP_403_FORBIDDEN
            )
        # import pdb; pdb.set_trace()
        manual_migration.apply_async((pk,))
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, url_name='rerun_submissions')
    def rerun_submissions(self, request, pk):

        phase = self.get_object()
        comp = phase.competition

        # Get submissions with no parent
        submissions = phase.submissions.filter(parent__isnull=True)

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
            # rerun all submissions
            for submission in submissions:
                submission.re_run()
            rerun_count = len(submissions)
            return Response({"count": rerun_count})
        else:
            raise PermissionDenied(error_message)

    # @swagger_auto_schema(responses={200: PhaseResultsSerializer})
    @extend_schema(responses={200: PhaseResultsSerializer})
    @action(detail=True, methods=['GET'], permission_classes=[AllowAny])
    def get_leaderboard(self, request, pk):
        phase = self.get_object()
        if phase.competition.fact_sheet:
            fact_sheet_keys = [(phase.competition.fact_sheet[question]['key'], phase.competition.fact_sheet[question]['title'])
                               for question in phase.competition.fact_sheet if phase.competition.fact_sheet[question]['is_on_leaderboard'] == 'true']
        else:
            fact_sheet_keys = None
        query = LeaderboardPhaseSerializer(phase).data
        response = {
            'title': query['leaderboard']['title'],
            'id': phase.id,
            'submissions': [],
            'tasks': [],
            'fact_sheet_keys': fact_sheet_keys or None,
            'primary_index': query['leaderboard']['primary_index']
        }
        columns = [col for col in query['columns']]
        submissions_keys = {}
        submission_detailed_results = {}
        for submission in query['submissions']:
            submission_key = f"{submission['owner']}{submission['parent'] or submission['id']}"
            # gather detailed result from submissions for each task
            # detailed_results are gathered based on submission key
            # `id` is used to fetch the right detailed result in detailed results page
            # `detailed_result` url is not needed
            submission_detailed_results.setdefault(submission_key, []).append({
                # 'detailed_result': submission['detailed_result'],
                'task': submission['task'],
                'id': submission['id']
            })

            if submission_key not in submissions_keys:
                submissions_keys[submission_key] = len(response['submissions'])
                response['submissions'].append({
                    'id': submission['id'],
                    'owner': submission['display_name'] or submission['owner'],
                    'scores': [],
                    'detailed_results': [],
                    'fact_sheet_answers': submission['fact_sheet_answers'],
                    'slug_url': submission['slug_url'],
                    'organization': submission['organization'],
                    'created_when': submission['created_when']
                })
            for score in submission['scores']:

                # to check if a column is found
                # this is useful because of `hidden` field
                # if a column is hidden it will not be shown here so
                # we will not return that score to the front-end
                column_found = False
                # default precision is set to 2
                precision = 2
                # default hidden is set to false
                hidden = False

                # loop over columns to find a column with the same index
                # replace default precision with column precision
                for col in columns:
                    if col["index"] == score["index"]:
                        precision = col["precision"]
                        hidden = col["hidden"]
                        column_found = True
                        break

                tempScore = score
                tempScore['task_id'] = submission['task']
                # round the score to 'precision' decimal points
                tempScore['score'] = str(round(float(tempScore["score"]), precision))

                # only add scores to the scores list
                # if this column is found
                # and
                # column is not hidden
                if column_found and not hidden:
                    response['submissions'][submissions_keys[submission_key]]['scores'].append(tempScore)

        # put detailed results in its submission
        for k, v in submissions_keys.items():
            response['submissions'][v]['detailed_results'] = submission_detailed_results[k]

        for task in query['tasks']:
            # This can be used to rendered variable columns on each task
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
    filter_fields = ('user__username', 'user__email', 'status', 'competition', 'user__is_deleted')
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
