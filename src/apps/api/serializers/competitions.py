from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.fields import NamedBase64ImageField
from api.mixins import DefaultUserCreateMixin
from api.serializers.leaderboards import LeaderboardSerializer, ColumnSerializer
from api.serializers.profiles import CollaboratorSerializer
from api.serializers.submissions import SubmissionScoreSerializer
from api.serializers.tasks import PhaseTaskInstanceSerializer
from competitions.models import Competition, Phase, Page, CompetitionCreationTaskStatus, CompetitionParticipant
from leaderboards.models import Leaderboard
from profiles.models import User
from tasks.models import Task

from api.serializers.queues import QueueSerializer


class PhaseSerializer(WritableNestedModelSerializer):
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=True, allow_null=False, slug_field='key',
                                         many=True)

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
            'is_final_phase',
        )

    def validate_leaderboard(self, value):
        if not value:
            raise ValidationError("Phases require a leaderboard")
        return value


class PhaseDetailSerializer(serializers.ModelSerializer):
    tasks = PhaseTaskInstanceSerializer(source='task_instances', many=True)

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
            'tasks',
            'auto_migrate_to_this_phase',
            'has_max_submissions',
            'max_submissions_per_day',
            'max_submissions_per_person',
            'execution_time_limit',
            'hide_output',
            'is_final_phase',
        )


class PhaseUpdateSerializer(PhaseSerializer):
    tasks = PhaseTaskInstanceSerializer(source='task_instances', many=True)
    leaderboard = LeaderboardSerializer(many=False)


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
            'docker_image',
            'allow_robot_submissions',
            'competition_type',
            'fact_sheet',
        )

    def validate_phases(self, phases):
        if not phases or len(phases) <= 0:
            raise ValidationError("Competitions must have at least one phase")
        if len(phases) == 1 and phases[0].get('auto_migrate_to_this_phase'):
            raise ValidationError("You cannot auto migrate in a competition with one phase")
        if phases[0].get('auto_migrate_to_this_phase') is True:
            raise ValidationError("You cannot auto migrate to the first phase of a competition")
        return phases

    def create(self, validated_data):
        if 'logo' not in validated_data:
            raise ValidationError("Competitions require a logo upon creation")
        return super().create(validated_data)


class CompetitionUpdateSerializer(CompetitionSerializer):
    phases = PhaseUpdateSerializer(many=True)


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
    fact_sheet = serializers.SerializerMethodField(read_only=True)

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
            'docker_image',
            'allow_robot_submissions',
            'competition_type',
            'fact_sheet',
            # 'fact_sheet_questions',
        )

    def get_fact_sheet(self, instance):
        fact_sheet = instance.fact_sheet
        if fact_sheet:
            fact_sheet_questions = []
            for key in fact_sheet.keys():
                if not fact_sheet[key]:
                    fact_sheet_questions.append({
                        "label": key,
                        "type": "text",
                    })
                elif type(fact_sheet[key]) is list:
                    if type(fact_sheet[key][0]) is bool:
                        fact_sheet_questions.append({
                            "label": key,
                            "type": "checkbox",
                        })
                    else:
                        fact_sheet_questions.append({
                            "label": key,
                            "type": "select",
                            "selection": fact_sheet[key],
                        })
                else:
                    raise ValidationError("Fact Sheet Format Error")
            return fact_sheet_questions
        else:
            return None

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
    participant_count = serializers.CharField(read_only=True)

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
