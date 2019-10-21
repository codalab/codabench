from rest_framework import serializers
from queues.models import Queue

from profiles.models import User


class QueueSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    organizers = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Queue
        fields = [
            'name',
            'vhost',
            'is_public',
            'owner',
            'organizers',
            'broker_url',
            'created_when',
            'is_owner',
            'id',
        ]
        read_only_fields = [
            'broker_url',
            'vhost',
            'created_when',
            'is_owner',
        ]

    def get_is_owner(self, instance):
        if instance.owner == self.context.get('owner'):
            return True
        return False


class QueueDetailSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    organizers = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    owner = serializers.CharField(source='owner.username', read_only=True)
    organizers = serializers.SerializerMethodField()

    class Meta:
        model = Queue
        fields = [
            'name',
            'vhost',
            'is_public',
            'owner',
            'organizers',
            'broker_url',
            'created_when',
            'is_owner',
            'id',
        ]
        read_only_fields = [
            'broker_url',
            'vhost',
            'created_when',
            'is_owner',
        ]

    def get_is_owner(self, instance):
        if instance.owner == self.context.get('owner'):
            return True
        return False

    def get_organizers(self, instance):
        return instance.organizers.values('username', 'email', 'id')
