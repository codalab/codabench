import os
from django.utils import timezone

from competitions.unpackers.base_unpacker import BaseUnpacker
from .utils import get_datetime, CompetitionUnpackingException


class V2Unpacker(BaseUnpacker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = {
            "title": self.competition_yaml.get('title'),
            "logo": None,
            "registration_auto_approve": self.competition_yaml.get('registration_auto_approve', False),
            "docker_image": self.competition_yaml.get('docker_image', 'codalab/codalab-legacy:py37'),
            "enable_detailed_results": self.competition_yaml.get('enable_detailed_results', False),
            "show_detailed_results_in_submission_panel": self.competition_yaml.get('show_detailed_results_in_submission_panel', True),
            "show_detailed_results_in_leaderboard": self.competition_yaml.get('show_detailed_results_in_leaderboard', True),
            "auto_run_submissions": self.competition_yaml.get('auto_run_submissions', True),
            "can_participants_make_submissions_public": self.competition_yaml.get('can_participants_make_submissions_public', True),
            "make_programs_available": self.competition_yaml.get('make_programs_available', False),
            "make_input_data_available": self.competition_yaml.get('make_input_data_available', False),
            "description": self.competition_yaml.get("description", ""),
            "competition_type": self.competition_yaml.get("competition_type", "competition"),
            "fact_sheet": self.competition_yaml.get("fact_sheet", None),
            "reward": self.competition_yaml.get("reward", None),
            "contact_email": self.competition_yaml.get("contact_email", None),
            "forum_enabled": self.competition_yaml.get("forum_enabled", True),
            "pages": [],
            "phases": [],
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
        self._unpack_phases()
        self._unpack_leaderboards()

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

    def _unpack_phases(self):
        # ---------------------------------------------------------------------
        # Phases
        try:
            # Sorting by index order and then enumerating below to keep phase order but indexes become 0 -> len(phases)
            phases = sorted(self.competition_yaml['phases'], key=lambda p: p.get('index', 0))
        except KeyError:
            raise CompetitionUnpackingException("Unable to find any phases for this competition")

        for index, phase_data in enumerate(phases):
            new_phase = {
                "index": index,
                "name": phase_data.get('name'),
                "description": phase_data.get('description'),
                "start": get_datetime(phase_data.get('start')),
                "end": get_datetime(phase_data.get('end')),
                'max_submissions_per_day': phase_data.get('max_submissions_per_day', 5),
                'max_submissions_per_person': phase_data.get('max_submissions', 100),
                'auto_migrate_to_this_phase': phase_data.get('auto_migrate_to_this_phase', False),
                'hide_output': phase_data.get('hide_output', False),
                'hide_prediction_output': phase_data.get('hide_prediction_output', False),
                'hide_score_output': phase_data.get('hide_score_output', False),
            }
            try:
                new_phase['tasks'] = phase_data['tasks']
            except KeyError:
                raise CompetitionUnpackingException(f'Phases must contain at least one task to be valid')

            execution_time_limit = phase_data.get('execution_time_limit')
            if execution_time_limit:
                new_phase['execution_time_limit'] = execution_time_limit

            if new_phase['max_submissions_per_day'] or new_phase['max_submissions_per_person']:
                new_phase['has_max_submissions'] = True

            # Public Data and Starting Kit
            try:
                new_phase['public_data'] = {
                    'file_name': phase_data['public_data'],
                    'file_path': os.path.join(self.temp_directory, phase_data['public_data']),
                    'file_type': 'public_data',
                    'creator': self.creator.id,
                }
            except KeyError:
                new_phase['public_data'] = None

            try:
                new_phase['starting_kit'] = {
                    'file_name': phase_data['starting_kit'],
                    'file_path': os.path.join(self.temp_directory, phase_data['starting_kit']),
                    'file_type': 'starting_kit',
                    'creator': self.creator.id,
                }
            except KeyError:
                new_phase['starting_kit'] = None

            self.competition['phases'].append(new_phase)
        self._validate_phase_ordering()
        self._set_phase_statuses()

    def _unpack_leaderboards(self):
        # ---------------------------------------------------------------------
        # Leaderboards
        try:
            leaderboards = self.competition_yaml['leaderboards']
        except KeyError:
            raise CompetitionUnpackingException('Could not find leaderboards in the competition yaml')

        self.competition['leaderboards'] = leaderboards
