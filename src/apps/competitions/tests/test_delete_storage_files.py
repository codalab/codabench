from unittest import mock

from django.test import SimpleTestCase

from competitions.tasks import delete_storage_files
from utils.storage import BundleStorage


class DeleteStorageFilesTests(SimpleTestCase):
    """
    Tests for the delete_storage_files celery task, which deletes the files of a deleted competition
    from storage and logs one report. The storage is mocked, so no real file is deleted.
    """

    def setUp(self):
        # Files as CompetitionDeleter.files() passes them: {file type: [[model label, field name, file name]]}.
        # All are dataset files, so all are in BundleStorage, the storage of Data.data_file.
        # They are deleted in this order: ingestion program, scoring program, starting kit
        self.files = {
            'task datasets': [
                ['datasets.Data', 'data_file', 'dataset/ingestion_program.zip'],
                ['datasets.Data', 'data_file', 'dataset/scoring_program.zip'],
            ],
            'phase datasets': [['datasets.Data', 'data_file', 'dataset/starting_kit.zip']],
        }

    def _delete_storage_files(self, storage_errors):
        """
        Runs the task with BundleStorage.delete mocked, and returns the mocked delete and the log report.
        `storage_errors` gives what each storage delete does, in order: None succeeds, an exception fails.
        """
        with mock.patch.object(BundleStorage, 'delete', side_effect=storage_errors) as storage_delete:
            with self.assertLogs('competitions.tasks', level='INFO') as logs:
                delete_storage_files(competition_id=1, competition_title='Test', files=self.files)
        # The whole report is logged once
        assert len(logs.records) == 1
        return storage_delete, logs.records[0]

    @staticmethod
    def _type_line(file_type, result):
        """Returns the report line of a file type, padded the same way as in delete_storage_files"""
        return f"{file_type:<28} {result}"

    def test_all_files_deleted(self):
        """Every file is deleted from storage, and the report is logged at info level with no failure"""
        storage_delete, report = self._delete_storage_files(storage_errors=[None, None, None])

        storage_delete.assert_has_calls([
            mock.call('dataset/ingestion_program.zip'),
            mock.call('dataset/scoring_program.zip'),
            mock.call('dataset/starting_kit.zip'),
        ])
        assert report.levelname == 'INFO'
        message = report.getMessage()
        assert 'Deleting files of competition 1 "Test"' in message
        assert 'Files to delete: 3' in message
        assert self._type_line('task datasets', '2 of 2 deleted') in message
        assert self._type_line('phase datasets', '1 of 1 deleted') in message
        assert 'Total: 3 deleted, 0 failed' in message

    def test_failed_file_is_reported_and_other_files_still_deleted(self):
        """
        When a file fails to delete, the other files are still deleted, and the report is logged at error level
        with the failed file and its error under its file type
        """
        # The ingestion program fails, the scoring program and starting kit are deleted
        storage_delete, report = self._delete_storage_files(storage_errors=[Exception('storage error'), None, None])

        # The files after the failed one are still deleted
        assert storage_delete.call_count == 3
        assert report.levelname == 'ERROR'
        message = report.getMessage()
        assert self._type_line('task datasets', '1 of 2 deleted, 1 failed') in message
        assert 'Failed to delete dataset/ingestion_program.zip: storage error' in message
        assert self._type_line('phase datasets', '1 of 1 deleted') in message
        assert 'Total: 2 deleted, 1 failed' in message
