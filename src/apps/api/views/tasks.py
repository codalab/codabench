from collections import defaultdict

from django.db.models import Q, OuterRef, Subquery
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.pagination import BasicPagination
from api.serializers import tasks as serializers
from competitions.models import Submission, Phase
from profiles.models import User
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

            task_filter = Q(created_by=self.request.user) | Q(shared_with=self.request.user)
            if self.request.query_params.get('public'):
                task_filter |= Q(is_public=True)

            qs = qs.filter(task_filter)

            # Determine whether a task is "valid" by finding some solution with a
            # passing submission
            task_validate_qs = Submission.objects.filter(
                md5__in=OuterRef("solutions__md5"),
                status=Submission.FINISHED,
                # TODO: This line causes our query to take ~10 seconds. Is this important?
                # phase__in=OuterRef("phases")
            )
            # We have to grab something from task_validate_qs here, so i grab pk
            qs = qs.annotate(validated=Subquery(task_validate_qs.values('pk')[:1]))

        return qs.order_by('-created_when').distinct()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            if self.action == 'list':
                return serializers.TaskListSerializer
            return serializers.TaskDetailSerializer
        return serializers.TaskSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        qs = self.get_queryset()

        phases = Phase.objects.filter(tasks__pk__in=qs.values_list('pk', flat=True))
        context['task_titles'] = defaultdict(list)
        for task in phases.values('tasks__pk', 'competition__title'):
            context['task_titles'][task['tasks__pk']].append(task['competition__title'])

        users = User.objects.filter(shared_tasks__pk__in=qs.values_list('pk', flat=True))
        context['shared_with'] = defaultdict(list)
        for user in users.values('username', 'shared_tasks__pk'):
            context['shared_with'][user['shared_tasks__pk']].append(user['username'])

        return context

    def update(self, request, *args, **kwargs):

        # Get task
        task = self.get_object()

        # Raise error if user is not the creator of the task or not a super user
        if request.user != task.created_by and not request.user.is_superuser:
            raise PermissionDenied("Cannot update a task that is not yours")

        # Check if 'is_public' is sent in the data
        # This means that from the front end the update is_public api is calle
        # with `is_public` in the data
        if 'is_public' in request.data:
            # Perform the update using the parent class's update method
            super().update(request, *args, **kwargs)
        else:
            # If the key is not in the request data, set the corresponding field to None
            # No condition for scoring program because a task must have a scoring program
            if "ingestion_program" not in request.data:
                task.ingestion_program = None
            if "input_data" not in request.data:
                task.input_data = None
            if "reference_data" not in request.data:
                task.reference_data = None

            # Save the task to apply the changes
            task.save()
            super().update(request, *args, **kwargs)

        # Fetch the updated task from the database to ensure it reflects all changes
        task.refresh_from_db()

        # Serialize the updated task using TaskDetailSerializer
        task_detail_serializer = serializers.TaskDetailSerializer(task)

        # Return the serialized data as a response
        return Response(task_detail_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        error = self.check_delete_permissions(request, instance)

        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=('POST',))
    def delete_many(self, request):
        qs = Task.objects.filter(id__in=request.data)
        errors = {}

        for task in qs:
            error = self.check_delete_permissions(request, task)
            if error:
                errors[task.name] = error

        if not errors:
            qs.delete()

        return Response(
            errors if errors else {'detail': 'Tasks deleted successfully'},
            status=status.HTTP_400_BAD_REQUEST if errors else status.HTTP_200_OK
        )

    # This function allows for multiple errors when deleting multiple objects
    def check_delete_permissions(self, request, task):
        if request.user != task.created_by:
            return "Cannot delete a task that is not yours"
        if task.phases.exists():
            return 'Cannot delete task: task is being used by a phase'
