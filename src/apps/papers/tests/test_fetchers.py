import datetime
from unittest import mock

from django.test import TestCase
from requests.exceptions import HTTPError

from papers.fetchers.exceptions import PartialFetchError
from papers.fetchers.openalex_fetcher import fetch_openalex_papers, parse_openalex_work
from papers.fetchers.thumbnails import generate_pdf_thumbnail


def _mock_response(json_data, raise_for_status=None):
    response = mock.Mock()
    response.json.return_value = json_data
    if raise_for_status is not None:
        response.raise_for_status.side_effect = raise_for_status
    return response


def _openalex_work(n, **overrides):
    work = {
        'id': f'https://openalex.org/W{n}',
        'display_name': f'Paper {n}',
        'publication_date': '2025-03-15',
        'cited_by_count': n * 10,
        'doi': f'https://doi.org/10.1234/paper.{n}',
        'authorships': [
            {'author': {'display_name': 'Alice Smith'}},
            {'author': {'display_name': 'Bob Jones'}},
        ],
        'primary_location': {
            'landing_page_url': f'https://example.org/paper/{n}',
            'pdf_url': f'https://example.org/paper/{n}.pdf',
            'source': {'display_name': 'arXiv (Cornell University)', 'type': 'repository'},
        },
        'locations': [],
    }
    work.update(overrides)
    return work


class FetchOpenAlexPapersTests(TestCase):
    def test_parse_openalex_work(self):
        parsed = parse_openalex_work(_openalex_work(1))
        self.assertEqual(parsed, {
            'doi': '10.1234/paper.1',
            'title': 'Paper 1',
            'authors': 'Alice Smith, Bob Jones',
            'venue': 'arXiv (Cornell University)',
            'publication_date': datetime.date(2025, 3, 15),
            'citation_count': 10,
            'url': 'https://example.org/paper/1',
            'pdf_url': 'https://example.org/paper/1.pdf',
        })

    def test_parse_prefers_journal_or_conference_venue(self):
        work = _openalex_work(
            1,
            locations=[
                {'source': {'display_name': 'arXiv (Cornell University)', 'type': 'repository'}},
                {'source': {'display_name': 'NeurIPS', 'type': 'conference'}},
            ],
        )
        self.assertEqual(parse_openalex_work(work)['venue'], 'NeurIPS')

    def test_parse_skips_work_without_doi_or_title(self):
        self.assertIsNone(parse_openalex_work(_openalex_work(1, doi='')))
        self.assertIsNone(parse_openalex_work(_openalex_work(1, display_name='   ')))

    @mock.patch('papers.fetchers.openalex_fetcher.requests.Session')
    def test_cursor_pagination(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            _mock_response({'id': 'https://openalex.org/W4283462007'}),
            _mock_response({'results': [_openalex_work(1)], 'meta': {'next_cursor': 'cursor-2'}}),
            _mock_response({'results': [_openalex_work(2)], 'meta': {'next_cursor': None}}),
        ]

        papers = fetch_openalex_papers('10.1016/j.patter.2022.100543')

        self.assertEqual([p['doi'] for p in papers], ['10.1234/paper.1', '10.1234/paper.2'])
        self.assertEqual(session.get.call_count, 3)

    @mock.patch('papers.fetchers.openalex_fetcher.requests.Session')
    def test_partial_fetch_error_salvages_earlier_pages(self, mock_session_cls):
        """A mid-pagination HTTP error raises PartialFetchError carrying already-fetched papers."""
        session = mock_session_cls.return_value
        session.get.side_effect = [
            _mock_response({'id': 'https://openalex.org/W4283462007'}),
            _mock_response({'results': [_openalex_work(1)], 'meta': {'next_cursor': 'cursor-2'}}),
            _mock_response({}, raise_for_status=HTTPError('503 Service Unavailable')),
        ]

        with self.assertRaises(PartialFetchError) as ctx:
            fetch_openalex_papers('10.1016/j.patter.2022.100543')

        self.assertEqual([p['doi'] for p in ctx.exception.papers], ['10.1234/paper.1'])
        self.assertIsInstance(ctx.exception.original_exception, HTTPError)

    @mock.patch('papers.fetchers.openalex_fetcher.requests.Session')
    def test_first_page_error_propagates(self, mock_session_cls):
        """A failure with nothing salvaged yet propagates the original exception."""
        session = mock_session_cls.return_value
        session.get.side_effect = [
            _mock_response({'id': 'https://openalex.org/W4283462007'}),
            _mock_response({}, raise_for_status=HTTPError('500 Server Error')),
        ]

        with self.assertRaises(HTTPError):
            fetch_openalex_papers('10.1016/j.patter.2022.100543')


class PdfThumbnailTests(TestCase):
    def test_rejects_non_http_urls(self):
        self.assertIsNone(generate_pdf_thumbnail(''))
        self.assertIsNone(generate_pdf_thumbnail('file:///etc/passwd'))

    @mock.patch('papers.fetchers.thumbnails.requests.get')
    def test_rejects_non_pdf_payload(self, mock_get):
        """HTML paywall/error pages returned with 200 OK must return None."""
        resp = mock.MagicMock()
        resp.__enter__.return_value = resp
        resp.iter_content.return_value = [b'<html>Login required</html>']
        mock_get.return_value = resp

        self.assertIsNone(generate_pdf_thumbnail('https://example.org/paper.pdf'))
