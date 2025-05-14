import os
import datetime

from competitions.unpackers.base_unpacker import BaseUnpacker
from competitions.unpackers.utils import CompetitionUnpackingException, get_datetime
import logging
logger = logging.getLogger()


class V15Unpacker(BaseUnpacker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Just in case docker image is blank (""), replace with default value
        docker_image = self.competition_yaml.get('competition_docker_image')
        if not docker_image:
            docker_image = "codalab/codalab-legacy:py37"

        self.competition = {
            "title": self.competition_yaml.get('title'),
            "logo": None,
            "registration_auto_approve": not self.competition_yaml.get('has_registration', True),
            "description": self.competition_yaml.get("description", ""),
            "docker_image": docker_image,
            "enable_detailed_results": self.competition_yaml.get('enable_detailed_results', False),
            "show_detailed_results_in_submission_panel": self.competition_yaml.get('show_detailed_results_in_submission_panel', True),
            "show_detailed_results_in_leaderboard": self.competition_yaml.get('show_detailed_results_in_leaderboard', True),
            "auto_run_submissions": self.competition_yaml.get('auto_run_submissions', True),
            "make_programs_available": self.competition_yaml.get('make_programs_available', False),
            "make_input_data_available": self.competition_yaml.get('make_input_data_available', False),
            "end_date": self.competition_yaml.get('end_date', None),
            "pages": [],
            "phases": [],
            "leaderboards": [],
            # Holding place for task and solution creation and for phases to reference afterword.
            "tasks": {},
            "solutions": [],
        }

    def unpack(self):
        self._unpack_pages()
        self._unpack_image()
        self._unpack_queue()
        self._unpack_phases()
        self._unpack_leaderboards()

    def _unpack_pages(self):
        try:
            pages = self.competition_yaml['html']
        except KeyError:
            raise CompetitionUnpackingException('HTML pages could not be found in the yaml file')

        if 'terms' not in pages:
            raise CompetitionUnpackingException(
                'A file containing the terms of the competition could not be located for this competition'
            )

        for index, (title, path) in enumerate(pages.items()):
            try:
                with open(os.path.join(self.temp_directory, path)) as f:
                    content = f.read()
            except FileNotFoundError:
                raise CompetitionUnpackingException(f'Could not find file for page: {title}')

            if title == 'terms':
                self.competition['terms'] = content
            else:
                self.competition['pages'].append({
                    "title": title,
                    "content": content,
                    "index": index,
                })

    def _unpack_phases(self):
        try:
            phases = self.competition_yaml['phases']
        except KeyError:
            raise CompetitionUnpackingException('No phases could be found for this competition')
        # convert dict to list, sorted by phasenumber
        phases = [phase for phase in sorted(phases.values(), key=lambda p: p['phasenumber'])]
        phases = self._preprocess_phases(phases)
        for index, phase in enumerate(phases):
            new_phase = {
                'index': index,
                'start': get_datetime(phase['start_date']),
                'name': phase['label'],
                'description': phase.get('description'),
                'max_submissions_per_day': phase.get('max_submissions_per_day', 5),
                'max_submissions_per_person': phase.get('max_submissions', 100),
                'auto_migrate_to_this_phase': phase.get('auto_migration', False),
                'hide_output': phase.get('hide_output', False),
                'hide_prediction_output': phase.get('hide_prediction_output', False),
                'hide_score_output': phase.get('hide_score_output', False),
            }
            execution_time_limit = phase.get('execution_time_limit')
            if execution_time_limit:
                new_phase['execution_time_limit'] = execution_time_limit
            if new_phase['max_submissions_per_person'] or new_phase['max_submissions_per_day']:
                new_phase['has_max_submissions'] = True
            try:
                next_phase = phases[index + 1]
                # V1 phases have no end dates.
                # to set an end date of a phase, get the next phase starting date
                next_phase_start_date = get_datetime(next_phase['start_date'])
                # subtract one day from it and use it as this phase end date
                new_phase['end'] = next_phase_start_date - datetime.timedelta(days=1)
            except IndexError:
                end = self.competition.get('end_date')
                if end and end != 'null':
                    new_phase['end'] = get_datetime(end)
                else:
                    new_phase['end'] = None

            # Public Data and Starting Kit
            try:
                new_phase['public_data'] = {
                    'file_name': phase['public_data'],
                    'file_path': os.path.join(self.temp_directory, phase['public_data']),
                    'file_type': 'public_data',
                    'creator': self.creator.id,
                }
            except KeyError:
                new_phase['public_data'] = None

            try:
                new_phase['starting_kit'] = {
                    'file_name': phase['starting_kit'],
                    'file_path': os.path.join(self.temp_directory, phase['starting_kit']),
                    'file_type': 'starting_kit',
                    'creator': self.creator.id,
                }
            except KeyError:
                new_phase['starting_kit'] = None

            task_index = len(self.competition['tasks'])
            new_phase['tasks'] = [task_index]
            self.competition['phases'].append(new_phase)

            new_task = {
                'name': f'{new_phase["name"]} Task',
                'description': new_phase['description'],
                'created_by': self.creator.id,
                'ingestion_only_during_scoring': phase.get('ingestion_program_only_during_scoring', False)
            }

            for file_type in ['ingestion_program', 'input_data', 'scoring_program', 'reference_data']:
                if file_type in phase:
                    new_task[file_type] = {
                        'file_name': phase[file_type],
                        'file_path': os.path.join(self.temp_directory, phase[file_type]),
                        'file_type': file_type,
                        'creator': self.creator.id,
                    }
            self.competition['tasks'][task_index] = new_task

        self._validate_phase_ordering()
        self._set_phase_statuses()

    def _preprocess_phases(self, phases):
        """If it's version 1.8, then we remove the first phase, which is the parent phase."""
        return phases[1:] if self._is_v18(phases) else phases

    def _is_v18(self, phases):
        """
        Determine if the current version is 1.8
        :return:
        """
        return any(p.get('is_parallel_parent') or p.get('parent_phasenumber') for p in phases)

    def _unpack_leaderboards(self):
        try:
            leaderboard = self.competition_yaml['leaderboard']
        except KeyError:
            raise CompetitionUnpackingException('Could not find leaderboard in the competition yaml')
        try:
            leaderboards = leaderboard['leaderboards']
        except KeyError:
            raise CompetitionUnpackingException('Could not find leaderboards declared on the competition leaderboard')
        try:
            # use rank = 1 if rank is not defined in .yaml file
            columns = sorted([{'title': k, **v} for k, v in leaderboard['columns'].items()], key=lambda c: c.get('rank', 1))
        except KeyError:
            raise CompetitionUnpackingException('Could not find columns declared on the competition leaderboard')

        for ldb_key, ldb_data in leaderboards.items():
            new_ldb_data = {
                'title': ldb_key,
                'key': ldb_key,
                'label': ldb_data['label'],
                'columns': []
            }
            self.competition['leaderboards'].append(new_ldb_data)

        for index, column in enumerate(columns):
            new_col_data = {
                # get label as title, if not found, use title by default
                'title': column.get('label', column['title']),
                'key': column['title'],
                'index': index,
                'sorting': column.get('sort') or 'desc',
                # get precision as numeric_format, if not found, use default value = 2
                'precision': column.get('numeric_format', 2),
                # get hidden, use False if not found
                'hidden': column.get('hidden', False)
            }

            for leaderboard_data in self.competition['leaderboards']:
                if column['leaderboard']['label'].lower() == leaderboard_data['label'].lower():
                    leaderboard_data['columns'].append(new_col_data)

    def _unpack_terms(self):
        # handled by _unpack_pages
        pass

    def _unpack_solutions(self):
        # no solutions to unpack
        pass

    def _unpack_tasks(self):
        # handled in _unpack_phases
        pass
