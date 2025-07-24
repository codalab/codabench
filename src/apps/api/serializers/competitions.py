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
from competitions.models import Competition, Phase, Page, CompetitionCreationTaskStatus, CompetitionParticipant, CompetitionWhiteListEmail
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
    is_final_phase = serializers.SerializerMethodField()

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
            'hide_prediction_output',
            'hide_score_output',
            'leaderboard',
            'public_data',
            'starting_kit',
            'is_final_phase',
        )

    def get_is_final_phase(self, obj):
        if len(obj.competition.phases.all()) > 1:
            return obj.is_final_phase
        elif len(obj.competition.phases.all()) == 1:
            obj.is_final_phase = True
            obj.save()
            return obj.is_final_phase

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
            'hide_prediction_output',
            'hide_score_output',
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
                daily_submission_count = qs.filter(created_when__date=now().date()).count()
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


class CompetitionWhitelistSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionWhiteListEmail
        fields = ['email']


class CompetitionSerializer(DefaultUserCreateMixin, WritableNestedModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    pages = PageSerializer(many=True)
    phases = PhaseSerializer(many=True)
    collaborators = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    queue = QueueSerializer(required=False, allow_null=True)
    # We're using a Base64 image field here so we can send JSON for create/update of this object, if we wanted
    # include the logo as a _file_ then we would need to use FormData _not_ JSON.
    logo = NamedBase64ImageField(required=True, allow_null=True)
    whitelist_emails = CompetitionWhitelistSerializer(many=True, required=False)

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
            'show_detailed_results_in_submission_panel',
            'show_detailed_results_in_leaderboard',
            'auto_run_submissions',
            'can_participants_make_submissions_public',
            'make_programs_available',
            'make_input_data_available',
            'docker_image',
            'allow_robot_submissions',
            'competition_type',
            'fact_sheet',
            'reward',
            'contact_email',
            'report',
            'whitelist_emails',
            'forum_enabled'
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

    def update(self, instance, validated_data):

        # Get the updated whitelist emails from the validated data
        updated_whitelist_emails = validated_data.get('whitelist_emails', [])

        # Delete all existing emails
        instance.whitelist_emails.all().delete()

        # Save the updated whitelist emails to the instance
        for whitelist_email in updated_whitelist_emails:
            CompetitionWhiteListEmail.objects.create(competition=instance, email=whitelist_email["email"])

        # Remove the 'whitelist_emails' key from validated_data to prevent it from being processed again
        validated_data.pop('whitelist_emails', None)

        # Continue with the regular update process
        collaborators = validated_data.get('collaborators', None)
        instance = super(CompetitionSerializer, self).update(instance, validated_data)

        # Django 3.0 doesn't automatically cascade updates through many to many relationships
        # Rationale is that there is too much "magic" in database operations through ORM
        # Therefore we need to explicitly create collaborator users in the CompetitionParticipant table
        if collaborators is not None:
            # First update the M2M relationship
            instance.collaborators.set(collaborators)

            # Then ensure each collaborator has a CompetitionParticipant entry
            # Also set to 'pending' as '_ensure_organizer_participants_accepted' in
            # src/aops/api/views/competitions.py 'CompetitionViewSet'
            # adjusts the status to 'approved'
            for collaborator in collaborators:
                CompetitionParticipant.objects.get_or_create(
                    user=collaborator,
                    competition=instance,
                    defaults={
                        'status': 'pending',
                    }
                )

        return instance


class CompetitionUpdateSerializer(CompetitionSerializer):
    phases = PhaseUpdateSerializer(many=True)
    queue = None


class CompetitionCreateSerializer(CompetitionSerializer):
    queue = None


class CompetitionDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    owner_display_name = serializers.SerializerMethodField()
    logo_icon = NamedBase64ImageField(allow_null=True)
    pages = PageSerializer(many=True)
    phases = PhaseDetailSerializer(many=True)
    leaderboards = serializers.SerializerMethodField()
    collaborators = CollaboratorSerializer(many=True)
    participant_status = serializers.CharField(read_only=True)
    participants_count = serializers.IntegerField(read_only=True)
    submissions_count = serializers.IntegerField(read_only=True)
    queue = QueueSerializer(read_only=True)
    whitelist_emails = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'published',
            'secret_key',
            'created_by',
            'owner_display_name',
            'created_when',
            'logo',
            'logo_icon',
            'terms',
            'pages',
            'phases',
            'leaderboards',
            'collaborators',
            'participant_status',
            'registration_auto_approve',
            'description',
            'participants_count',
            'submissions_count',
            'queue',
            'enable_detailed_results',
            'show_detailed_results_in_submission_panel',
            'show_detailed_results_in_leaderboard',
            'auto_run_submissions',
            'can_participants_make_submissions_public',
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
            'whitelist_emails',
            'forum_enabled'
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

    def get_whitelist_emails(self, instance):
        whitelist_emails_query = instance.whitelist_emails.all()
        whitelist_emails_list = [entry.email for entry in whitelist_emails_query]
        return whitelist_emails_list

    def get_owner_display_name(self, obj):
        # Get the user's display name if not None, otherwise return username
        return obj.created_by.display_name if obj.created_by.display_name else obj.created_by.username

    def to_representation(self, instance):
        """
        This is a built-in function where we can choose which fields to include in the serializer's output
        """
        representation = super().to_representation(instance)
        user = self.context['request'].user

        # If user is not admin/creator/collaborator then do not include secret_key and whitelist_emails
        if not instance.user_has_admin_permission(user):
            representation.pop('secret_key', None)
            representation.pop('whitelist_emails', None)

        return representation


class CompetitionSerializerSimple(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    owner_display_name = serializers.SerializerMethodField()
    participants_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'created_by',
            'owner_display_name',
            'created_when',
            'published',
            'participants_count',
            'logo',
            'logo_icon',
            'description',
            'competition_type',
            'reward',
            'contact_email',
            'report',
            'is_featured',
            'submissions_count',
            'participants_count'
        )

    def get_created_by(self, obj):
        # Get the user's display name if not None, otherwise return username
        return obj.created_by.display_name if obj.created_by.display_name else obj.created_by.username

    def get_owner_display_name(self, obj):
        # Get the user's display name if not None, otherwise return username
        return obj.created_by.display_name if obj.created_by.display_name else obj.created_by.username


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
    is_deleted = serializers.BooleanField(source='user.is_deleted')

    class Meta:
        model = CompetitionParticipant
        fields = (
            'id',
            'username',
            'is_bot',
            'email',
            'status',
            'is_deleted',
        )


class FrontPageCompetitionsSerializer(serializers.Serializer):
    popular_comps = CompetitionSerializerSimple(many=True)
    recent_comps = CompetitionSerializerSimple(many=True)


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
