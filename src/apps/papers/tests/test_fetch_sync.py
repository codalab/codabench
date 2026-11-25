import datetime
from unittest import mock

from django.test import TestCase

from factories import PaperFactory
from papers.fetchers.exceptions import PartialFetchError
from papers.models import Paper
from papers.tasks import sync_citing_papers


def _paper_data(n, **overrides):
    data = {
        'doi': f'10.1000/paper.{n}',
        'title': f'Paper {n}',
        'authors': 'John Doe',
        'venue': 'ICML',
        'publication_date': datetime.date(2025, 1, 10),
        'citation_count': 5,
        'url': f'https://example.org/paper/{n}',
        'pdf_url': '',
    }
    data.update(overrides)
    return data


class SyncCitingPapersTests(TestCase):
    def _sync_with(self, fetcher_mock, skip_thumbnails=True):
        with mock.patch.dict('papers.tasks.FETCHERS', {'openalex': fetcher_mock}):
            return sync_citing_papers(source='openalex', skip_thumbnails=skip_thumbnails)

    def test_creates_papers_on_first_sync(self):
        stats = self._sync_with(mock.Mock(return_value=[_paper_data(1), _paper_data(2)]))

        self.assertEqual(Paper.objects.count(), 2)
        self.assertEqual(stats['created'], 2)
        self.assertEqual(stats['updated'], 0)
        self.assertIsNone(stats['partial_error'])

    def test_refetch_updates_only_when_fields_change(self):
        existing = PaperFactory(doi='10.1000/paper.1', citation_count=5)

        stats_changed = self._sync_with(mock.Mock(return_value=[_paper_data(1, citation_count=42)]))
        self.assertEqual(Paper.objects.count(), 1)
        self.assertEqual(stats_changed['created'], 0)
        self.assertEqual(stats_changed['updated'], 1)
        existing.refresh_from_db()
        self.assertEqual(existing.citation_count, 42)

        stats_same = self._sync_with(mock.Mock(return_value=[_paper_data(1, citation_count=42)]))
        self.assertEqual(stats_same['created'], 0)
        self.assertEqual(stats_same['updated'], 0)

    def test_partial_fetch_error_saves_salvaged_papers(self):
        """Papers fetched before a mid-sync failure are still persisted."""
        err = PartialFetchError([_paper_data(1)], RuntimeError('timeout'))
        stats = self._sync_with(mock.Mock(side_effect=err))

        self.assertEqual(Paper.objects.count(), 1)
        self.assertEqual(stats['created'], 1)
        self.assertEqual(stats['partial_error'], 'timeout')

    @mock.patch('papers.tasks.generate_pdf_thumbnail', return_value=None)
    def test_thumbnail_generation_respects_skip_flag(self, mock_thumb):
        data = [_paper_data(1, pdf_url='https://example.org/paper.pdf')]

        self._sync_with(mock.Mock(return_value=[dict(data[0])]), skip_thumbnails=True)
        mock_thumb.assert_not_called()

        self._sync_with(mock.Mock(return_value=[dict(data[0])]), skip_thumbnails=False)
        mock_thumb.assert_called_once_with('https://example.org/paper.pdf')

    def test_data_error_skips_bad_paper_and_continues(self):
        """A single paper exceeding a column max_length is skipped without aborting the sync."""
        bad = _paper_data(1, url='https://example.org/' + 'a' * 600)
        good = _paper_data(2)

        stats = self._sync_with(mock.Mock(return_value=[bad, good]))

        self.assertEqual(Paper.objects.count(), 1)
        self.assertEqual(Paper.objects.first().doi, '10.1000/paper.2')
        self.assertEqual(stats['created'], 1)

    def test_unknown_source_raises_value_error(self):
        with self.assertRaises(ValueError):
            sync_citing_papers(source='unknown', skip_thumbnails=True)
