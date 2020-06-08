
from django.utils import timezone

from competitions.unpackers.v2 import V2Unpacker
from .utils import CompetitionUnpackingException
from ..models import Competition


class CodabenchV1Unpacker(V2Unpacker):
    """
    this unpacker mainly focus on unpack benchmark bundle and create correspond model in order to create benchmark.
    from benchmark bundle transfer to competition v2 bundle is not support here, it will raise ambiguity,
    reason is:

    1. user upload bundle from benchmark page to create bench mark
    2. user upload bundle from competition page to create competition by using benchmark bundle

    how could we distinguish the path user upload from? because we will use same api upload_completed()..
    If we insist on it, there will be more code changes and the readability will be greatly reduced.
    """
    def unpack(self):
        self._unpack_pages()
        self._unpack_tasks()
        self._unpack_solutions()
        self._unpack_terms()
        self._unpack_image()
        self._unpack_queue()
        self._set_default_phase()
        self._unpack_leaderboard()
        self._set_competition_type()

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

    def _set_competition_type(self):
        """
        we set competition type to `Competition.BENCHMARK` here, so the front end could use this type to implement
        UI special logic
        by default this type is `Competition.COMPETITION`
        """
        self.competition['type'] = Competition.BENCHMARK

    @staticmethod
    def _generate_default_phase_start_time():
        from datetime import datetime
        return datetime.now().replace(tzinfo=timezone.now().tzinfo)

    def _collect_task_index_from_yaml(self):
        return [item['index'] for item in self.competition_yaml['tasks']]
