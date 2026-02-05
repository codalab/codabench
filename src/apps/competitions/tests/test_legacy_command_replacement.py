from django.test import TestCase
# from compute_worker.compute_worker import replace_legacy_metadata_command
import pytest


def replace_legacy_metadata_command():
    pass


@pytest.mark.skip()
class LegacyConverterCommandTests(TestCase):
    def test_ingestion_command_is_converted_correctly(self):
        v15 = 'python $ingestion_program/ingestion.py $input $output $ingestion_program $submission_program'
        v2 = 'python /app/program/ingestion.py /app/input_data /app/output /app/program /app/ingested_program'
        assert replace_legacy_metadata_command(command=v15, kind='ingestion', is_scoring=False) == v2

    def test_scoring_command_is_converted_correctly(self):
        v15 = 'python $program/score.py $input $output'
        v2 = 'python /app/program/score.py /app/input /app/output'
        assert replace_legacy_metadata_command(command=v15, kind='program', is_scoring=False) == v2
