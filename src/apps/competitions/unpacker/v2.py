import base64
import os
import json
import datetime

from django.utils import timezone
from django.core.files import File

from competitions.models import Phase
from competitions.unpacker.exceptions import CompetitionUnpackingException
from competitions.unpacker.utils import _get_datetime, _zip_if_directory, get_data_key
from datasets.models import Data
from tasks.models import Solution, Task


class V2Unpacker:
    def __init__(self, competition_yaml, temp_directory, creator, version):
        self.competition_yaml = competition_yaml
        self.temp_directory = temp_directory
        self.version = version
        self.competition = None
        self.tasks = []
        self.datasets = []
        self.solutions = []
        self.creator = creator

    def unpack(self):
        # ---------------------------------------------------------------------
        # Initialize the competition dict
        self.competition = {
            "title": self.competition_yaml.get('title'),
            # NOTE! We use 'logo' instead of 'image' here....
            "logo": None,
            "registration_auto_approve": self.competition_yaml.get('registration_auto_approve', False),
            "docker_image": self.competition_yaml.get('docker_image', 'codalab/codalab-legacy:py3'),
            "pages": [],
            "phases": [],
            "leaderboards": [],
            # Holding place for phases to reference. Ignored by competition serializer.
            "tasks": {},
            "solutions": {},
        }

        self._unpack_pages()
        self._unpack_tasks()
        self._unpack_solutions()
        self._unpack_terms()
        self._unpack_image()
        self._unpack_phases()
        self._unpack_leaderboards()

        return {
            'competition': self.competition,
            'tasks': self.tasks,
            'solutions': self.solutions,
        }

    def _unpack_pages(self):
        # ---------------------------------------------------------------------
        # Pages
        for index, page in enumerate(self.competition_yaml.get('pages')):
            try:
                page_content = open(os.path.join(self.temp_directory, page["file"])).read()

                if not page_content:
                    raise CompetitionUnpackingException(f"Page '{page['file']}' is empty, it must contain content.")

                self.competition['pages'].append({
                    "title": page.get("title"),
                    "content": page_content,
                    "index": index
                })
            except FileNotFoundError:
                raise CompetitionUnpackingException(f"Unable to find page: {page['file']}")

    def _unpack_tasks(self):
        # ---------------------------------------------------------------------
        # Tasks
        tasks = self.competition_yaml.get('tasks')
        if tasks:
            for task in tasks:
                if 'index' not in task:
                    raise CompetitionUnpackingException(
                        f'ERROR: No index for task: {task["name"] if "name" in task else task["key"]}')

                index = task['index']

                if index in self.competition['tasks']:
                    raise CompetitionUnpackingException(f'ERROR: Duplicate task indexes. Index: {index}')

                if 'key' in task:
                    # just add the {index: key} to competition tasks
                    self.competition['tasks'][index] = task['key']
                else:
                    # must create task object so we can add {index: key} to competition tasks
                    new_task = {
                        'name': task.get('name'),
                        'description': task.get('description'),
                        'created_by': self.creator.id,
                        'ingestion_only_during_scoring': task.get('ingestion_only_during_scoring', False),
                        'index': index
                    }
                    for file_type in ['ingestion_program', 'input_data', 'scoring_program', 'reference_data']:
                        new_task[file_type] = {
                            'obj': task,
                            'file_type': file_type,
                            'temp_directory': self.temp_directory,
                            'creator': self.creator,
                            'index': index
                        }

                    # serializer = TaskSerializer(
                    #     data=new_task,
                    # )
                    # serializer.is_valid(raise_exception=True)
                    # new_task = serializer.save()
                    # self.competition["tasks"][index] = new_task.key
                    self.tasks.append(new_task)

    def _unpack_solutions(self):
        # ---------------------------------------------------------------------
        # Solutions
        solutions = self.competition_yaml.get('solutions')
        if solutions:
            for solution in solutions:
                if 'index' not in solution:
                    raise CompetitionUnpackingException(
                        f"ERROR: No index for solution: {solution['name'] if 'name' in solution else solution['key']}")

                index = solution['index']
                # task_keys = [self.competition['tasks'][task_index] for task_index in solution.get('tasks')]
                task_keys = [self.tasks[task_index] for task_index in solution.get('tasks')]

                if not task_keys:
                    raise CompetitionUnpackingException(
                        f"ERROR: Solution: {solution['key']} missing task index pointers")

                if index in self.competition['solutions']:
                    raise CompetitionUnpackingException(f"ERROR: Duplicate indexes. Index: {index}")

                if 'key' in solution:
                    # add {index: {'key': key, 'tasks': task_index}} to competition solutions
                    solution = Solution.objects.filter(key=solution['key']).first()
                    if not solution:
                        raise CompetitionUnpackingException(f'Could not find solution with key: "{solution["key"]}"')
                    solution.tasks.add(*Task.objects.filter(key__in=task_keys))

                    self.competition['solutions'][index] = solution['key']

                else:
                    # create solution object and then add {index: {'key': key, 'tasks': task_indexes}} to competition solutions
                    name = solution.get('name') or f"solution @ {timezone.now():%m-%d-%Y %H:%M}"
                    description = solution.get('description')
                    file_name = solution['path']
                    file_path = os.path.join(self.temp_directory, file_name)
                    # file_path = os.path.join(self.temp_directory, file_name)
                    if os.path.exists(file_path):
                        new_solution_data = Data(
                            created_by=self.creator,
                            type='solution',
                            name=name,
                            was_created_by_competition=True,
                        )
                        file_path = _zip_if_directory(file_path)
                        new_solution_data.data_file.save(os.path.basename(file_path), File(open(file_path, 'rb')))
                        new_solution = {
                            'data': new_solution_data.key,
                            'tasks': task_keys,
                            'name': name,
                            'description': description,
                            'index': index,
                        }
                        self.solutions.append(new_solution)
                        # serializer = SolutionSerializer(data=new_solution)
                        # serializer.is_valid(raise_exception=True)
                        # new_solution = serializer.save()
                        # self.competition['solutions'][index] = new_solution.key
                    else:
                        pass
                        # TODO: add processing for using a key to data for a solution?
                        # new_task[file_type] = new_dataset.key

    def _unpack_terms(self):
        # ---------------------------------------------------------------------
        # Terms
        terms_path = self.competition_yaml.get('terms')
        if not terms_path:
            raise CompetitionUnpackingException('A file containing the terms of this competition has not been '
                                                'supplied in the required location')
        try:
            terms_content = open(os.path.join(self.temp_directory, terms_path)).read()

            if not terms_content:
                raise CompetitionUnpackingException(f"{terms_path} is empty, it must contain content.")

            self.competition['terms'] = terms_content
        except FileNotFoundError:
            raise CompetitionUnpackingException(f"Unable to find page: {terms_path}")


    def _unpack_image(self):
        # ---------------------------------------------------------------------
        # Logo
        # Turn image into base64 version for easy uploading
        # (Can maybe split this into a separate function)
        image_path = os.path.join(self.temp_directory, self.competition_yaml.get('image'))

        if not os.path.exists(image_path):
            raise CompetitionUnpackingException(f"Unable to find image: {competition_yaml.get('image')}")

        with open(image_path, "rb") as image:
            self.competition['logo'] = json.dumps({
                "file_name": os.path.basename(self.competition_yaml.get('image')),
                # Converts to b64 then to string
                "data": base64.b64encode(image.read()).decode()
            })

    def _unpack_phases(self):
        # ---------------------------------------------------------------------
        # Phases

        for index, phase_data in enumerate(sorted(self.competition_yaml.get('phases'), key=lambda x: x.get('index') or 0)):
            # This normalizes indexes to be 0 indexed but respects the ordering of phase indexes from the yaml if present
            new_phase = {
                "index": index,
                "name": phase_data.get('name'),
                "description": phase_data.get('description'),
                "start": _get_datetime(phase_data.get('start')),
                "end": _get_datetime(phase_data.get('end')),
                'max_submissions_per_day': phase_data.get('max_submissions_per_day'),
                'max_submissions_per_person': phase_data.get('max_submissions'),
                'auto_migrate_to_this_phase': phase_data.get('auto_migrate_to_this_phase', False),
            }
            execution_time_limit = phase_data.get('execution_time_limit_ms')
            if execution_time_limit:
                new_phase['execution_time_limit'] = execution_time_limit

            if new_phase['max_submissions_per_day'] or 'max_submissions' in phase_data:
                new_phase['has_max_submissions'] = True

            tasks = phase_data.get('tasks')
            if not tasks:
                raise CompetitionUnpackingException(f'Phases must contain at least one task to be valid')

            # new_phase['tasks'] = [self.competition['tasks'][index] for index in tasks]
            new_phase['tasks'] = [self.tasks[index] for index in tasks]

            self.competition['phases'].append(new_phase)
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

        # TODO: Ensure I didn't break phase start/end validation with this
        current_phase = list(filter(
            lambda p: p['start'] if p.get('start') else datetime.datetime < now() < p['end'] if p.get(
                'end') else datetime.datetime, self.competition['phases']
        ))
        if current_phase:
            current_index = current_phase[0]['index']
            previous_index = current_index - 1 if current_index >= 1 else None
            next_index = current_index + 1 if current_index < len(self.competition['phases']) - 1 else None
        else:
            current_index = None
            next_phase = list(filter(lambda p: p['start'] > timezone.now() < p['end'], self.competition['phases']))
            if next_phase:
                next_index = next_phase[0]['index']
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

    def _unpack_leaderboards(self):
        # ---------------------------------------------------------------------
        # Leaderboards
        for leaderboard in self.competition_yaml.get('leaderboards'):
            self.competition['leaderboards'].append(leaderboard)
