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
from rest_framework.permissions import AllowAny

from api.pagination import BasicPagination, LargePagination
from api.serializers import datasets as serializers
from datasets.models import Data
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
                qs = qs.filter(type__in=[
                    Data.INPUT_DATA,
                    Data.PUBLIC_DATA,
                    Data.REFERENCE_DATA,
                    Data.INGESTION_PROGRAM,
                    Data.SCORING_PROGRAM,
                    Data.STARTING_KIT,
                    Data.SOLUTION
                ])

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
        if self.action == 'public':
            return serializers.DatasetSerializer
        elif self.request.method == 'GET':
            return serializers.DataDetailSerializer
        else:
            return serializers.DataSerializer

    def get_permissions(self):
        if self.action == 'public':
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        # Check required field
        if not request.data.get("file_size"):
            return Response({"file_size": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        # Check file_size is float
        try:
            file_size = float(request.data.get('file_size', 0))
        except (TypeError, ValueError):
            return Response(
                {"file_size": ["A valid number is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check User quota
        storage_used = float(request.user.get_used_storage_space())
        quota = float(request.user.quota)
        quota = gb_to_bytes(quota)
        if storage_used + file_size > quota:
            available_space = quota - storage_used
            available_space = pretty_bytes(available_space, return_0_for_invalid=True)
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
        dataset = self.get_object()
        error = self.check_delete_permissions(request, dataset)
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

    @action(detail=False, methods=('GET',), pagination_class=LargePagination)
    def public(self, request):
        """
        Retrieve a public list of datasets with optional filtering and ordering.

        This endpoint returns a paginated list of datasets that are public.
        It supports several optional query parameters for filtering and sorting the results.

        Query Parameters:
        -----------------
        - search (str, optional): A search term to filter competitions by their title.
        - ordering (str, optional): Specifies the order of the results. Supported values:
            * "recently_added" - Most recently created datasets.
            * "most_downloaded" - Datasets with the most downloads.
            Defaults to "recently_added" if not provided or invalid.
        - has_license (bool, optional): If "true", filters datasets that has license.
        - is_verified (bool, optional): If "true", filters datasets that are verified.

        Returns:
        --------
        - 200 OK: A paginated or full list of serialized datasets matching the filter criteria. The response is serialized using `DatasetSerializer`.
        """

        # Receive filters from request query params
        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering")
        has_license = request.query_params.get("has_license", "false").lower() == "true"
        is_verified = request.query_params.get("is_verified", "false").lower() == "true"

        qs = Data.objects.filter(
            is_public=True,
            type=Data.PUBLIC_DATA
        )

        # Filter by title and description (search)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Filter by has_license
        if has_license:
            qs = qs.filter(license__isnull=False)

        # Filter by is_verified
        if is_verified:
            qs = qs.filter(is_verified=True)

        # Apply ordering
        if ordering == "recently_added":
            qs = qs.order_by("-id")  # most recently created
        elif ordering == "most_downloaded":
            qs = qs.order_by("-downloads")  # descending by download count
        else:
            qs = qs.order_by("-id")  # default fallback

        queryset = self.filter_queryset(qs)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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
