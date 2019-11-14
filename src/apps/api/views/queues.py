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
    serializer_class = serializers.QueueSerializer
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
            return serializers.QueueSerializer
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
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance.owner:
            raise PermissionDenied("Cannot delete a queue that is not yours")
        return super().destroy(request, *args, **kwargs)
