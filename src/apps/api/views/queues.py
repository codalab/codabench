from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.pagination import BasicPagination
from api.serializers import queues as serializers
from queues.models import Queue
from queues import rabbit

# TODO:// TaskViewSimple uses simple serializer from tasks, which exists purely for the use of Select2 on phase modal
#   is there a better way to do it using get_serializer_class() method?


class QueueViewSet(ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = serializers.QueueSerializer
    filter_fields = ('owner', 'is_public')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    pagination_class = BasicPagination

    def get_queryset(self):
        show_public = self.request.query_params.get('public')
        # qs = Queue.objects.prefetch_related('solutions', 'solutions__data')
        if show_public:
            qs = self.queryset.filter(Q(is_public=True) | Q(owner=self.request.user)) | self.request.user.organized_queues.all()
        else:
            qs = self.queryset.filter(owner=self.request.user) | self.request.user.organized_queues.all()
        # Distinct so that we don't get duplicates
        return qs.order_by('-created_when').distinct()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.QueueDetailSerializer
        else:
            return serializers.QueueSerializer

    def get_serializer_context(self):
        return {
            "owner": self.request.user
        }

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
            raise PermissionDenied("Cannot update a task that is not yours")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user != instance.owner:
            raise PermissionDenied("Cannot delete a task that is not yours")
        return super().destroy(request, *args, **kwargs)
