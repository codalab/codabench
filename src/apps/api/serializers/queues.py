from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.mixins import DefaultUserCreateMixin
from queues.models import Queue
from profiles.models import User
from django.db.models import Q


class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'id',
        )


class QueueOwnerMixin:
    def get_is_owner(self, instance):
        request = self.context.get('request')
        if not request:
            return None
        return instance.owner and instance.owner == request.user


class QueueCreationSerializer(QueueOwnerMixin, DefaultUserCreateMixin, serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    organizers = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Queue
        user_field = 'owner'
        fields = (
            'name',
            'is_public',
            'organizers',
            'owner',
            'broker_url',
            'vhost',
            'created_when',
            'is_owner',
            'id',
        )
        read_only_fields = (
            'owner',
            'broker_url',
            'vhost',
            'created_when',
            'is_owner',
        )

    def validate(self, attrs):
        request = self.context.get('request')
        if request.user.queues.count() == request.user.rabbitmq_queue_limit and not request.user.is_superuser:
            raise PermissionDenied("User has reached queue limit!")
        return super().validate(attrs)


class QueueSerializer(QueueOwnerMixin, serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    owner = serializers.CharField(source='owner.username', read_only=True)
    organizers = OrganizerSerializer(many=True, read_only=True)

    class Meta:
        model = Queue
        fields = (
            'name',
            'vhost',
            'is_public',
            'owner',
            'organizers',
            'broker_url',
            'created_when',
            'is_owner',
            'id',
        )
        # This serializer is read only, basically..
        read_only_fields = (
            'name',
            'vhost',
            'is_public',
            'owner',
            'organizers',
            'broker_url',
            'created_when',
            'is_owner',
        )


class QueueListSerializer(QueueSerializer):
    competitions = serializers.SerializerMethodField()

    class Meta(QueueSerializer.Meta):
        fields = QueueSerializer.Meta.fields + ('competitions',)

    def get_competitions(self, obj):
        # get user from the context request
        user = self.context['request'].user

        # for super user return all competiitons using this queue
        # for admin return competitions where this user is organizer using this queue
        # for non-admin return public competitions using this queue
        if user.is_superuser:
            # Fetch all competitions
            competitions = obj.competitions.all().values('id', 'title')
        else:
            # Fetch all competitions where user is organizer or competition is published
            competitions = obj.competitions.filter(
                Q(published=True) |
                Q(created_by=user) |
                Q(collaborators=user)
            ).values('id', 'title')

        return competitions
