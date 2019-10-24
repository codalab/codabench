import os
import uuid
from uuid import UUID

from django.core.files import File
from django.utils import timezone

from api.serializers.competitions import CompetitionSerializer
from api.serializers.tasks import TaskSerializer, SolutionSerializer
from datasets.models import Data
from tasks.models import Task, Solution
from .utils import CompetitionUnpackingException, zip_if_directory


class BaseUnpacker:
    def __init__(self):
        self.creator = None
        self.competition = None
        self.created_tasks = []
        self.created_solutions = []
        self.created_datasets = []

    def _get_current_phase(self, phases):
        for phase in phases:
            if phase['start'] < timezone.now():
                try:
                    if phase['end'] > timezone.now():
                        return phase
                except KeyError:
                    # phase is endless, so it is indefinitely current
                    return phase

    def _get_next_phase(self, phases):
        future_phases = filter(lambda p: p['start'] > timezone.now(), phases)
        return min(future_phases, key=lambda p: p['index'], default=None)

    def _get_data_key(self, file_name, file_path, file_type, creator, *args, **kwargs):
        if os.path.exists(file_path):
            new_dataset = Data(
                created_by=creator,
                type=file_type,
                name=f"{file_type} @ {timezone.now():'%m-%d-%Y %H:%M'}",
                was_created_by_competition=True,
            )
            file_path = zip_if_directory(file_path)
            new_dataset.data_file.save(os.path.basename(file_path), File(open(file_path, 'rb')))
            self.created_datasets.append(new_dataset)
            return new_dataset.key
        else:
            try:
                # checking if file name could be a uuid
                uuid.UUID(file_name)
            except ValueError:
                raise CompetitionUnpackingException(f'Cannot find dataset: "{file_name}"')

            if not Data.objects.filter(key=file_name).exists():
                raise CompetitionUnpackingException(f'Cannot find {file_type} with key: "{file_name}"')
            return file_name

    def _save_tasks(self):
        for index, task in self.competition['tasks'].items():
            if isinstance(task, str):
                try:
                    task = Task.objects.get(key=task)
                except Task.DoesNotExist:
                    raise CompetitionUnpackingException(f'Task with key {task} does not exist')
                self.competition['tasks'][index] = task
            else:
                for file_type in ['ingestion_program', 'input_data', 'scoring_program', 'reference_data']:
                    try:
                        task_file_data = task[file_type]
                    except KeyError:
                        # file type not here, moving on
                        continue
                    key = self._get_data_key(**task_file_data)
                    task[file_type] = key
                serializer = TaskSerializer(
                    data=task,
                )
                serializer.is_valid(raise_exception=True)
                new_task = serializer.save()
                self.created_tasks.append(new_task)
                self.competition['tasks'][index] = new_task

    def _save_solutions(self):
        for solution in self.competition['solutions']:
            if 'key' in solution:
                try:
                    s = Solution.objects.get(key=solution['key'])
                except Solution.DoesNotExist:
                    raise CompetitionUnpackingException(f'Could not find solution with key: {solution["key"]}')
                for task_index in solution['tasks']:
                    s.add(self.competition['tasks'][task_index])
            else:
                solution['tasks'] = [self.competition['tasks'][index].key for index in solution['tasks']]
                solution['data'] = self._get_data_key(**solution, file_type='solution')
                serializer = SolutionSerializer(data=solution)
                serializer.is_valid(raise_exception=True)
                new_solution = serializer.save()
                self.created_solutions.append(new_solution)

    def _save_competition(self):
        for phase in self.competition['phases']:
            phase['tasks'] = [self.competition['tasks'][index].key for index in phase['tasks']]
        serializer = CompetitionSerializer(
            data=self.competition,
            context={'created_by': self.creator}
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def _clean(self):
        for dataset in self.created_datasets:
            dataset.delete()
        for task in self.created_tasks:
            task.delete()
        for solution in self.created_solutions:
            solution.delete()

    def save(self):
        try:
            self._save_tasks()
            self._save_solutions()
            return self._save_competition()
        except Exception as e:
            self._clean()
            raise e


class Finalizer:
    def __init__(self, data, creator):
        self.competition = data
        self.creator = creator

    def finalize(self):
        self._create_tasks()
        self._create_solutions()

        serializer = CompetitionSerializer(
            data=self.competition['competition'],
            # We have to pass the creator here this special way, because this is how the API
            # takes the request.user
            context={"created_by": self.creator}
        )
        # try:
        serializer.is_valid(raise_exception=True)
        competition = serializer.save()
        return competition

    def _create_tasks(self):
        for task_data in self.competition['tasks']:
            temp_index = task_data['index']
            for file_type in ['ingestion_program', 'input_data', 'scoring_program', 'reference_data']:
                key = ''
                task_data[file_type] = key
            serializer = TaskSerializer(
                data=task_data,
            )
            serializer.is_valid(raise_exception=True)
            new_task = serializer.save()
            for phase_data in self.competition['competition']['phases']:
                for index, temp_task_data in enumerate(phase_data['tasks']):
                    if not isinstance(temp_task_data, UUID):
                        if temp_task_data['index'] == temp_index:
                            phase_data['tasks'][index] = new_task.key
            for solution_data in self.competition['solutions']:
                for index, temp_task_data in enumerate(solution_data.get('tasks')):
                    if not isinstance(temp_task_data, UUID):
                        if temp_task_data['index'] == temp_index:
                            solution_data['tasks'][index] = new_task.key

    def _create_solutions(self):
        for solution_data in self.competition['solutions']:
            temp_index = solution_data['index']
            serializer = SolutionSerializer(data=solution_data)
            serializer.is_valid(raise_exception=True)
            new_solution = serializer.save()
            for phase_data in self.competition['competition']['phases']:
                for index, temp_solution_data in enumerate(phase_data.get('solutions', [])):
                    if not isinstance(temp_solution_data, UUID):
                        if temp_solution_data['index'] == temp_index:
                            phase_data['solutions'][index] = new_solution.key