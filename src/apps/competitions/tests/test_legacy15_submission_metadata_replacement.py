from unittest import TestCase
from docker.compute_worker.compute_worker import Run


class LegacyConverterRemoteTests(TestCase):
    def setUp(self):
        self.test_scoring_commands = [
            'python $program/score.py $input $output',
            'python $program/evaluate.py $input $output',
        ]

        self.test_ingestion_commands = [
            'python $ingestion_program/ingestion.py $input $output $ingestion_program $submission_program',
        ]

        self.truth_commands_ingestion = [
            'python /app/program/ingestion.py /app/input_data /app/output /app/program /app/ingested_program',
        ]

        self.truth_commands_scoring = [
            'python /app/program/score.py /app/input /app/output',
            'python /app/program/evaluate.py /app/input /app/output',
        ]

    def test_v15_submission_metadata_replacement_works_on_scoring(self):
        for index, command in enumerate(self.test_scoring_commands):
            new_command = Run._replace_legacy_metadata_command(command=command, kind='scoring')
            assert new_command == self.truth_commands_scoring[index]

    def test_v15_submission_metadata_replacement_works_on_ingestion(self):
        for index, command in enumerate(self.test_ingestion_commands):
            new_command = Run._replace_legacy_metadata_command(command=command, kind='ingestion')
            assert new_command == self.truth_commands_ingestion[index]
