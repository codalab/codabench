from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import tasks as serializers
from tasks.models import Task


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = serializers.TaskSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    # filter_fields = ('type', 'name', 'key',)
    search_fields = ('name', 'description',)

    def get_queryset(self):
        filters = Q(is_public=True) | Q(created_by=self.request.user)
        qs = Task.objects.filter(filters)
        return qs

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "created_by": self.request.user
        }

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance.created_by:
            raise PermissionDenied("Cannot delete a task that is not yours")
        return super().destroy(request, *args, **kwargs)


class TaskViewSetSimple(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = serializers.TaskSerializerSimple
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)

    def get_queryset(self):
        filters = Q(is_public=True) | Q(created_by=self.request.user)
        qs = Task.objects.filter(filters)
        return qs

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "created_by": self.request.user
        }
