import datetime
import logging
import json
import copy
import os

from apps.competitions.tasks import CompetitionUnpackingException
logger = logging.getLogger(__name__)


class CompetitionConversionException(CompetitionUnpackingException):
    pass


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
    # 'public_data': 'public_data',
    # 'starting_kit': 'starting_kit',
}

# TODO: Remove all casts, or smartly handle them based on type(?)

class LegacyBundleConverter:
    """
    Bundle converter for v1.5 to v2:
        - Data: Should be the YAML data from the bundle read to a Python dict
    """
    def __init__(self, data={}):
        # Do a deep copy so we're not modifying the original and can re-check against it
        self.data = copy.deepcopy(data)

    def __get_next_parent_phase(self, current_index):
        # Loop through all of our phase objects, and find the first one which is greater than our current phase and is a parallel parent.
        for phase_index, phase_data in self.data['phases'].items():
            if phase_data.get('is_parallel_parent') and phase_index > current_index:
                return phase_index
        return None

    def __get_parent_phase(self, parent_phase_index, new_temp_phase_list):
        # Loop through index, phase_data and find whichever one has the matching index. We delete the extra key later.
        for index, phase_data in enumerate(new_temp_phase_list):
            if phase_data.get('index') == parent_phase_index:
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
        if self.data['phases'].get(next_index):
            # Handle parent phases
            # if self.data['phases'][current_index].get('is_parallel_parent'):
            #     # This is a parent phase
            #     pass
            # elif self.data['phases'][current_index].get('parent_phasenumber'):
            #     # This is a child phase
            #     pass
            # else:
            # This is a regular sequential phase without children/parents
            logger.info('Converter: There is a next phase')
            print('Converter: There is a next phase')
            if self.data['phases'][next_index].get('start_date'):
                logger.info('Converter: There is a next phase with a start date')
                print('Converter: There is a next phase with a start date')
                # We have a phase after this one with a start date
                # new_phase_data['end'] = self.data['phases'][next_index]['start_date']
                return self.data['phases'][next_index]['start_date']
        return None

    def convert(self, plain=False):
        if not self._is_legacy_bundle():
            logger.info("Bundle data does not appear to be legacy. Skipping.")
            print("Bundle data does not appear to be legacy. Skipping.")
            return self.data
        else:
            if not self.data.get('competition_docker_image') or not self.data.get('docker_image'):
                self.data['docker_image'] = 'ckcollab/codalab-legacy:latest'
        self._convert_pages()
        self._convert_phases()
        self._convert_leaderboard()
        self._convert_misc_keys()
        if plain:
            self.data = json.loads(json.dumps(self.data, default=str))
        print("Retrning data: {}".format(self.data))
        return self.data

    def _is_legacy_bundle(self):
        return any([bool(key in self.data) for key in LEGACY_DEPRECATED_KEYS])

    def _convert_pages(self):
        new_html_data = []

        self._key_sanity_check('html')
        logger.info("Converting HTML to pages")
        print("Converting HTML to pages")
        for page_key, page_file in self.data['html'].items():
            if page_key == 'terms':
                self.data['terms'] = page_file
            new_html_data.append({
                'title': page_key,
                'file': page_file
            })
        del self.data['html']
        self.data['pages'] = new_html_data


    def _convert_phases(self):
        new_phase_list = []
        new_task_list = []
        new_solution_list = []

        self._key_sanity_check('phases')
        logger.info("Converting phase format")
        print("Converting phase format")

        has_parent_phases = any('is_parallel_parent' in phase_data for phase_index, phase_data in self.data['phases'].items())

        logger.info("Converter: Has parent phases: {}".format(has_parent_phases))

        for phase_index, phase_data in self.data['phases'].items():
            new_phase_data = {}
            new_task_data = {}
            parent_phase_tracking = {}

            legacy_index_type = type(phase_index)
            legacy_index = legacy_index_type(phase_index)

            new_task_data['index'] = int(phase_index)

            # Automatic mapping
            for phase_data_key, phase_data_value in phase_data.items():
                if phase_data_key in LEGACY_PHASE_KEY_MAPPING:
                    new_phase_data[LEGACY_PHASE_KEY_MAPPING[phase_data_key]] = phase_data_value
                if phase_data_key in PHASE_TASK_COMMON_MAPPING:
                    new_task_data[PHASE_TASK_COMMON_MAPPING[phase_data_key]] = phase_data_value

            # If we're not a child phase, get our next date and set it
            if not self.data['phases'][phase_index].get('parent_phasenumber'):
                next_index = self.__get_next_index(current_index=phase_index, key_type=legacy_index_type,
                                                   has_parent_phases=has_parent_phases)
                next_end_date = self.__get_phase_end(phase_index, next_index)
                if next_end_date:
                    new_phase_data['end'] = next_end_date


            # This is dumb. Phases in legacy format are `indices` but are read as strings. This fails in tests, so help
            # it out with the converison


            # TODO: Rework this... This should all be based on phase_index type...

            # if type(phase_index) != int:
            #     phase_index = int(phase_index)
            #     next_index = int(phase_index) + 1
            # else:
            #     phase_index = str(phase_index)
            #     next_index = str(int(phase_index) + 1)

            # # Try to set the data type right. In tests all keys are strings, in non-tests int are fine as keys
            # if not self.data['phases'].get(next_index) and type(next_index) == int:
            #     next_index = str(next_index)
            # if not self.data['phases'].get(next_index) and type(next_index) == str:
            #     next_index = int(next_index)

            # Call our next end stuff here

            new_task_list.append(new_task_data)
            if phase_data.get('starting_kit'):
                new_solution_data = {
                    'index': int(phase_index),
                    'tasks': [int(phase_index)],
                    'path': phase_data.get('starting_kit')
                }
                new_phase_data['solutions'] = [int(phase_index)]
                new_solution_list.append(new_solution_data)

            print(self.data['phases'])
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            # print(self.data['phases'])
            print(phase_index)
            print(type(phase_index))
            print([type(index) for index in self.data['phases'].keys()])
            print(self.data['phases'].keys())
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            # Handle new task + solution
            if has_parent_phases and self.data['phases'][phase_index].get('parent_phasenumber'):
                # self.__get_parent_phase(phase_index, new_phase_list)
                # parent_phase_index = self.data['phases'][phase_index]['parent_phasenumber']
                # if parent_phase_index > 1:
                #     parent_phase_index -= 1
                # print(parent_phase_index)
                # print(len(new_phase_list))
                parent_phase_index = self.__get_parent_phase(self.data['phases'][phase_index]['parent_phasenumber'], new_phase_list)
                logger.info("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                logger.info("This phase has a parent phase that should be at index {}".format(self.data['phases'][phase_index]['parent_phasenumber']))
                logger.info(parent_phase_index)
                logger.info("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                if parent_phase_index != None:
                    logger.info("Adding task entry to phase")
                    if not new_phase_list[parent_phase_index].get('tasks'):
                        new_phase_list[parent_phase_index]['tasks'] = []
                    new_phase_list[parent_phase_index]['tasks'].append(int(phase_index))
            elif has_parent_phases and self.data['phases'][phase_index].get('is_parallel_parent'):
                new_phase_data['index'] = phase_index
                logger.info("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
                logger.info("This is a parent phase; Adding it's index to help track: {}".format(phase_index))
                print(new_phase_data)
                print(new_phase_list)
                logger.info("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
                new_phase_list.append(new_phase_data)
            else:
                logger.info("Regularly doing phase data, and task data")
                new_phase_data['tasks'] = [int(phase_index)]
                # Append our new phase data
                new_phase_list.append(new_phase_data)

                # if self.data['phases'][phase_index].get('is_parallel_parent'):
                #     parent_phase_tracking[
        print(new_phase_list)
        del self.data['phases']
        # Cleanup residual keys we're not using
        for phase_data in new_phase_list:
            if phase_data.get('index'):
                del phase_data['index']
        self.data['phases'] = new_phase_list
        self.data['tasks'] = new_task_list
        self.data['solutions'] = new_solution_list


    def _convert_leaderboard(self):
        new_leaderboard_list = []


        logger.info("Converting leaderboard")
        print("Converting leaderboard")

        # Combine leaderboard + columns, then process
        if not self.data['leaderboard'].get('columns') or not self.data['leaderboard'].get('leaderboards'):
            raise CompetitionConversionException("Leaderboard data missing keys: columns, and leaderboards.")

        for ldb_key, ldb_data in self.data['leaderboard']['leaderboards'].items():
            new_ldb_data = {
                'title': ldb_key,
                'key': ldb_key,
                'columns': []
            }
            new_leaderboard_list.append(new_ldb_data)

        col_index_counter = 0
        for col_key, col_data in self.data['leaderboard']['columns'].items():
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

        del self.data['leaderboard']
        self.data['leaderboards'] = new_leaderboard_list

    def _convert_misc_keys(self):
        logger.info("Converting misc keys")
        print("Converting misc keys")
        top_level_keys = list(self.data.keys())
        for top_level_key in top_level_keys:
            if top_level_key in LEGACY_COMPETITION_KEY_MAPPING:
                self.data[LEGACY_COMPETITION_KEY_MAPPING[top_level_key]] = self.data[top_level_key]
                del self.data[top_level_key]
        # Do this again so we don't grab any keys we previously deleted
        top_level_keys = list(self.data.keys())
        for top_level_key in top_level_keys:
            if top_level_key in LEGACY_DEPRECATED_KEYS:
                del self.data[top_level_key]

    def _key_sanity_check(self, key):
        if not self.data.get(key):
            raise CompetitionConversionException("Could not find {} key in data.".format(key))
        if not isinstance(self.data.get(key), dict):
            raise CompetitionConversionException("Did not receive a dict of {} data, but the key is present".format(key))

# import yaml
# import requests
# from apps.competitions.converter import LegacyBundleConverter
# my_url = 'https://raw.githubusercontent.com/madclam/m2aic2019/master/starting_kit/utilities/competition.yaml'
# # my_url = 'https://raw.githubusercontent.com/madclam/timeSeries/master/starting_kit/utilities/sample_bundle_19-04-09-22-34/competition.yaml'
# resp = requests.get(my_url)
# my_data = resp.content
# my_yaml_data = yaml.load(my_data)
# converter = LegacyBundleConverter(my_yaml_data)
# result = converter.convert()
# with open('data.yml', 'w') as outfile:
#     yaml.dump(result, outfile, default_flow_style=False, ignore_aliases=True)
