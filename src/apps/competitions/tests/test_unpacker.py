import json
import os
from tempfile import TemporaryDirectory

import yaml

from unittest import TestCase

from apps.competitions.unpacker.unpacker import V2Unpacker, V15Unpacker
from profiles.models import User

COMP_15_DICT = {}
COMP_2_DICT = {}


class LegacyConverterRemoteTests(TestCase):
    def setUp(self):
        self.test_files_dir = os.path.join(os.getcwd(), 'src/apps/competitions/tests/files/')

        self.yaml_data_15 = yaml.load(open(os.path.join(self.test_files_dir, 'legacy.yaml'), 'r'))
        # We do this with JSON here to make sure in tests we're working with plain dictionaries. It looks like
        # we're defaulting to using OYAML, which outputs ordered dictionaries.
        self.yaml_data_15 = json.loads(json.dumps(self.yaml_data_15, default=str))

        self.yaml_data_2 = yaml.load(open(os.path.join(self.test_files_dir, 'v2.yaml'), 'r'))
        # We do this with JSON here to make sure in tests we're working with plain dictionaries. It looks like
        # we're defaulting to using OYAML, which outputs ordered dictionaries.
        self.yaml_data_2 = json.loads(json.dumps(self.yaml_data_2, default=str))

        self.creator = User.objects.create(
            username='test_user'
        )

    def test_v15_unpacker(self):
        with TemporaryDirectory() as temp_directory:
            unpacker = V15Unpacker(
                competition_yaml=self.yaml_data_15,
                temp_directory=temp_directory,
                creator=self.creator,
                version='1.5')
            competition_serializer_dict = unpacker.unpack()
            assert competition_serializer_dict == COMP_15_DICT

    def test_v2_unpacker(self):
        with TemporaryDirectory() as temp_directory:
            unpacker = V2Unpacker(
                competition_yaml=self.yaml_data_2,
                temp_directory=temp_directory,
                creator=self.creator,
                version='2')
            competition_serializer_dict = unpacker.unpack()
            assert competition_serializer_dict == COMP_2_DICT
