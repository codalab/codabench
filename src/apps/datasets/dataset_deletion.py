"""
Code to delete datasets.

Use DatasetDeleter whenever datasets are deleted: one dataset or many.
Data.delete() uses it too.
"""
import logging

from django.db import transaction

from datasets.models import Data

logger = logging.getLogger(__name__)


class DatasetDeleter:
    """
    Deletes datasets and their files.
    Use it whenever datasets are deleted: one dataset or many. Data.delete() uses it too.

    First the database records are deleted. Then the files are deleted.
    Why: a bulk delete (queryset.delete()) does not call Data.delete(), so the files would stay in storage.
    With this class, one delete and a bulk delete work the same way.
    """

    def __init__(self, datasets):
        """`datasets`: the datasets to delete (a queryset of Data)."""
        # Read the ids now and keep them.
        self.data_ids = list(datasets.values_list('id', flat=True))

    def files(self):
        """Returns the names of the files to delete. Datasets without a file are skipped."""
        file_names = Data.objects.filter(id__in=self.data_ids).values_list('data_file', flat=True)
        return [name for name in file_names if name]

    def delete(self):
        """Deletes the database records first, then the files."""
        # Get the file names now. After the records are deleted, we can't read them anymore.
        file_names = self.files()

        # Everything inside this block is deleted together. If one step fails, nothing is deleted.
        with transaction.atomic():
            # A queryset delete never calls Data.delete(), so it does not come back to this class
            Data.objects.filter(id__in=self.data_ids).delete()

            # Delete the files only after the records are really deleted.
            # robust=True: if deleting the files fails, we log the error and the delete still succeeds.
            transaction.on_commit(lambda: self._delete_files(file_names), robust=True)

    def _delete_files(self, file_names):
        """
        Deletes the files from storage, and logs one report at the end.
        If one file fails, we add it to the report and continue with the other files.
        `file_names`: the names of the files to delete (see files()).
        """
        storage = Data._meta.get_field('data_file').storage
        failed_files = []
        for file_name in file_names:
            try:
                storage.delete(file_name)
            except Exception as e:
                failed_files.append(f"Failed to delete {file_name}: {e}")

        # We build the whole report first and log it once at the end,
        # so it is not mixed with other logs
        deleted_count = len(file_names) - len(failed_files)
        failed_text = f", {len(failed_files)} failed" if failed_files else ""
        report = [
            "=" * 80,
            f"Deleting files of datasets {self.data_ids}",
            f"{deleted_count} of {len(file_names)} deleted{failed_text}",
        ]
        # Then one line for each file that failed
        report.extend(f"    {failed_file}" for failed_file in failed_files)
        report.append("=" * 80)

        # Logged as an error if any file failed, so it is easy to find
        log = logger.error if failed_files else logger.info
        log("\n" + "\n".join(report))
