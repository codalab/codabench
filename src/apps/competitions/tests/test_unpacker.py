import datetime
import os
import zipfile
from tempfile import TemporaryDirectory
from uuid import UUID

import yaml
from django.test import TestCase

from apps.competitions.unpacker.unpacker import V15Unpacker
from competitions.unpacker.exceptions import CompetitionUnpackingException
from profiles.models import User

COMP_15_DICT = {}


class LegacyConverterRemoteTests(TestCase):
    def setUp(self):
        self.test_files_dir = os.path.join(os.getcwd(), 'src/tests/functional/test_files/')
        self.competition_15_bundle = os.path.join(self.test_files_dir, 'competition_15.zip')

        self.creator = User.objects.create(
            username='test_user'
        )

    def test_v15_unpacker(self):
        with TemporaryDirectory() as temp_directory:
            try:
                with zipfile.ZipFile(self.competition_15_bundle, 'r') as zip_pointer:
                    zip_pointer.extractall(temp_directory)
            except zipfile.BadZipFile:
                raise CompetitionUnpackingException("Bad zip file uploaded.")

            # ---------------------------------------------------------------------
            # Read metadata (competition.yaml)
            yaml_path = os.path.join(temp_directory, "competition.yaml")
            yaml_data = open(yaml_path).read()
            competition_yaml = yaml.load(yaml_data)

            unpacker = V15Unpacker(
                competition_yaml=competition_yaml,
                temp_directory=temp_directory,
                creator=self.creator,
                version='1.5')
            competition_serializer_dict = unpacker.unpack()
            assert competition_serializer_dict == COMP_15_DICT
