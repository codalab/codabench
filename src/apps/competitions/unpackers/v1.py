import os

from competitions.unpackers.base_unpacker import BaseUnpacker
from competitions.unpackers.utils import CompetitionUnpackingException, get_datetime


class V15Unpacker(BaseUnpacker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = {
            "title": self.competition_yaml.get('title'),
            "logo": None,
            "registration_auto_approve": not self.competition_yaml.get('has_registration', True),
            "docker_image": self.competition_yaml.get('competition_docker_image', 'codalab/codalab-legacy:py3'),
            "pages": [],
            "phases": [],
            "leaderboards": [],
            # Holding place for phases to reference. Ignored by competition serializer.
            "tasks": {},
            "solutions": [],
        }

    def unpack(self):
        self._unpack_pages()
        self._unpack_image()
        self._unpack_phases()
        self._unpack_leaderboards()

    def _unpack_pages(self):
        try:
            pages = self.competition_yaml['html']
        except KeyError:
            raise CompetitionUnpackingException('HTML pages could not be found in the yaml file')

        if 'terms' not in pages:
            # TODO: SHOULD terms be required? are they required in v1.5? How do we handle this?
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
        for index, phase in enumerate(phases):
            new_phase = {
                'index': index,
                'start': get_datetime(phase['start_date']),
                'name': phase['label'],
                'description': phase.get('description'),
                'max_submissions_per_day': phase.get('max_submissions_per_day'),
                'max_submissions_per_person': phase.get('max_submissions'),
                'auto_migrate_to_this_phase': phase.get('auto_migration', False),
            }
            execution_time_limit = phase.get('execution_time_limit')
            if execution_time_limit:
                new_phase['execution_time_limit'] = execution_time_limit
            if new_phase['max_submissions_per_person'] or new_phase['max_submissions_per_day']:
                new_phase['has_max_submissions'] = True
            try:
                next_phase = phases[index + 1]
                new_phase['end'] = get_datetime(next_phase['start_date'])
            except IndexError:
                end = self.competition.get('end_date')
                if end and end != 'null':
                    new_phase['end'] = get_datetime(end)
                else:
                    new_phase['end'] = None
            if not phase.get('is_parallel_parent') and not phase.get('parent_phasenumber'):
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
            else:
                raise CompetitionUnpackingException('Parallel Parents not supported')

        self._validate_phase_ordering()
        self._set_phase_statuses()

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
            columns = sorted([{'title': k, **v} for k, v in leaderboard['columns'].items()], key=lambda c: c['rank'])
        except KeyError:
            raise CompetitionUnpackingException('Could not find columns declared on the competition leaderboard')

        for ldb_key, ldb_data in leaderboards.items():
            new_ldb_data = {
                'title': ldb_key,
                'key': ldb_key,
                'columns': []
            }
            self.competition['leaderboards'].append(new_ldb_data)

        for index, column in enumerate(columns):
            new_col_data = {
                'title': column['title'],
                'key': column['title'],
                'index': index,
                'sorting': 'desc'  # TODO: not an option in v1.5?
            }

            for leaderboard_data in self.competition['leaderboards']:
                if column['leaderboard']['label'].lower() == leaderboard_data['key'].lower():
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
