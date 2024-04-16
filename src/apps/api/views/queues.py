from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from queues.models import Queue
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.pagination import BasicPagination
from api.serializers import queues as serializers


class QueueViewSet(ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = serializers.QueueListSerializer
    filter_fields = ('owner', 'is_public', 'name')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    pagination_class = BasicPagination

    def get_queryset(self):
        qs = self.queryset.prefetch_related('organizers')
        filters = Q(owner=self.request.user)
        if self.request.query_params.get('public'):
            filters |= Q(is_public=True)
        qs = qs.filter(filters) | self.request.user.organized_queues.all()
        return qs.distinct().order_by('name')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.QueueListSerializer
        else:
            return serializers.QueueCreationSerializer

    def create(self, request, *args, **kwargs):
        temp_data = request.data
        temp_data['owner'] = self.request.user.pk
        serializer = self.get_serializer(data=temp_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        queue = self.get_object()
        if request.user != queue.owner and not request.user.is_superuser:
            raise PermissionDenied("Cannot update a queue that is not yours")

        # Get the original value of is_public before updating
        before_update_queue_is_public = queue.is_public

        # Get the competitions that are using this queue
        competitions = queue.competitions.all()

        # Update the queue
        updated_queue_response = super().update(request, *args, **kwargs)

        # If the queue `is_public`` field is updated to False, then update competitions
        if 'is_public' in request.data and not request.data['is_public'] and before_update_queue_is_public:

            # Set the queue field in all competitions to NULL
            # which do not belong to the user
            for competition in competitions:
                if competition.created_by != request.user:
                    competition.queue = None
                    competition.save()

        return updated_queue_response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance.owner:
            raise PermissionDenied("Cannot delete a queue that is not yours")
        return super().destroy(request, *args, **kwargs)
