import os

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied

from django.core.files.base import ContentFile
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from api.serializers import datasets as serializers
from datasets.models import Data, DataGroup
from competitions.models import Competition
from api.pagination import BasicPagination
from utils.data import make_url_sassy


class DataViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  # mixins.UpdateModelMixin,  # We don't update datasets!
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Data.objects.all()
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('type', 'name', 'key', 'was_created_by_competition')
    search_fields = ('name', 'description', 'key',)
    pagination_class = BasicPagination

    def get_queryset(self):
        filters = Q(is_public=True) | Q(created_by=self.request.user)

        qs = Data.objects.filter(filters)

        qs = qs.exclude(Q(type=Data.COMPETITION_BUNDLE) | Q(name__isnull=True))

        qs = qs.select_related('created_by')

        return qs

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.DataDetailSerializer
        else:
            return serializers.DataSerializer

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "created_by": self.request.user
        }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_dataset = serializer.save()  # request_sassy_file_name is temporarily set via this serializer
        headers = self.get_success_headers(serializer.data)

        # Make an empty placeholder so we can sign a URL allowing us to upload to it
        sassy_file_name = os.path.basename(new_dataset.request_sassy_file_name)
        # encode here helps GCS do the upload, complains
        # ```TypeError: ('`data` must be bytes, received', <class 'str'>)``` otherwise
        print("uhhh??")
        print(new_dataset.request_sassy_file_name)
        print(sassy_file_name)
        print(new_dataset.data_file.name)

        new_dataset.data_file.save(sassy_file_name, ContentFile(''.encode()))
        context = {
            "key": new_dataset.key,
            "sassy_url": make_url_sassy(new_dataset.data_file.name, 'w'),
        }
        return Response(context, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        if request.user != self.get_object().created_by:
            raise PermissionDenied()
        return super().destroy(request, *args, **kwargs)


class DataGroupViewSet(ModelViewSet):
    queryset = DataGroup.objects.all()
    serializer_class = serializers.DataGroupSerializer


@api_view(['PUT'])
def upload_completed(request, key):
    # TODO: This view is weird. We have competitions, submissions, etc. that may not need to call this? We might need special behavior/metadata for "submission finalization" for example. Competitions are a unique usecase where they hold all of the metadata in the bundle itself

    try:
        dataset = Data.objects.get(created_by=request.user, key=key)
    except Data.DoesNotExist:
        raise Http404()

    dataset.upload_completed_successfully = True
    dataset.save()

    if dataset.type == Data.COMPETITION_BUNDLE:
        # Doing a local import here to avoid circular imports
        from competitions.tasks import unpack_competition
        unpack_competition.apply_async((dataset.pk,))

    return Response({"key": dataset.key})


@api_view(['POST'])
def create_competition_dump(request, competition_id):
    try:
        comp = Competition.objects.get(pk=competition_id)
        if not request.user == comp.created_by:
            return Response({"error": "Denied. You do not have access"}, status=status.HTTP_403_FORBIDDEN)
        from competitions.tasks import create_competition_dump
        create_competition_dump.delay(competition_id)
        return Response(
            {
                "status": "Success. Competition dump is being created."
            },
            status=status.HTTP_202_ACCEPTED)
    except ObjectDoesNotExist:
        return Response({"error": "Competition not found!"}, status=status.HTTP_403_FORBIDDEN)
