import asyncio
from os.path import basename

from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.mixins import DefaultUserCreateMixin
from api.serializers import leaderboards
from api.serializers.tasks import TaskSerializer
from competitions.models import Submission, SubmissionDetails, CompetitionParticipant, Phase
from datasets.models import Data
from leaderboards.models import SubmissionScore
from utils.data import make_url_sassy

from tasks.models import Task


class SubmissionScoreSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source='column.index', read_only=True)
    column_key = serializers.CharField(source='column.key', read_only=True)

    class Meta:
        model = SubmissionScore
        fields = (
            'id',
            'index',
            'score',
            'column_key',
        )


class SubmissionSerializer(serializers.ModelSerializer):
    scores = SubmissionScoreSerializer(many=True)
    filename = serializers.SerializerMethodField(read_only=True)
    owner = serializers.CharField(source='owner.username')
    phase_name = serializers.CharField(source='phase.name')
    on_leaderboard = serializers.BooleanField(read_only=True)
    task = TaskSerializer()

    class Meta:
        model = Submission
        fields = (
            'phase_name',
            'name',
            'filename',
            'description',
            'created_when',
            'is_public',
            'status',
            'status_details',
            'owner',
            'has_children',
            'parent',
            'children',
            'pk',
            'id',
            'phase',
            'scores',
            'leaderboard',
            'on_leaderboard',
            'task',
        )
        read_only_fields = (
            'pk',
            'phase',
            'scores',
            'leaderboard',
            'on_leaderboard',
        )

    def get_filename(self, instance):
        return basename(instance.data.data_file.name)


class SubmissionLeaderBoardSerializer(serializers.ModelSerializer):
    scores = SubmissionScoreSerializer(many=True)
    owner = serializers.CharField(source='owner.username')

    class Meta:
        model = Submission
        fields = (
            'scores',
            'owner',
            'task',
            'leaderboard_id',
        )
        extra_kwargs = {
            "scores": {"read_only": True},
            "owner": {"read_only": True},
        }


class SubmissionCreationSerializer(DefaultUserCreateMixin, serializers.ModelSerializer):
    """Used for creation _and_ status updates..."""
    data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    filename = serializers.SerializerMethodField(read_only=True)
    tasks = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), required=False, write_only=True, many=True)
    phase = serializers.PrimaryKeyRelatedField(queryset=Phase.objects.all(), required=True)

    class Meta:
        model = Submission
        user_field = 'owner'
        fields = (
            'id',
            'data',
            'phase',
            'status',
            'status_details',
            'filename',
            'description',
            'secret',
            'md5',
            'tasks',
            'fact_sheet_answers',
        )
        extra_kwargs = {
            'secret': {"write_only": True},
            'description': {"read_only": True},
            # 'status': {"read_only": True},
        }

    def get_filename(self, instance):
        return basename(instance.data.data_file.name)

    def create(self, validated_data):
        tasks = validated_data.pop('tasks', None)

        sub = super().create(validated_data)
        sub.start(tasks=tasks)

        return sub

    def validate(self, attrs):
        data = super().validate(attrs)

        if attrs.get('fact_sheet_answers'):
            fact_sheet_answers = data['fact_sheet_answers']
            fact_sheet = data['phase'].competition.fact_sheet
            if set(fact_sheet_answers.keys()) != set(fact_sheet.keys()):
                raise ValidationError("Fact Sheet keys do not match Answer keys")
            for key in fact_sheet_answers.keys():
                if not fact_sheet[key] and not isinstance(fact_sheet_answers[key], str):
                    raise ValidationError(f'{fact_sheet_answers[key]} should be string not {type(fact_sheet_answers[key])}')
                elif fact_sheet_answers[key] not in fact_sheet[key] and fact_sheet[key]:
                    raise ValidationError(f'{key}: {fact_sheet_answers[key]} is not a valid selection from {fact_sheet[key]}')

        # Make sure selected tasks are part of the phase
        if attrs.get('tasks'):
            if not all(_ in attrs['phase'].tasks.all() for _ in attrs['tasks']):
                raise ValidationError("All tasks must be part of the current phase.")

        # Only on create (when we don't have instance set) check permissions
        if not self.instance:
            is_in_competition = data["phase"].competition.participants.filter(
                user=self.context["request"].user,
                status=CompetitionParticipant.APPROVED
            ).exists()
            if not is_in_competition:
                raise PermissionDenied("You do not have access to this competition to make a submission")

        return data

    def update(self, submission, validated_data):
        # TODO: Test, could you change the phase of a submission?
        if submission.secret != validated_data.get('secret'):
            raise PermissionDenied("Submission secret invalid")

        if "status" in validated_data:
            # Received a status update, let the frontend know
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()

            loop.run_until_complete(channel_layer.group_send(f"submission_listening_{submission.owner.pk}", {
                'type': 'submission.message',
                'text': {
                    "kind": "status_update",
                    "status": validated_data["status"],
                },
                'submission_id': submission.id,
            }))

        if validated_data.get("status") == Submission.SCORING:
            # Start scoring because we're "SCORING" status now from compute worker
            from competitions.tasks import run_submission
            # task = validated_data.get('task_pk')
            # if not task:
            #     raise ValidationError('Cannot update submission. Task pk was not provided')
            # task = Task.objects.get(id=task)
            run_submission(submission.pk, tasks=[submission.task], is_scoring=True)
        resp = super().update(submission, validated_data)
        if submission.parent:
            submission.parent.check_child_submission_statuses()
        return resp


class SubmissionDetailSerializer(serializers.ModelSerializer):
    data_file = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionDetails
        fields = (
            'name',
            'data_file',
        )

    def get_data_file(self, instance):
        return make_url_sassy(instance.data_file.name)


class SubmissionFilesSerializer(serializers.ModelSerializer):
    logs = serializers.SerializerMethodField()
    data_file = serializers.SerializerMethodField()
    prediction_result = serializers.SerializerMethodField()
    scoring_result = serializers.SerializerMethodField()
    detailed_result = serializers.SerializerMethodField()
    leaderboards = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = (
            'logs',
            'data_file',
            'prediction_result',
            'detailed_result',
            'scoring_result',
            'leaderboards',
        )

    def get_logs(self, instance):
        if instance.phase.hide_output and not instance.phase.competition.user_has_admin_permission(self.context['request'].user):
            return []
        return SubmissionDetailSerializer(instance.details.all(), many=True).data

    def get_data_file(self, instance):
        return make_url_sassy(instance.data.data_file.name)

    def get_prediction_result(self, instance):
        if instance.prediction_result.name:
            if instance.phase.hide_output and not instance.phase.competition.user_has_admin_permission(self.context['request'].user):
                return None
            return make_url_sassy(instance.prediction_result.name)

    def get_detailed_result(self, instance):
        if instance.detailed_result.name:
            return make_url_sassy(instance.detailed_result.name)

    def get_scoring_result(self, instance):
        if instance.scoring_result.name:
            if instance.phase.hide_output and not instance.phase.competition.user_has_admin_permission(self.context['request'].user):
                return None
            return make_url_sassy(instance.scoring_result.name)

    def get_leaderboards(self, instance):
        if instance.phase.hide_output and not instance.phase.competition.user_has_admin_permission(self.context['request'].user):
            return None
        boards = list(set([score.column.leaderboard for score in instance.scores.all().select_related('column__leaderboard')]))
        return [leaderboards.LeaderboardSerializer(lb).data for lb in boards]
