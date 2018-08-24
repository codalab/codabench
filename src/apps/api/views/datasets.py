import os

from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from uuid import UUID

from django.core.files.base import ContentFile
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers import datasets as serializers
from datasets.models import Data, DataGroup
from datasets.utils import _make_url_sassy


class DataViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  # mixins.UpdateModelMixin,  # We don't update datasets!
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Data.objects.all()
    serializer_class = serializers.DataSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('type', 'name', 'key',)
    search_fields = ('name', 'description',)

    def get_queryset(self):
        filters = Q(is_public=True) | Q(created_by=self.request.user)

        # query = self.request.query_params.get('q', None)
        # # Check if they are searching for a UUID
        # if query is not None and len(query) > 15:
        #     try:
        #         filters |= Q(key=UUID(query))
        #     except ValueError:
        #         # Not a valid uuid, ignore
        #         pass
        qs = Data.objects.filter(filters)

        qs = qs.exclude(type=Data.COMPETITION_BUNDLE)

        return qs

    def get_serializer_context(self):
        return {
            "created_by": self.request.user
        }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_dataset = serializer.save()
        headers = self.get_success_headers(serializer.data)

        data = serializer.data

        sassy_file_name = request.data.get('request_sassy_file_name')
        if sassy_file_name:
            # we didn't have a data file so let's make a sassy URL
            sassy_file_name = os.path.basename(sassy_file_name)
            new_dataset.data_file.save(sassy_file_name, ContentFile(''))
            data['sassy_url'] = _make_url_sassy(new_dataset.data_file.name, 'w')

        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        if request.user != self.get_object().created_by:
            raise PermissionDenied()
        return super().destroy(request, *args, **kwargs)


class DataGroupViewSet(ModelViewSet):
    queryset = DataGroup.objects.all()
    serializer_class = serializers.DataGroupSerializer


#
#
# """
#
# Make `request upload` and `upload completed` API endpoints! (and `do upload` for local storage?)
#
# They should use serializers to confirm the data and such
#
# We should also have a `receive_upload` function for local storage, so everything is consistent
#
# """
#
# @api_view(['GET'])
# def request_upload(request):
#     # I need:
#     #   - Desired file name
#     #   - Dataset PK where upload_completed_successfully=False and created_by = request.user
#
#     try:
#         dataset = Data.objects.get(
#             pk=request.GET.get('pk'),
#             created_by=request.user,
#             upload_completed_successfully=False
#         )
#     except Data.DoesNotExist:
#         raise Http404()
#
#
# @api_view(['POST'])
# def upload_completed(request):
#     # if new_dataset.type == Data.COMPETITION_BUNDLE:
#     #     # Doing a local import here to avoid circular imports
#     #     from competitions.tasks import unpack_competition
#     #     unpack_competition.apply_async((new_dataset.pk,))
#
#
#     # instance.upload_completed_successfully = True
#     # instance.save()
#     pass
#
#
# # TODO: Implement this so we can do local storage and receive stdout/etc. jazz
# # def do_upload(request)
