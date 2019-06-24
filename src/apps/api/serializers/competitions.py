from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from api.fields import NamedBase64ImageField
from api.serializers.leaderboards import LeaderboardSerializer
from api.serializers.profiles import CollaboratorSerializer
from api.serializers.tasks import TaskSerializerSimple
from competitions.models import Competition, Phase, Page, CompetitionCreationTaskStatus
from profiles.models import User
from tasks.models import Task


class PhaseSerializer(WritableNestedModelSerializer):
    tasks = serializers.SlugRelatedField(queryset=Task.objects.all(), required=False, allow_null=True, slug_field='key',
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
        )


class PhaseDetailSerializer(serializers.ModelSerializer):
    tasks = TaskSerializerSimple(many=True)

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
            'has_max_submissions',
            'max_submissions_per_day',
            'max_submissions_per_person',
        )


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


class CompetitionSerializer(WritableNestedModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
    logo = NamedBase64ImageField(required=True)
    pages = PageSerializer(many=True)
    phases = PhaseSerializer(many=True)
    leaderboards = LeaderboardSerializer(many=True)
    collaborators = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

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
            'pages',
            'phases',
            'leaderboards',
            'collaborators',
        )

    def get_created_by(self, object):
        return str(object.created_by)

    def validate_leaderboards(self, value):
        if not value:
            raise serializers.ValidationError("Competitions require at least 1 leaderboard")
        return value

    def validate_phases(self, attrs):
        if not attrs['phases'] or len(attrs['phases'] <= 0):
            raise serializers.ValidationError("Competitions must have at least one phase")
        if attrs['phases'][0]['auto_migrate_to_this_phase']:
            raise serializers.ValidationError("You cannot auto migrate to the first phase of a competition")
        if len(attrs['phases']) == 1 and attrs['phases'][0]['auto_migrate_to_this_phase']:
            raise serializers.ValidationError("You cannot auto migrate in a competition with one phase")

        return attrs

    def create(self, validated_data):
        validated_data["created_by"] = self.context['created_by']
        return super().create(validated_data)


class CompetitionDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    logo = NamedBase64ImageField(required=True)
    pages = PageSerializer(many=True)
    phases = PhaseDetailSerializer(many=True)
    leaderboards = LeaderboardSerializer(many=True)
    collaborators = CollaboratorSerializer(many=True)

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
            'pages',
            'phases',
            'leaderboards',
            'collaborators',
        )


class CompetitionSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'created_when',
            'published'
        )


PageSerializer.competition = CompetitionSerializer(many=True, source='competition')


class CompetitionCreationTaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionCreationTaskStatus
        fields = (
            'status',
            'details',
            'resulting_competition',
        )
