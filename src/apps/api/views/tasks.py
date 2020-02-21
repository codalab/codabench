from django.db.models import Q, OuterRef, Subquery
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.pagination import BasicPagination
from api.serializers import tasks as serializers
from competitions.models import Submission
from tasks.models import Task


# TODO:// TaskViewSimple uses simple serializer from tasks, which exists purely for the use of Select2 on phase modal
#   is there a better way to do it using get_serializer_class() method?


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = serializers.TaskSerializer
    filter_fields = ('created_by', 'is_public')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name', 'description',)
    pagination_class = BasicPagination

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.method == 'GET':
            qs = qs.select_related(
                'input_data',
                'reference_data',
                'ingestion_program',
                'scoring_program'
            ).prefetch_related(
                'solutions',
                'solutions__data'
            )
            if self.request.query_params.get('public'):
                qs = qs.filter(Q(is_public=True) | Q(created_by=self.request.user))
            else:
                qs = qs.filter(created_by=self.request.user)

            # Determine whether a task is "valid" by finding some solution with a
            # passing submission
            task_validate_qs = Submission.objects.filter(
                md5__in=OuterRef("solutions__md5"),
                status=Submission.FINISHED,
                phase__in=OuterRef("phases")
            )
            # We have to grab something from task_validate_qs here, so i grab pk
            qs = qs.annotate(validated=Subquery(task_validate_qs.values('pk')[:1]))

        return qs.order_by('-created_when')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            if self.action == 'list':
                return serializers.TaskListSerializer
            return serializers.TaskDetailSerializer
        return serializers.TaskSerializer

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
