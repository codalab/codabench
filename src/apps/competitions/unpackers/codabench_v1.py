import os

from django.utils import timezone

from competitions.unpackers.base_unpacker import BaseUnpacker
from .utils import CompetitionUnpackingException


class CodabenchV1Unpacker(BaseUnpacker):
    """
    transform a benchmarks bundle to competition
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = {
            "title": self.competition_yaml.get('title'),
            "logo": None,
            "registration_auto_approve": self.competition_yaml.get('registration_auto_approve', False),
            "docker_image": self.competition_yaml.get('docker_image', 'codalab/codalab-legacy:py3'),
            "enable_detailed_results": self.competition_yaml.get('enable_detailed_results', False),
            "description": self.competition_yaml.get("description", ""),
            "pages": [],
            "phases": [], # benchmarks did not have concept of phase, we set phase by default in backend.
            "leaderboards": [],
            # Holding place for task and solution creation and for phases to reference afterword.
            "tasks": {},
            "solutions": [],
        }

    def unpack(self):
        self._unpack_pages()
        self._unpack_tasks()
        self._unpack_solutions()
        self._unpack_terms()
        self._unpack_image()
        self._unpack_queue()
        self._set_default_phase()
        self._unpack_leaderboard()

    def _unpack_pages(self):
        # ---------------------------------------------------------------------
        # Pages
        for index, page in enumerate(self.competition_yaml.get('pages')):
            try:
                with open(os.path.join(self.temp_directory, page["file"])) as f:
                    page_content = f.read()
            except FileNotFoundError:
                raise CompetitionUnpackingException(f"Unable to find page: {page['file']}")

            if not page_content:
                raise CompetitionUnpackingException(f"Page '{page['file']}' is empty, it must contain content.")

            self.competition['pages'].append({
                "title": page.get("title"),
                "content": page_content,
                "index": index,
            })

    def _unpack_tasks(self):
        # ---------------------------------------------------------------------
        # Tasks
        try:
            tasks = self.competition_yaml['tasks']
        except KeyError:
            raise CompetitionUnpackingException('No tasks listed in this competition')

        for task in tasks:
            try:
                index = task['index']
            except KeyError:
                raise CompetitionUnpackingException(
                    f'ERROR: No index for task: {task.get("name") or task.get("key")}'
                )

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
                }
                for file_type in ['ingestion_program', 'input_data', 'scoring_program', 'reference_data']:
                    if file_type in task:
                        new_task[file_type] = {
                            'file_name': task[file_type],
                            'file_path': os.path.join(self.temp_directory, task[file_type]),
                            'file_type': file_type,
                            'creator': self.creator.id,
                        }
                    elif file_type == 'scoring_program':
                        raise CompetitionUnpackingException(
                            f'ERROR: Task "{task.get("name") or index}" does not have a scoring program'
                        )
                self.competition['tasks'][index] = new_task

    def _unpack_solutions(self):
        # ---------------------------------------------------------------------
        # Solutions
        solutions = self.competition_yaml.get('solutions')
        if not solutions:
            return

        for solution in solutions:
            try:
                index = solution['index']
            except KeyError:
                raise CompetitionUnpackingException(
                    f"ERROR: No index for solution: {solution.get('name') or solution.get('key')}"
                )

            try:
                tasks = solution['tasks']
            except KeyError:
                raise CompetitionUnpackingException(f"Could not find tasks for solution: {solution.get('name') or solution.get('key')}")

            if not all([task_index in self.competition['tasks'] for task_index in tasks]):
                raise CompetitionUnpackingException(
                    f"ERROR: Solution: {solution['key']} missing task index pointers"
                )

            if index in self.competition['solutions']:
                raise CompetitionUnpackingException(f"ERROR: Duplicate solution indexes. Index: {index}")

            if 'key' in solution:
                new_solution = {
                    'key': solution['key']
                }
            else:
                try:
                    file_name = solution['path']
                except KeyError:
                    raise CompetitionUnpackingException(f'Solution {solution.get("name")} missing "path"')

                file_path = os.path.join(self.temp_directory, file_name)

                new_solution = {
                    'file_name': file_name,
                    'file_path': file_path,
                    'name': solution.get('name') or f"solution @ {timezone.now():%m-%d-%Y %H:%M}",
                    'description': solution.get('description'),
                    'creator': self.creator.id,
                }
            new_solution['tasks'] = tasks
            self.competition['solutions'].append(new_solution)

    def _unpack_terms(self):
        # ---------------------------------------------------------------------
        # Terms
        try:
            terms_path = self.competition_yaml['terms']
        except KeyError:
            raise CompetitionUnpackingException(
                'A file containing the terms of this competition has not been supplied in the required location'
            )

        try:
            with open(os.path.join(self.temp_directory, terms_path)) as f:
                terms_content = f.read()
        except FileNotFoundError:
            raise CompetitionUnpackingException(f"Unable to find page: {terms_path}")

        if not terms_content:
            raise CompetitionUnpackingException(f"{terms_path} is empty, it must contain content.")

        self.competition['terms'] = terms_content

    def _set_default_phase(self):
        # ---------------------------------------------------------------------
        # Phases
        new_phase = {
            "index": 0,
            "name": 'DEAFULT'
        }
        try:
            new_phase['tasks'] = self._collect_task_index_from_yaml()
        except KeyError:
            raise CompetitionUnpackingException(f'Phases must contain at least one task to be valid')

        new_phase['start'] = self._generate_default_phase_start_time()
        self.competition['phases'].append(new_phase)

        self._validate_phase_ordering()
        self._set_phase_statuses()

    def _unpack_leaderboard(self):
        # ---------------------------------------------------------------------
        # Leaderboard
        try:
            leaderboard = self.competition_yaml['leaderboard']
        except KeyError:
            raise CompetitionUnpackingException('Could not find leaderboard in the competition yaml')

        # To be compatible with the definition of the CompetitionSerializer,
        # convert the dict type to an element in the list
        self.competition['leaderboards'] = [leaderboard]

    @staticmethod
    def _generate_default_phase_start_time():
        from datetime import datetime
        return datetime.now().replace(tzinfo=timezone.now().tzinfo)

    def _collect_task_index_from_yaml(self):
        return [item['index'] for item in self.competition_yaml['tasks']]

