import asyncio
from os.path import basename

from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.mixins import DefaultUserCreateMixin
from api.serializers import leaderboards
# from api.serializers.profiles import SimpleOrganizationSerializer
from api.serializers.tasks import TaskSerializer
from api.serializers.submission_leaderboard import SubmissionScoreSerializer
from competitions.models import Submission, SubmissionDetails, CompetitionParticipant, Phase
from datasets.models import Data
from utils.data import make_url_sassy

from tasks.models import Task
from queues.models import Queue


class SubmissionSerializer(serializers.ModelSerializer):
    scores = SubmissionScoreSerializer(many=True)
    filename = serializers.SerializerMethodField(read_only=True)
    owner = serializers.CharField(source='owner.username')
    phase_name = serializers.CharField(source='phase.name')
    on_leaderboard = serializers.BooleanField(read_only=True)
    task = TaskSerializer()
    created_when = serializers.DateTimeField()
    auto_run = serializers.SerializerMethodField(read_only=True)
    can_make_submissions_public = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Submission
        fields = (
            'phase_name',
            'name',
            'filename',
            'description',
            'created_when',
            'is_public',
            'is_specific_task_re_run',
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
            'fact_sheet_answers',
            'leaderboard',
            'on_leaderboard',
            'task',
            'auto_run',
            'can_make_submissions_public',
            'is_soft_deleted',
        )
        read_only_fields = (
            'pk',
            'phase',
            'scores',
            'is_specific_task_re_run',
            'leaderboard',
            'on_leaderboard',
        )

    def get_filename(self, instance):
        if instance.data and instance.data.data_file:
            return basename(instance.data.data_file.name)
        # NOTE: if submission data is None, it means it is soft deleted
        return "Deleted File"

    def get_auto_run(self, instance):
        # returns this submission's competition auto_run_submissions Flag
        return instance.phase.competition.auto_run_submissions

    def get_can_make_submissions_public(self, instance):
        # returns this submission's competition can_participants_make_submissions_public Flag
        return instance.phase.competition.can_participants_make_submissions_public


class SubmissionCreationSerializer(DefaultUserCreateMixin, serializers.ModelSerializer):
    """Used for creation _and_ status updates..."""
    data = serializers.SlugRelatedField(queryset=Data.objects.all(), required=False, allow_null=True, slug_field='key')
    filename = serializers.SerializerMethodField(read_only=True)
    tasks = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), required=False, write_only=True, many=True)
    phase = serializers.PrimaryKeyRelatedField(queryset=Phase.objects.all(), required=True)
    queue = serializers.PrimaryKeyRelatedField(queryset=Queue.objects.all(), required=False, allow_null=True)
    created_when = serializers.DateTimeField(format="%Y-%m-%d %H:%M", required=False)
    scores = SubmissionScoreSerializer(many=True, required=False)

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
            'organization',
            'queue',
            'created_when',
            'scores'
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

        # Check if auto_run_submissions is enabled then run the submission
        # Otherwise organizer will run manually
        if sub.phase.competition.auto_run_submissions:
            sub.start(tasks=tasks)

        return sub

    def validate(self, attrs):
        data = super().validate(attrs)

        if attrs.get('fact_sheet_answers'):
            fact_sheet_answers = data['fact_sheet_answers']
            fact_sheet = data['phase'].competition.fact_sheet
            if set(fact_sheet_answers.keys()) != set(fact_sheet.keys()):
                raise ValidationError("Fact Sheet keys do not match Answer keys")
            for key, value in fact_sheet_answers.items():
                if not fact_sheet[key] and not isinstance(value, str):
                    raise ValidationError(f'{value} should be string not {type(value)}')
                elif value not in fact_sheet[key]['selection'] and fact_sheet[key]['selection']:
                    raise ValidationError(f'{key}: {value} is not a valid selection from {fact_sheet[key]}')
                elif not value and fact_sheet[key]['is_required'] == 'true' and not isinstance(value, bool):
                    raise ValidationError(f'{fact_sheet[key]["title"]}({key}) requires an answer')

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

        # Cannot change submission if secret key is not valid
        if submission.secret != validated_data.get('secret'):
            raise PermissionDenied("Submission secret invalid")

        # Task of a submission cannot be updated
        if "task" in validated_data:
            raise PermissionDenied("Task of a submission cannot be update")

        # Update status if it is there in validated data
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

        if validated_data.get('status') == Submission.RUNNING and self.instance.parent is not None and self.instance.parent.status is not Submission.RUNNING:
            self.instance.parent.status = Submission.RUNNING
            self.instance.parent.save()

        if validated_data.get("status") == Submission.SCORING:
            # Start scoring because we're "SCORING" status now from compute worker
            from competitions.tasks import run_submission
            # task = validated_data.get('task_pk')
            # if not task:
            #     raise ValidationError('Cannot update submission. Task pk was not provided')
            # task = Task.objects.get(id=task)
            run_submission(submission.pk, tasks=[submission.task], is_scoring=True)

        elif validated_data.get("status") == Submission.FINISHED:
            # We finished submission, no longer need to store submission stuff in Redis, free it up!
            cache.delete(f"submission-{submission.pk}-log")

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
            'fact_sheet_answers',
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
