import json
import os
import yaml

from unittest import TestCase

from apps.competitions.converter import LegacyBundleConverter, LEGACY_PHASE_KEY_MAPPING, LEGACY_DEPRECATED_KEYS


COMP_DICT = {}

class LegacyConverterRemoteTests(TestCase):

    def setUp(self):
        self.test_files_dir = os.path.join(os.getcwd(), 'src/apps/competitions/tests/files/')
        assert os.path.exists(self.test_files_dir)

        self.yaml_data = yaml.load(open(os.path.join(self.test_files_dir, 'legacy.yaml'), 'r'))
        # We do this with JSON here to make sure in tests we're working with plain dictionaries. It looks like
        # we're defaulting to using OYAML, which outputs ordered dictionaries.
        self.yaml_data = json.loads(json.dumps(self.yaml_data, default=str))
        self.truth_data = yaml.load(open(os.path.join(self.test_files_dir, 'truth.yaml'), 'r'))
        # We do this with JSON here to make sure in tests we're working with plain dictionaries. It looks like
        # we're defaulting to using OYAML, which outputs ordered dictionaries.
        self.truth_data = json.loads(json.dumps(self.truth_data, default=str))

    def test_v15_unpacker(self):
        l = Legacy_unpacker()
        new_dict = l.unpack(yaml.load())
        assert new_dict == COMP_DICT

    def test_converter_converts_pages_fine(self):
        converter = LegacyBundleConverter(self.yaml_data)
        # This only acts on the data stored in the converter object
        converter._convert_pages()

        # HTML key asserts
        # Assert that in our original data we have the html key
        assert 'html' in self.yaml_data.keys()
        # Assert that we no longer have an HTML key after conversion
        assert 'html' not in converter.data.keys()

        # Page key asserts
        # Assert that in our original data we do not have the pages key
        assert 'pages' not in self.yaml_data.keys()
        # Assert that we now have the pages key in our converted YAML
        assert 'pages' in converter.data.keys()

        # Assert that previously our objects were formatted completely differently
        assert isinstance(self.yaml_data['html'], dict)
        # Assert that the last instance of our page data in legacy format is a dict
        # assert isinstance(self.yaml_data['html'], dict)

        # Assert that our pages key is an instance of list, being a list of dict with key/value pairs
        assert isinstance(converter.data['pages'], list)
        # Assert that our last page object in the list, is a dict
        assert isinstance(converter.data['pages'][-1], dict)

        # Assert that our page object (dict) contains the keys we need to read
        assert converter.data['pages'][-1].get('title')
        assert converter.data['pages'][-1].get('file')

        # Assert we get the same number of pages
        assert len(converter.data['pages']) == len(self.yaml_data['html'].keys())

        # Assert that it equals the verified output we have that works
        assert converter.data['pages'] == self.truth_data['pages']

    def test_converter_converts_phases_fine(self):
        converter = LegacyBundleConverter(self.yaml_data)
        # This only acts on the data stored in the converter object
        converter._convert_phases()

        # Assert our old data is formatted how we'd expect
        assert 'phases' in self.yaml_data.keys()
        assert isinstance(self.yaml_data['phases'], dict)

        # Assert our new data is formatted correctly
        assert 'phases' in converter.data.keys()
        assert isinstance(converter.data['phases'], list)

        # Assert our data is equal in length between the two formats
        assert len(converter.data['phases']) == len(self.yaml_data['phases'].keys())

        # Assert our conversion created tasks. We cannot check for solutions because solutions depend on a starting kit
        # being defined. Cannot also check length against phases because parent/child relations
        assert 'tasks' in converter.data.keys()

        # Assert they contain the same data in converted keys.
        # This check is grabbing the last phase by key in the legacy bundle, and checking it's label against the
        # last phase's name in our new phases list. They should be 1:1
        assert self.yaml_data['phases'][list(self.yaml_data['phases'].keys())[-1]]['label'] == converter.data['phases'][-1]['name']

        # Assert our new phases actually have a task key
        assert 'tasks' in converter.data['phases'][-1].keys()

        # Assert our start and end dates are correctly set on conversion.

        # First check that our start's didn't get changed in the conversion
        assert self.yaml_data['phases'][list(self.yaml_data['phases'].keys())[-1]]['start_date'] == converter.data['phases'][-1]['start']

        # Next check that (if we have at least 2 phases) that the first one's end date is equal to the second's start date
        if len(self.yaml_data['phases'].keys()) > 1 and len(converter.data['phases']) > 1:
            assert converter.data['phases'][0]['end'] == converter.data['phases'][1]['start']

        # Make a list to assert we didn't carry over any keys that shouldn't be by making a list of booleans for
        # whether each deprecated key is in our new data:
        changed_legacy_keys = [key for key in LEGACY_PHASE_KEY_MAPPING.keys() if key != LEGACY_PHASE_KEY_MAPPING[key]]
        bool_list_comp = [dep_key in converter.data['phases'][-1].keys() for dep_key in changed_legacy_keys]
        # Assert that we do not have any `True` booleans in our list comprehension
        assert not any(bool_list_comp)

        # Assert that for key in our legacy mappings, it is replaced by it's value counterpart in our legacy mappings
        # for our first phase
        assert all(
            [
                converter.data['phases'][0][LEGACY_PHASE_KEY_MAPPING[key]] == self.yaml_data['phases']['1'][key] for key
                in self.yaml_data['phases']['1'].keys() if LEGACY_PHASE_KEY_MAPPING.get(key)
            ]
        )

        assert converter.data['phases'] == self.truth_data['phases']
        assert converter.data['tasks'] == self.truth_data['tasks']
        assert converter.data['solutions'] == self.truth_data['solutions']

    def test_converter_converts_leaderboards_fine(self):
        converter = LegacyBundleConverter(self.yaml_data)
        # This only acts on the data stored in the converter object
        converter._convert_leaderboard()

        # Assert our old data is formatted how we'd expect
        assert 'leaderboard' in self.yaml_data.keys()
        assert isinstance(self.yaml_data['leaderboard'], dict)

        assert 'leaderboards' in self.yaml_data['leaderboard'].keys()
        assert 'columns' in self.yaml_data['leaderboard'].keys()

        # Assert our new data is formatted correctly
        assert 'leaderboards' in converter.data.keys()
        assert isinstance(converter.data['leaderboards'], list)

        assert all([key in list(converter.data['leaderboards'][0].keys()) for key in ['title', 'key']])
        assert all([key in list(converter.data['leaderboards'][0]['columns'][0].keys()) for key in ['title', 'key', 'index', 'sorting']])

        # Assert that our old columns and new columns should line up:
        # This check seems pointless, since really we re-arrange and change at most 3 keys.

        # Assert that our converter data matches truth
        assert converter.data['leaderboards'] == self.truth_data['leaderboards']

    def test_converter_converts_deprecated_keys_fine(self):
        converter = LegacyBundleConverter(self.yaml_data)
        # This only acts on the data stored in the converter object
        converter._convert_misc_keys()

        assert all([key not in converter.data.keys() for key in LEGACY_DEPRECATED_KEYS])

    def test_entire_converter_process_against_truth_data(self):
        converter = LegacyBundleConverter(self.yaml_data)
        # This only acts on the data stored in the converter object
        result = converter.convert(plain=True)
        assert result == self.truth_data
