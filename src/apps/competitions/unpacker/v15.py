import base64
import os
import json
import datetime

import logging
from django.utils import timezone

from django.core.files import File

from rest_framework.exceptions import ValidationError

from competitions.unpacker.exceptions import CompetitionUnpackingException, CompetitionConversionException

from competitions.unpacker.utils import _get_datetime, _zip_if_directory, get_data_key

from datasets.models import Data

from tasks.models import Solution, Task

from competitions.models import Phase

from api.serializers.competitions import CompetitionSerializer

logger = logging.getLogger()


class V15Unpacker:
    LEGACY_DEPRECATED_KEYS = [
        'force_submission_to_leaderboard',
        'disallow_leaderboard_modifying',
        'has_registration',
        'enable_detailed_results',
        'enable_forum',
        'admin_names',
        'end_date',
    ]

    LEGACY_COMPETITION_KEY_MAPPING = {
        'competition_docker_image': 'docker_image',
    }

    LEGACY_PHASE_KEY_MAPPING = {
        'label': 'name',
        'description': 'description',
        'start_date': 'start',
    }

    PHASE_TASK_COMMON_MAPPING = {
        'label': 'name',
        'input_data': 'input_data',
        'scoring_program': 'scoring_program',
        'reference_data': 'reference_data',
        'ingestion_program': 'ingestion_program',
        'ingestion_program_only_during_scoring': 'ingestion_only_during_scoring',
        # 'public_data': 'public_data',
        # 'starting_kit': 'starting_kit',
    }

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

        print("DATA IS: {}".format(self.competition_yaml))

        self.convert()

        print("DATA IS NOW: {}".format(self.competition_yaml))

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
        # self._convert_pages()

        print("Our fucking yaml is: {}".format(self.competition_yaml))

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

        print("Tasks is: {}".format(tasks))

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
                        print("MAKING SOMETHING HOORAY")

                    # serializer = TaskSerializer(
                    #     data=new_task,
                    # )
                    # serializer.is_valid(raise_exception=True)
                    # new_task = serializer.save()
                    # self.competition["tasks"][index] = new_task.key
                    self.tasks.append(new_task)
                    print("TASKS IS NOW: {}".format(self.tasks))

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
                print(type(index))
                print(solution.get('tasks'))
                print(self.competition.get('tasks'))
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

            print("WHAT IS SELF.TASKS CURRENTLY?: {}".format(self.tasks))
            print("WHAT IS TASKS CURRENTLY?: {}".format(tasks))
            print("WHAT IS INDEX CURRENTLY?: {}".format(index))
            print("WHAT IS LENGTH OF TASKS CURRENTLY?: {}".format(len(tasks)))
            print("WHAT IS LENGTH OF SELF.TASKS CURRENTLY?: {}".format(len(self.tasks)))

            # TODO: FIGURE THIS SUN BITCH OUT
            new_phase['tasks'] = [self.tasks[index-1] for index in tasks]

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

    def __get_next_parent_phase(self, current_index):
        # Loop through all of our phase objects, and find the first one which is greater than our current phase and is a parallel parent.
        for phase_index, phase_data in self.competition_yaml['phases'].items():
            if phase_data.get('is_parallel_parent') and phase_index > current_index:
                return phase_index
        return None

    def __get_parent_phase(self, parent_phase_index, new_temp_phase_list):
        # Loop through index, phase_data and find whichever one has the matching index. We delete the extra key later.
        for index, phase_data in enumerate(new_temp_phase_list):
            if int(phase_data.get('index')) == int(parent_phase_index):
                return index
        return None

    def __get_next_index(self, current_index, key_type, has_parent_phases=False):
        # Handle regular sequential phases
        if not has_parent_phases:
            if key_type == int:
                return current_index + 1
            else:
                return str(int(current_index) + 1)
        # Handle parent/sub/child phases
        elif has_parent_phases:
            next_parent_phase_index = self.__get_next_parent_phase(current_index)
            if next_parent_phase_index:
                return next_parent_phase_index
        return None

    def __get_phase_end(self, current_index, next_index):
        if self.competition_yaml['phases'].get(next_index):
            logger.info('Converter: There is a next phase')
            if self.competition_yaml['phases'][next_index].get('start_date'):
                logger.info('Converter: There is a next phase with a start date')
                # We have a phase after this one with a start date
                return self.competition_yaml['phases'][next_index]['start_date']
        return None

    def convert(self, plain=False):
        if not self._is_legacy_bundle():
            logger.info("Bundle data does not appear to be legacy. Skipping.")
            return self.competition_yaml
        else:
            if not self.competition_yaml.get('competition_docker_image') or not self.competition_yaml.get('docker_image'):
                logger.info("Competition is legacy and missing docker image. Setting to ckcollab/codalab-legacy:latest")
                self.competition_yaml['docker_image'] = 'ckcollab/codalab-legacy:latest'
        self._convert_pages()
        self._convert_phases()
        self._convert_leaderboard()
        self._convert_misc_keys()
        if plain:
            self.data = json.loads(json.dumps(self.data, default=str))
        # logger.info("Retrning data: {}".format(self.data))
        # return self.data

    def _is_legacy_bundle(self):
        return any([bool(key in self.competition_yaml) for key in self.LEGACY_DEPRECATED_KEYS])

    def _convert_pages(self):
        new_html_data = []
        self._key_sanity_check('html')
        logger.info("Converting HTML to pages")
        for page_key, page_file in self.competition_yaml['html'].items():
            if page_key == 'terms':
                self.competition_yaml['terms'] = page_file
            new_html_data.append({
                'title': page_key,
                'file': page_file
            })
        del self.competition_yaml['html']
        self.competition_yaml['pages'] = new_html_data


    def _convert_phases(self):
        new_phase_list = []
        new_task_list = []
        new_solution_list = []

        self._key_sanity_check('phases')
        logger.info("Converting phase format")

        has_parent_phases = any('is_parallel_parent' in phase_data for phase_index, phase_data in self.competition_yaml['phases'].items())

        logger.info("Converter: Has parent phases: {}".format(has_parent_phases))

        for phase_index, phase_data in self.competition_yaml['phases'].items():
            new_phase_data = {}
            new_task_data = {}

            legacy_index_type = type(phase_index)
            new_task_data['index'] = int(phase_index)

            # Automatic mapping
            for phase_data_key, phase_data_value in phase_data.items():
                if phase_data_key in self.LEGACY_PHASE_KEY_MAPPING:
                    new_phase_data[self.LEGACY_PHASE_KEY_MAPPING[phase_data_key]] = phase_data_value
                if phase_data_key in self.PHASE_TASK_COMMON_MAPPING:
                    new_task_data[self.PHASE_TASK_COMMON_MAPPING[phase_data_key]] = phase_data_value

            # If we're not a child phase, get our next date and set it
            if not self.competition_yaml['phases'][phase_index].get('parent_phasenumber'):
                next_index = self.__get_next_index(
                    current_index=phase_index,
                    key_type=legacy_index_type,
                    has_parent_phases=has_parent_phases
                )
                next_end_date = self.__get_phase_end(phase_index, next_index)
                if next_end_date:
                    logger.info("Setting end date as {end_date} on phase {phase_index}".format(
                        end_date=next_end_date,
                        phase_index=phase_index)
                    )
                    new_phase_data['end'] = next_end_date

            new_task_list.append(new_task_data)
            if phase_data.get('starting_kit'):
                logger.info("Adding starting kit as solution to task: {}".format(phase_index))
                new_solution_data = {
                    'index': int(phase_index),
                    'tasks': [int(phase_index)],
                    'path': phase_data.get('starting_kit')
                }
                new_phase_data['solutions'] = [int(phase_index)]
                new_solution_list.append(new_solution_data)

            # Handle new task + solution
            if has_parent_phases and phase_data.get('parent_phasenumber'):
                parent_phase_index = self.__get_parent_phase(phase_data['parent_phasenumber'], new_phase_list)
                logger.info("This phase has a parent phase that should be at index {}".format(phase_data['parent_phasenumber']))
                if parent_phase_index != None:
                    logger.info("Adding task entry to phase")
                    if not new_phase_list[parent_phase_index].get('tasks'):
                        new_phase_list[parent_phase_index]['tasks'] = []
                    new_phase_list[parent_phase_index]['tasks'].append(int(phase_index))
            elif has_parent_phases and phase_data.get('is_parallel_parent'):
                new_phase_data['index'] = phase_index
                logger.info("This is a parent phase; Adding it's index to help track: {}".format(phase_index))
                new_phase_list.append(new_phase_data)
            else:
                logger.info("Regularly doing phase data, and task data")
                new_phase_data['tasks'] = [int(phase_index)]
                # Append our new phase data
                new_phase_list.append(new_phase_data)
        del self.competition_yaml['phases']
        # Cleanup residual keys we're not using
        for phase_data in new_phase_list:
            if phase_data.get('index'):
                del phase_data['index']
        self.competition_yaml['phases'] = new_phase_list
        self.competition_yaml['tasks'] = new_task_list
        self.competition_yaml['solutions'] = new_solution_list

    def _convert_leaderboard(self):
        new_leaderboard_list = []
        logger.info("Converting leaderboard")

        # Combine leaderboard + columns, then process
        if not self.competition_yaml['leaderboard'].get('columns') or not self.competition_yaml['leaderboard'].get('leaderboards'):
            raise CompetitionConversionException("Leaderboard data missing keys: columns, and leaderboards.")

        for ldb_key, ldb_data in self.competition_yaml['leaderboard']['leaderboards'].items():
            new_ldb_data = {
                'title': ldb_key,
                'key': ldb_key,
                'columns': []
            }
            new_leaderboard_list.append(new_ldb_data)

        col_index_counter = 0
        for col_key, col_data in self.competition_yaml['leaderboard']['columns'].items():
            new_col_data = {
                'title': col_data.get('label'),
                'key': col_key,
                'index': col_data.get('rank', col_index_counter),
                'sorting': 'desc'  # v1.5 doesn't have this at all????
            }

            col_index_counter += 1

            for leaderboard_data in new_leaderboard_list:
                if col_data['leaderboard']['label'].lower() == leaderboard_data['key'].lower():
                    leaderboard_data['columns'].append(new_col_data)

        del self.competition_yaml['leaderboard']
        self.competition_yaml['leaderboards'] = new_leaderboard_list

    def _convert_misc_keys(self):
        logger.info("Converting misc keys")
        top_level_keys = list(self.competition_yaml.keys())
        for top_level_key in top_level_keys:
            if top_level_key in self.LEGACY_COMPETITION_KEY_MAPPING:
                self.competition_yaml[self.LEGACY_COMPETITION_KEY_MAPPING[top_level_key]] = self.competition_yaml[top_level_key]
                del self.competition_yaml[top_level_key]
        # Do this again so we don't grab any keys we previously deleted
        top_level_keys = list(self.competition_yaml.keys())
        for top_level_key in top_level_keys:
            if top_level_key in self.LEGACY_DEPRECATED_KEYS:
                del self.competition_yaml[top_level_key]

    def _key_sanity_check(self, key):
        if not self.competition_yaml.get(key):
            raise CompetitionConversionException("Could not find {} key in data.".format(key))
        if not isinstance(self.competition_yaml.get(key), dict):
            raise CompetitionConversionException("Did not receive a dict of {} data, but the key is present".format(key))
