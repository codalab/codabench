from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import tasks as serializers
from tasks.models import Task

# TODO:// TaskViewSimple uses simple serializer from tasks, which exists purely for the use of Select2 on phase modal
#   is there a better way to do it using get_serializer_class() method?


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = serializers.TaskSerializer
    filter_fields = ('created_by', 'is_public')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name', 'description',)

    def get_queryset(self):
        return Task.objects.filter(Q(is_public=True) | Q(created_by=self.request.user)).prefetch_related('solutions', 'solutions__data')


    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        # TODO: what is this doing? do we still need it?
        if not self.request:
            return {}

        return {
            "created_by": self.request.user
        }

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if request.user != task.created_by and not request.user.is_superuser:
            raise PermissionDenied("Cannot update a task that is not yours")
        return super().update(request, *args, **kwargs)

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
        return Task.objects.filter(Q(is_public=True) | Q(created_by=self.request.user))

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        # TODO: what is this doing? do we still need it?
        if not self.request:
            return {}

        return {
            "created_by": self.request.user
        }
