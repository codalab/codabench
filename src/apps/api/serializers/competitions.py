from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.fields import NamedBase64ImageField
from api.mixins import DefaultUserCreateMixin
from api.serializers.datasets import DataDetailSerializer
from api.serializers.leaderboards import LeaderboardSerializer, ColumnSerializer
from api.serializers.profiles import CollaboratorSerializer
from api.serializers.submissions import SubmissionScoreSerializer
from api.serializers.tasks import PhaseTaskInstanceSerializer
from competitions.models import Competition, Phase, Page, CompetitionCreationTaskStatus, CompetitionParticipant
from forums.models import Forum
from leaderboards.models import Leaderboard
from profiles.models import User
from tasks.models import Task

from api.serializers.queues import QueueSerializer
from datetime import datetime
from django.utils.timezone import now


class PhaseSerializer(WritableNestedModelSerializer):
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=True, allow_null=False, slug_field='key',
                                         many=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Phase
        fields = (
            'id',
            'index',
            'start',
            'end',
            'name',
            'description',
            'status',
            'execution_time_limit',
            'tasks',
            'has_max_submissions',
            'max_submissions_per_day',
            'max_submissions_per_person',
            'auto_migrate_to_this_phase',
            'hide_output',
            'leaderboard',
            'public_data',
            'starting_kit',
            'is_final_phase',
        )

    def get_status(self, obj):

        now = datetime.now().replace(tzinfo=None)
        start = obj.start.replace(tzinfo=None)
        end = obj.end.replace(tzinfo=None) if obj.end else obj.end
        phase_ended = False
        phase_started = False

        # check if phase has started
        if start > now:
            # start date is in the future, phase started = NO
            phase_started = False
        else:
            # start date is not in the future, phase started = YES
            phase_started = True

        if phase_started:
            # check if end date exists for this phase
            if end:
                if end < now:
                    # Phase cannote accept submissions if end date is in the past
                    phase_ended = True
                else:
                    # Phase can accept submissions if end date is in the future
                    phase_ended = False
            else:
                # Phase can accept submissions if end date is not given
                phase_ended = False

        if phase_started and phase_ended:
            return Phase.PREVIOUS
        elif phase_started and (not phase_ended):
            return Phase.CURRENT
        elif not phase_started:
            return Phase.NEXT

    def validate_leaderboard(self, value):
        if not value:
            raise ValidationError("Phases require a leaderboard")
        return value


class PhaseDetailSerializer(serializers.ModelSerializer):
    tasks = PhaseTaskInstanceSerializer(source='task_instances', many=True)
    status = serializers.SerializerMethodField()
    public_data = DataDetailSerializer(read_only=True)
    starting_kit = DataDetailSerializer(read_only=True)
    used_submissions_per_day = serializers.SerializerMethodField()
    used_submissions_per_person = serializers.SerializerMethodField()

    class Meta:
        model = Phase
        fields = (
            'id',
            'index',
            'start',
            'end',
            'name',
            'description',
            'status',
            'execution_time_limit',
            'tasks',
            'has_max_submissions',
            'max_submissions_per_day',
            'max_submissions_per_person',
            'auto_migrate_to_this_phase',
            'hide_output',
            # no leaderboard
            'public_data',
            'starting_kit',
            'is_final_phase',
            'used_submissions_per_day',
            'used_submissions_per_person'

        )

    def get_status(self, obj):

        now = datetime.now().replace(tzinfo=None)
        start = obj.start.replace(tzinfo=None)
        end = obj.end.replace(tzinfo=None) if obj.end else obj.end
        phase_ended = False
        phase_started = False

        # check if phase has started
        if start > now:
            # start date is in the future, phase started = NO
            phase_started = False
        else:
            # start date is not in the future, phase started = YES
            phase_started = True

        if phase_started:
            # check if end date exists for this phase
            if end:
                if end < now:
                    # Phase cannote accept submissions if end date is in the past
                    phase_ended = True
                else:
                    # Phase can accept submissions if end date is in the future
                    phase_ended = False
            else:
                # Phase can accept submissions if end date is not given
                phase_ended = False

        if phase_started and phase_ended:
            return Phase.PREVIOUS
        elif phase_started and (not phase_ended):
            return Phase.CURRENT
        elif not phase_started:
            return Phase.NEXT

    def get_used_submissions_per_day(self, obj):

        # Check if 'request' key exists in the context
        if 'request' in self.context:
            # Get user from the request
            user = self.context['request'].user
            if user.is_authenticated:
                # Get all submissions which are not failed and belongs to this user for this phase
                qs = obj.submissions.filter(owner=user, parent__isnull=True).exclude(status='Failed')
                # Count submissions made today
                daily_submission_count = qs.filter(created_when__day=now().day).count()
                return daily_submission_count
        return 0

    def get_used_submissions_per_person(self, obj):

        # Check if 'request' key exists in the context
        if 'request' in self.context:
            # Get user from the request
            user = self.context['request'].user
            if user.is_authenticated:
                # Get all submissions which are not failed and belongs to this user for this phase
                qs = obj.submissions.filter(owner=user, parent__isnull=True).exclude(status='Failed')
                # Count all submissions
                total_submission_count = qs.count()
                return total_submission_count
        return 0


class PhaseUpdateSerializer(PhaseSerializer):
    tasks = PhaseTaskInstanceSerializer(source='task_instances', many=True)


class PageSerializer(WritableNestedModelSerializer):
    # *NOTE* The competition property has to be replicated at the end of the file
    # after the CompetitionSerializer class is declared
    # competition = CompetitionSerializer(many=True)

    class Meta:
        model = Page
        fields = (
            'id',
            'title',
            'content',
            'index',
        )


class CompetitionSerializer(DefaultUserCreateMixin, WritableNestedModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    pages = PageSerializer(many=True)
    phases = PhaseSerializer(many=True)
    collaborators = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    queue = QueueSerializer(required=False, allow_null=True)
    # We're using a Base64 image field here so we can send JSON for create/update of this object, if we wanted
    # include the logo as a _file_ then we would need to use FormData _not_ JSON.
    logo = NamedBase64ImageField(required=True, allow_null=True)

    class Meta:
        model = Competition
        user_field = 'created_by'
        fields = (
            'id',
            'title',
            'published',
            'secret_key',
            'created_by',
            'created_when',
            'logo',
            'docker_image',
            'pages',
            'phases',
            'collaborators',
            'description',
            'terms',
            'registration_auto_approve',
            'queue',
            'enable_detailed_results',
            'make_programs_available',
            'make_input_data_available',
            'docker_image',
            'allow_robot_submissions',
            'competition_type',
            'fact_sheet',
            'reward',
            'contact_email',
            'report',
        )

    def validate_phases(self, phases):
        if not phases or len(phases) <= 0:
            raise ValidationError("Competitions must have at least one phase")
        if len(phases) == 1 and phases[0].get('auto_migrate_to_this_phase'):
            raise ValidationError("You cannot auto migrate in a competition with one phase")
        if phases[0].get('auto_migrate_to_this_phase') is True:
            raise ValidationError("You cannot auto migrate to the first phase of a competition")
        return phases

    def validate_fact_sheet(self, fact_sheet):
        if not bool(fact_sheet):
            return None
        if not isinstance(fact_sheet, dict):
            raise ValidationError("Not valid JSON")

        expected_keys = {"key", "type", "title", "selection", "is_required", "is_on_leaderboard"}
        valid_question_types = {"checkbox", "text", "select"}
        for key, value in fact_sheet.items():
            missing_keys = expected_keys.symmetric_difference(set(value.keys()))
            if missing_keys:
                raise ValidationError(f'Missing {missing_keys} values for {key}')
            if key != value['key']:
                raise ValidationError(f"key:{value['key']}  does not match JSON key:{key}")
            if value['type'] not in valid_question_types:
                raise ValidationError(f"{value['type']} is not a valid question type")
        return fact_sheet

    def create(self, validated_data):
        if 'logo' not in validated_data:
            raise ValidationError("Competitions require a logo upon creation")

        instance = super().create(validated_data)

        # Ensure a forum is created for this competition
        Forum.objects.create(competition=instance)

        return instance


class CompetitionUpdateSerializer(CompetitionSerializer):
    phases = PhaseUpdateSerializer(many=True)
    queue = None


class CompetitionCreateSerializer(CompetitionSerializer):
    queue = None


class CompetitionDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    pages = PageSerializer(many=True)
    phases = PhaseDetailSerializer(many=True)
    leaderboards = serializers.SerializerMethodField()
    collaborators = CollaboratorSerializer(many=True)
    participant_status = serializers.CharField(read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    submission_count = serializers.IntegerField(read_only=True)
    queue = QueueSerializer(read_only=True)

    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'published',
            'secret_key',
            'created_by',
            'created_when',
            'logo',
            'terms',
            'pages',
            'phases',
            'leaderboards',
            'collaborators',
            'participant_status',
            'registration_auto_approve',
            'description',
            'participant_count',
            'submission_count',
            'queue',
            'enable_detailed_results',
            'make_programs_available',
            'make_input_data_available',
            'docker_image',
            'allow_robot_submissions',
            'competition_type',
            'fact_sheet',
            'forum',
            'reward',
            'contact_email',
            'report',
        )

    def get_leaderboards(self, instance):
        try:
            if instance.user_has_admin_permission(self.context['request'].user):
                qs = Leaderboard.objects.filter(phases__competition=instance).distinct('id')
            else:
                qs = Leaderboard.objects.filter(phases__competition=instance, hidden=False).distinct('id')
        except KeyError:
            raise Exception(f'KeyError on context. Context: {self.context}')
        return LeaderboardSerializer(qs, many=True).data


class CompetitionSerializerSimple(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username')
    participant_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'created_by',
            'created_when',
            'published',
            'participant_count',
            'logo',
            'description',
            'competition_type',
            'reward',
            'contact_email',
            'report',
        )


PageSerializer.competition = CompetitionSerializer(many=True, source='competition')


class CompetitionCreationTaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionCreationTaskStatus
        fields = (
            'status',
            'details',
            'resulting_competition',
            'created_by',
        )


class CompetitionParticipantSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    is_bot = serializers.BooleanField(source='user.is_bot')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = CompetitionParticipant
        fields = (
            'id',
            'username',
            'is_bot',
            'email',
            'status',
        )


class FrontPageCompetitionsSerializer(serializers.Serializer):
    popular_comps = CompetitionSerializerSimple(many=True)
    featured_comps = CompetitionSerializerSimple(many=True)


class PhaseResultsSubmissionSerializer(serializers.Serializer):
    owner = serializers.CharField()
    scores = SubmissionScoreSerializer(many=True)


class PhaseResultsTaskSerializer(serializers.Serializer):
    colWidth = serializers.IntegerField()
    id = serializers.IntegerField()
    columns = ColumnSerializer(many=True)
    name = serializers.CharField()


class PhaseResultsSerializer(serializers.Serializer):
    title = serializers.CharField()
    id = serializers.IntegerField()
    tasks = PhaseResultsTaskSerializer(many=True, read_only=True)
    submissions = PhaseResultsSubmissionSerializer(many=True)
