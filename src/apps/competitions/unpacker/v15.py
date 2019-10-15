import datetime
import logging
from django.utils import timezone

from competitions.unpacker.exceptions import CompetitionUnpackingException, CompetitionConversionException
from competitions.unpacker.utils import _get_datetime, _zip_if_directory, get_data_key
from competitions.converter import LegacyBundleConverter
from competitions.models import Phase
from competitions.unpacker.v2 import V2Unpacker

logger = logging.getLogger()


class V15Unpacker(V2Unpacker):

    def unpack(self):
        converter = LegacyBundleConverter(data=self.competition_yaml)
        # We just need to convert our data before hand versus v2
        self.competition_yaml = converter.convert()
        print("Competiton yaml: {}".format(self.competition_yaml))
        return super().unpack()

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
            lambda p: p['start'] if p.get('start') else datetime.datetime < timezone.now() < p['end'] if p.get(
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
