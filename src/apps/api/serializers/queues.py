from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from queues.models import Queue

from profiles.models import User


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


class QueueCreationSerializer(QueueOwnerMixin, serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    organizers = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Queue
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
            'id',
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
            'id',
        )
