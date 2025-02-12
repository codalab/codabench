import io
import yaml
import zipfile
from django.core.files.uploadedfile import InMemoryUploadedFile
from collections import defaultdict
from django.db.models import Q, OuterRef, Subquery
from django.db import transaction
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
from datasets.models import Data
from utils.data import pretty_bytes, gb_to_bytes


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
            # when there is `public` in the query params, it means user has checked on the front-end
            # the Show public tasks checkbox.
            # When a user clicks that public task that may not belong to the user, we want to show
            # the public task to the user and hence we check the `retrieve` action
            if self.request.query_params.get('public') or self.action == 'retrieve':
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
        task_detail_serializer = serializers.TaskSerializer(task)

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

    @action(detail=False, methods=('POST',))
    def upload_task(self, request):

        """
        This function is used to upload a task. To upload a task, a zip file is created from the components of the task:
            - task.yaml (required)
            - ingestion_program.zip (optional)
            - scoring_program.zip (optional)
            - input_data.zip (optional)
            - reference_data.zip (optional)

        task.yaml has the following structure:
            name: Task Name
            description: Task Description
            is_public: true/false
            input_data:
                key: Your dataset key
            reference_data:
                key: Your dataset key
            scoring_program:
                zip: scoring_program.zip
            ingestion_program:
                zip: ingestion_program.zip

            Note:
             - You can upload a task.yaml file without any other files if you want to create a task from existing datasets/programs using keys
             - You can use a mix of key and zip to upload a task e.g. to use already uploaded input data and reference data but upload new ingestion and scoring programs
             - You can choose to upload all the datasets and programs without using the key

        """

        # Access uploaded file
        uploaded_file = request.FILES.get('file')

        # -----------
        # Check File
        # -----------

        # Check if a file is provided
        if not uploaded_file:
            return Response({"error": "No attached file found, please try again!"}, status=status.HTTP_400_BAD_REQUEST)

        # ------------
        # Check Quota
        # ------------

        # Check if user has enough quota to proceed
        storage_used = float(request.user.get_used_storage_space())
        # User quota is in GB
        quota = float(request.user.quota)
        # Convert user quota to bytes
        quota = gb_to_bytes(quota)
        file_size = uploaded_file.size
        if storage_used + file_size > quota:
            file_size = pretty_bytes(file_size)
            return Response({'error': "Insufficient space! Please free up some space and try again. You can manage your files in the Resources page."}, status=status.HTTP_507_INSUFFICIENT_STORAGE)

        # ----------------------
        # Process Task zip file
        # ----------------------
        try:
            # Process the zip file
            with zipfile.ZipFile(uploaded_file, 'r') as zip_file:

                # ------------------
                # Process yaml file
                # ------------------

                # Check if 'task.yaml' exists
                if 'task.yaml' not in zip_file.namelist():
                    return Response({"error": "task.yaml not found in the zip file"}, status=status.HTTP_400_BAD_REQUEST)

                # Read the task.yaml file
                with zip_file.open('task.yaml') as task_file:
                    try:
                        task_data = yaml.safe_load(task_file)
                    except yaml.YAMLError as e:
                        return Response({"error": f"Error parsing task.yaml: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                    # ------------------
                    # Yaml file checks
                    # ------------------

                    # Check if task has a name
                    if "name" not in task_data:
                        return Response({"error": f"Missing: name, task must have a name"}, status=status.HTTP_400_BAD_REQUEST)

                    # Check if task has a description
                    if "description" not in task_data:
                        return Response({"error": f"Missing: description, task must have a description"}, status=status.HTTP_400_BAD_REQUEST)

                    # Check if task has a scoring program
                    if Data.SCORING_PROGRAM not in task_data:
                        return Response({"error": f"Missing: scoring_program, task must have a scoring_program"}, status=status.HTTP_400_BAD_REQUEST)

                    # ------------------------------
                    # Process datasets and programs
                    # ------------------------------

                    # Begin atomic transaction to ensure rollback if any error occurs
                    with transaction.atomic():
                        # Initialize task fields
                        task_kwargs = {
                            'name': task_data.get('name'),
                            'description': task_data.get('description'),
                            'created_by': request.user,
                            'is_public': task_data.get('is_public', False),
                            'ingestion_only_during_scoring': task_data.get('ingestion_only_during_scoring', False),
                        }

                        # Function to create or get dataset from either zip or key
                        # If both key and zip are present, key is used and zip is ignored
                        def create_or_get_data(data_type, data_info):
                            # Process dataset/program if data_info is not empty i.e. provided in the yaml file
                            if data_info:
                                key = data_info.get('key', None)
                                zip_name = data_info.get('zip', None)

                                if key:
                                    # Retrieve dataset by key if provided
                                    try:
                                        return Data.objects.get(key=key, created_by=request.user, type=data_type)
                                    except Data.DoesNotExist:
                                        raise ValueError(f"{data_type} with key '{key}' not found.")
                                elif zip_name:
                                    # Check that the zip file exists in the main zip and create dataset
                                    if zip_name not in zip_file.namelist():
                                        raise ValueError(f"Dataset file '{zip_name}' not found in the uploaded zip file.")
                                    if not zip_name.endswith(".zip"):
                                        raise ValueError(f"Dataset file '{zip_name}' should be a zip file.")
                                    try:
                                        # Createa a new dataset using the zip file for dataset/program
                                        with zip_file.open(zip_name) as data_zip_file:
                                            # Read file content
                                            file_content = data_zip_file.read()

                                            # Get the file size in bytes
                                            file_size = len(file_content)

                                            # Create a BytesIO object for the dataset file
                                            data_file = InMemoryUploadedFile(
                                                file=io.BytesIO(file_content),
                                                field_name='data_file',
                                                name=zip_name,
                                                content_type='application/zip',
                                                size=file_size,
                                                charset=None
                                            )
                                            # Create dataset
                                            dataset = Data.objects.create(
                                                name=zip_name,
                                                created_by=request.user,
                                                data_file=data_file,
                                                type=data_type
                                            )
                                            return dataset
                                    except zipfile.BadZipFile:
                                        raise ValueError(f"{zip_name} is not a valid ZIP file.")
                                    except Exception as e:
                                        raise ValueError(f"Error processing {zip_name}: {str(e)}")

                            # For scoring program key or zip is required because task must have a scoring program
                            if data_type == Data.SCORING_PROGRAM:
                                raise ValueError(f"{data_type} must have either a key or zip")
                            else:
                                return None

                        # Create datasets based on task.yaml contents
                        # Loop over all possible datasets and programs and create or get that dataset.
                        # If a dataset is not provided in the yaml, use None value for it
                        datasets_and_programs = [Data.INGESTION_PROGRAM, Data.SCORING_PROGRAM, Data.INPUT_DATA, Data.REFERENCE_DATA]
                        for dataset in datasets_and_programs:
                            task_kwargs[dataset] = create_or_get_data(data_type=dataset, data_info=task_data.get(dataset, {}))

                        # Create the Task using the task kwrgs created from yaml and datasets/programs
                        task = Task.objects.create(**task_kwargs)

                        # Return a success message
                        return Response({"message": f"Task '{task.name}' created successfully!"}, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # catch all value errors here
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # catch all other unexpected errors here
            return Response({"error": f"An error occurred while creating the task.\n {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # This function allows for multiple errors when deleting multiple objects
    def check_delete_permissions(self, request, task):
        if request.user != task.created_by:
            return "Cannot delete a task that is not yours"
        if task.phases.exists():
            return 'Cannot delete task: task is being used by a phase'
