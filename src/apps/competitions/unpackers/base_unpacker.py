import base64
import json
import os
import uuid

from django.core.files import File
from django.test import RequestFactory
from django.utils import timezone

from api.serializers.competitions import CompetitionSerializer
from api.serializers.leaderboards import LeaderboardSerializer
from api.serializers.tasks import TaskSerializer, SolutionSerializer
from competitions.models import Phase
from datasets.models import Data
from queues.models import Queue
from tasks.models import Task, Solution
from utils.storage import md5
from .utils import CompetitionUnpackingException, zip_if_directory


class BaseUnpacker:
    def __init__(self, competition_yaml, temp_directory, creator):
        self.competition_yaml = competition_yaml
        self.temp_directory = temp_directory
        self.creator = creator
        self.competition = None
        self.created_tasks = []
        self.created_solutions = []
        self.created_datasets = []

        # We'll make a fake request to pass to DRF serializers for request.user context
        self.fake_request = RequestFactory()
        self.fake_request.user = self.creator

    def _get_data_key(self, file_name, file_path, file_type, creator, *args, **kwargs):
        """Takes in a potential UUID or file path

        :returns (file path/uuid key, file path of temp zip)"""
        if os.path.exists(file_path):
            new_dataset = Data(
                created_by_id=creator,
                type=file_type,
                name=f"{file_type} @ {timezone.now():'%m-%d-%Y %H:%M'}",
                was_created_by_competition=True,
            )
            file_path = zip_if_directory(file_path)
            new_dataset.data_file.save(os.path.basename(file_path), File(open(file_path, 'rb')))
            self.created_datasets.append(new_dataset)
            return new_dataset.key, file_path
        else:
            try:
                # checking if file name could be a uuid
                uuid.UUID(file_name)
            except ValueError:
                raise CompetitionUnpackingException(f'Cannot find dataset: "{file_name}"')

            if not Data.objects.filter(key=file_name).exists():
                raise CompetitionUnpackingException(f'Cannot find {file_type} with key: "{file_name}"')
            return file_name, None

    def _read_image(self, image_name):
        image_path = os.path.join(self.temp_directory, image_name)
        try:
            with open(image_path, "rb") as image:
                return json.dumps({
                    "file_name": image_name,
                    # Converts to b64 then to string
                    "data": base64.b64encode(image.read()).decode()
                })
        except FileNotFoundError:
            raise CompetitionUnpackingException(f"Unable to find image: {self.competition_yaml.get('image')}")

    def _get_current_phase(self, phases):
        for phase in phases:
            if phase['start'] < timezone.now():
                try:
                    if phase['end'] is not None and phase['end'] > timezone.now():
                        return phase
                    elif phase['end'] is None:
                        # phase is endless, so it is indefinitely current
                        return phase
                except KeyError:
                    # no phase['end'] so it is endless
                    return phase

    def _get_next_phase(self, phases):
        future_phases = filter(lambda p: p['start'] > timezone.now(), phases)
        return min(future_phases, key=lambda p: p['index'], default=None)

    def _set_phase_statuses(self):
        self.competition['phases'][-1]['is_final_phase'] = True

        current_phase = self._get_current_phase(self.competition['phases'])
        if current_phase:
            current_index = current_phase['index']
            previous_index = current_index - 1 if current_index >= 1 else None
            next_index = current_index + 1 if current_index < len(self.competition['phases']) - 1 else None
        else:
            current_index = None
            next_phase = self._get_next_phase(self.competition['phases'])
            if next_phase:
                next_index = next_phase['index']
                previous_index = next_index - 1 if next_index >= 1 else None
            else:
                next_index = None
                previous_index = None

        if current_index is not None:
            self.competition['phases'][current_index]['status'] = Phase.CURRENT
        if next_index is not None:
            self.competition['phases'][next_index]['status'] = Phase.NEXT
        if previous_index is not None:
            self.competition['phases'][previous_index]['status'] = Phase.PREVIOUS

    def _validate_phase_ordering(self):
        for i in range(len(self.competition['phases'])):
            if i == 0:
                continue
            phase1 = self.competition['phases'][i - 1]
            phase2 = self.competition['phases'][i]
            if phase1['end'] is None:
                raise CompetitionUnpackingException(
                    f'Phase: {phase1.get("name", phase1["index"])} must have an end time because it has a phase after it.'
                )
            elif phase2['start'] < phase1['end']:
                raise CompetitionUnpackingException(
                    f'Phases must be sequential. Phase: {phase2.get("name", phase2["index"])}'
                    f'starts before Phase: {phase1.get("name", phase1["index"])} has ended'
                )
            elif phase1['end'] == phase2['start']:
                # Current phase start date and previous phase end dates are same, raise error
                raise CompetitionUnpackingException(
                    f'Phases dates conflict. Phase: {phase2.get("name", phase2["index"])} '
                    f'should start after Phase: {phase1.get("name", phase1["index"])} has ended'
                )

    def _unpack_pages(self):
        """
        Modify self.competition['page'] by appending pages to the list, with data shaped as follows
        {
            "title": page_title,
            "content": page_content (read from the file),
            "index": page_index (so we know what order to display the pages on the competition detail page),
        }
        """
        raise NotImplementedError

    def _unpack_tasks(self):
        """
        Modify self.competition['tasks'] dictionary. The key should be the tasks index (to be consumed by phases
        the data should be as follows:

        index: {
            'name': task_name,
            'description': task_description,
            'created_by': creator.id,
            'ingestion_only_during_scoring': bool,
            # All the relevant data files:
            'scoring_program': {
                'file_name': file_name,
                'file_path': file_path (including temp_dir),
                'file_type': 'scoring_program',
                'creator': creator,
            }
            'ingestion_program': {} # etc
        }
        Alternatively, a UUID key may be specified, in which case the data may be:

        index: key
        """
        raise NotImplementedError

    def _unpack_solutions(self):
        """
        Append solution data to self.competition['solutions']
        {
            'file_name': file_name,
            'file_path': file_path,
            'name': solution_name,
            'description': solution_description,
            'creator': creator,
            'tasks': []
        }
        A key may also be specified, to tie an existing solution to a new task
        {
            'key': key,
            'tasks': []
        }
        in both cases, tasks should be a list of indexes (should equate to keys in the tasks dict created above)
        """
        raise NotImplementedError

    def _unpack_terms(self):
        """
        Read the content of the terms and conditions and assign them to self.competition['terms']
        If unpack pages creates terms, this can be ignored
        """
        raise NotImplementedError

    def _unpack_image(self):
        try:
            image_name = self.competition_yaml['image']
        except KeyError:
            raise CompetitionUnpackingException('An image for this competition could not be found in the yaml')

        self.competition['logo'] = self._read_image(image_name)

    def _unpack_queue(self):
        # Get Queue by vhost/uuid. If instance not returned, or we don't have access don't set it!
        vhost = self.competition_yaml.get('queue')
        if vhost:
            try:
                queue = Queue.objects.get(vhost=vhost)
                if not queue.is_public:
                    all_queue_organizer_names = queue.organizers.all().values_list('username', flat=True)
                    if queue.owner != self.creator and self.creator.username not in all_queue_organizer_names:
                        raise CompetitionUnpackingException("You do not have access to the specified queue!")
                self.competition['queue'] = {
                    'name': queue.name,
                    'vhost': queue.vhost,
                    'is_public': queue.is_public,
                    'owner': queue.owner,
                    'organizers': queue.organizers,
                    'broker_url': queue.broker_url,
                    'created_when': queue.broker_url,
                    'id': queue.id,
                }
            except Queue.DoesNotExist:
                raise CompetitionUnpackingException("The specified Queue does not exist!")

    def _unpack_phases(self):
        """
        Append to self.competition['phases']:
        {
            "index": index,
            "name": phase_name,
            "description": phase_description,
            "start": phase_start (datetime.datetime),
            "end": phase_end (datetime.datetime),
            # BB public_data and starting_kit
            # ... See serializer for complete fields list
            "tasks": [list of indices that should match self.competition['tasks']]
        }
        Should call self._validate_phase_ordering() and self._set_phase_statuses()
        """
        raise NotImplementedError

    def _unpack_leaderboards(self):
        """
        {
            'id',
            'primary_index',
            'title',
            'key',
            'columns' : {
                'id',
                'computation',
                'computation_indexes',
                'title',
                'key',
                'sorting',
                'index',
            },
        }
        """
        raise NotImplementedError

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
                    key, temp_data_path = self._get_data_key(**task_file_data)
                    task[file_type] = key
                # because created_by is a read only field, we need to grab it from the context and can't pass it in data
                serializer = TaskSerializer(data=task, context={'request': self.fake_request})
                serializer.is_valid(raise_exception=True)
                new_task = serializer.save()
                self.created_tasks.append(new_task)
                self.competition['tasks'][index] = new_task

    def _save_solutions(self):
        for solution in self.competition['solutions']:
            if 'key' in solution:
                try:
                    s = Solution.objects.get(key=solution['key'])
                    solution_tasks = s.tasks.all().values_list('pk', flat=True)
                except Solution.DoesNotExist:
                    raise CompetitionUnpackingException(f'Could not find solution with key: {solution["key"]}')
                for task_index in solution['tasks']:
                    task = self.competition['tasks'][task_index]
                    if task.id not in solution_tasks:
                        s.tasks.add(task)
            else:
                solution['tasks'] = [self.competition['tasks'][index].key for index in solution['tasks']]
                solution['data'], temp_data_path = self._get_data_key(**solution, file_type='solution')
                if temp_data_path:
                    solution['md5'] = md5(temp_data_path)
                # because created_by is a read only field, we need to grab it from the context and can't pass it in data
                serializer = SolutionSerializer(data=solution, context={'request': self.fake_request})
                serializer.is_valid(raise_exception=True)
                new_solution = serializer.save()
                self.created_solutions.append(new_solution)

    def _save_leaderboards(self):
        for index, leaderboard in enumerate(self.competition['leaderboards']):
            serializer = LeaderboardSerializer(data=leaderboard, context={'request': self.fake_request})
            serializer.is_valid(raise_exception=True)
            self.competition['leaderboards'][index] = serializer.save()

    def _save_competition(self):
        for phase in self.competition['phases']:
            phase['tasks'] = [self.competition['tasks'][index].key for index in phase['tasks']]
            phase['leaderboard'] = self.competition['leaderboards'][0].id
            phase_public_data_file_data = phase['public_data']
            phase_starting_kit_file_data = phase['starting_kit']
            if phase_public_data_file_data is not None:
                public_data_key, public_data_temp_data_path = self._get_data_key(**phase_public_data_file_data)
                phase['public_data'] = Data.objects.filter(key=public_data_key)[0].id
            if phase_starting_kit_file_data is not None:
                starting_kit_key, starting_kit_temp_data_path = self._get_data_key(**phase_starting_kit_file_data)
                phase['starting_kit'] = Data.objects.filter(key=starting_kit_key)[0].id

        self.competition.pop('leaderboards')

        serializer = CompetitionSerializer(
            data=self.competition,
            context={'request': self.fake_request}
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
            self._save_leaderboards()
            return self._save_competition()
        except Exception as e:
            self._clean()
            raise e
