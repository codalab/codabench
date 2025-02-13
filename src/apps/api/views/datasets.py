import os

from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.pagination import BasicPagination
from api.serializers import datasets as serializers
from datasets.models import Data, DataGroup
from competitions.models import CompetitionCreationTaskStatus
from utils.data import make_url_sassy, pretty_bytes, gb_to_bytes


class DataViewSet(ModelViewSet):
    queryset = Data.objects.all()
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('type', 'name', 'key', 'was_created_by_competition', 'is_public')
    search_fields = ('file_name', 'name', 'description', 'key', 'competition__title',)
    pagination_class = BasicPagination

    def get_queryset(self):

        if self.request.method == 'GET':

            # filters
            # -----------

            # _public = true if want to show public datasets/submissions
            is_public = self.request.query_params.get('_public', 'false') == 'true'

            # _type = submission if called from submissions tab to filter only submissions
            is_submission = self.request.query_params.get('_type', '') == 'submission'

            # _type = dataset if called from datasets and programs tab to filter datasets and programs
            is_dataset = self.request.query_params.get('_type', '') == 'dataset'

            # _type = dataset if called from datasets and programs tab to filter datasets and programs
            is_bundle = self.request.query_params.get('_type', '') == 'bundle'

            # get queryset
            qs = self.queryset

            # filter submissions
            if is_submission:
                qs = qs.filter(Q(type=Data.SUBMISSION))

            # filter datasets and programs
            if is_dataset:
                qs = qs.filter(~Q(type=Data.SUBMISSION))
                qs = qs.exclude(Q(type=Data.COMPETITION_BUNDLE))

            # filter bundles
            if is_bundle:
                qs = qs.filter(Q(type=Data.COMPETITION_BUNDLE))

            # public filter check
            if is_public:
                qs = qs.filter(Q(created_by=self.request.user) | Q(is_public=True))
            else:
                qs = qs.filter(Q(created_by=self.request.user))

            # if GET is called but provided no filters, fall back to default behaviour
            if (not is_submission) and (not is_dataset) and (not is_bundle) and (not is_public):
                qs = self.queryset
                qs = qs.filter(Q(is_public=True) | Q(created_by=self.request.user))

        else:
            qs = self.queryset
            qs = qs.filter(Q(is_public=True) | Q(created_by=self.request.user))

        qs = qs.exclude(Q(name__isnull=True))

        qs = qs.select_related('created_by').order_by('-created_when')

        return qs

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.DataDetailSerializer
        else:
            return serializers.DataSerializer

    def create(self, request, *args, **kwargs):
        # Check User quota
        storage_used = float(request.user.get_used_storage_space())
        quota = float(request.user.quota)
        quota = gb_to_bytes(quota)
        file_size = float(request.data['file_size'])
        if storage_used + file_size > quota:
            available_space = pretty_bytes(quota - storage_used)
            file_size = pretty_bytes(file_size)
            message = f'Insufficient space. Your available space is {available_space}. The file size is {file_size}. Please free up some space and try again. You can manage your files in the Resources page.'
            return Response({'data_file': [message]}, status=status.HTTP_400_BAD_REQUEST)

        # All good, let's proceed
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_dataset = serializer.save()  # request_sassy_file_name is temporarily set via this serializer
        headers = self.get_success_headers(serializer.data)

        # Make an empty placeholder so we can sign a URL allowing us to upload to it
        sassy_file_name = os.path.basename(new_dataset.request_sassy_file_name)
        # encode here helps GCS do the upload, complains
        # ```TypeError: ('`data` must be bytes, received', <class 'str'>)``` otherwise

        new_dataset.data_file.save(sassy_file_name, ContentFile(''.encode()))
        context = {
            "key": new_dataset.key,
            "sassy_url": make_url_sassy(new_dataset.data_file.name, 'w'),
        }
        return Response(context, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        # TODO: Confirm this has a test
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
        qs = Data.objects.filter(id__in=request.data)
        errors = {}

        for dataset in qs:
            error = self.check_delete_permissions(request, dataset)
            if error:
                errors[dataset.name] = error

        if not errors:
            qs.delete()

        return Response(
            errors if errors else {'detail': 'Datasets deleted successfully'},
            status=status.HTTP_400_BAD_REQUEST if errors else status.HTTP_200_OK
        )

    # This function allows for multiple errors when deleting multiple objects
    def check_delete_permissions(self, request, dataset):
        if request.user != dataset.created_by:
            return 'Cannot delete a dataset that is not yours'

        if dataset.in_use.exists():
            return 'Cannot delete dataset: dataset is in use'

        if dataset.submission.first():
            sub = dataset.submission.first()
            if sub.phase:
                return 'Cannot delete submission: submission belongs to an existing competition. Please visit the competition and delete your submission from there.'


class DataGroupViewSet(ModelViewSet):
    queryset = DataGroup.objects.all()
    serializer_class = serializers.DataGroupSerializer
    # TODO: Anyone can delete these?


@api_view(['PUT'])
def upload_completed(request, key):
    # TODO: This view is weird. We have competitions, submissions, etc. that may not need to call this?
    #  We might need special behavior/metadata for "submission finalization" for example.
    #  Competitions are a unique use case where they hold all of the metadata in the bundle itself

    try:
        dataset = Data.objects.get(created_by=request.user, key=key)
    except Data.DoesNotExist:
        raise Http404()

    dataset.upload_completed_successfully = True
    dataset.save()

    if dataset.type == Data.COMPETITION_BUNDLE:
        # Doing a local import here to avoid circular imports
        from competitions.tasks import unpack_competition

        status = CompetitionCreationTaskStatus.objects.create(
            created_by=request.user,
            dataset=dataset,
            status=CompetitionCreationTaskStatus.STARTING,
        )
        unpack_competition.apply_async((status.pk,))
        return Response({"status_id": status.pk})

    return Response({"key": dataset.key})
