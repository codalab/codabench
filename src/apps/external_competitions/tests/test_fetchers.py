from unittest import mock

from django.test import TestCase
from requests.exceptions import HTTPError

from external_competitions.fetchers.codabench_fetcher import fetch_codabench_competitions
from external_competitions.fetchers.codalab_fetcher import fetch_codalab_competitions
from external_competitions.fetchers.exceptions import PartialFetchError
from factories import ExternalPlatformFactory


def _mock_response(json_data, raise_for_status=None):
    """
    Builds a fake requests.Response standing in for `requests.get(...)`'s return
    value, so tests can control its .json() body without any real HTTP call.
    Pass an exception as raise_for_status to simulate an HTTP error response,
    e.g. HTTPError('500 Server Error') for a failed request - .raise_for_status()
    will then raise that exception, just like the real requests library does.
    """
    response = mock.Mock()
    response.json.return_value = json_data
    if raise_for_status is not None:
        response.raise_for_status.side_effect = raise_for_status
    return response


class FetchCodabenchCompetitionsTests(TestCase):
    def setUp(self):
        self.platform = ExternalPlatformFactory(
            competitions_fetch_url='https://codabench.example.org/api/competitions/public/',
            competition_base_url='https://codabench.example.org/competitions',
        )

    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_single_page(self, mock_get):
        """
        Fetches a single unpaginated page and checks each item is mapped to the
        right fields, including the competition_url built from the base url and id.
        """
        mock_get.return_value = _mock_response({
            'next': None,
            'results': [{
                'id': 42,
                'title': 'Iris',
                'description': 'The well known Iris dataset',
                'logo': 'https://codabench.example.org/logo.png',
                'owner_display_name': 'Jane Doe',
                'created_when': '2026-01-01T00:00:00Z',
            }],
        })

        result = fetch_codabench_competitions(self.platform)

        self.assertEqual(result, [{
            'name': 'Iris',
            'description': 'The well known Iris dataset',
            'image_url': 'https://codabench.example.org/logo.png',
            'organizer_name': 'Jane Doe',
            'competition_url': 'https://codabench.example.org/competitions/42/',
            'competition_created_when': '2026-01-01T00:00:00Z',
            'competition_started_when': None,
        }])
        # Separately from checking the output above, confirm requests.get was actually
        # called with the right URL and page=1, and only once. mock.ANY matches any
        # value - we don't care about the exact timeout, just that one was passed.
        mock_get.assert_called_once_with(
            self.platform.competitions_fetch_url, params={'page': 1}, timeout=mock.ANY
        )

    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_strips_query_params_from_logo_url(self, mock_get):
        """
        Fetches an item whose logo url has query params (like a presigned MinIO
        link) and checks everything after the "?" is stripped from image_url.
        """
        mock_get.return_value = _mock_response({
            'next': None,
            'results': [{
                'id': 1,
                'title': 'Comp',
                'logo': 'https://minio.example.org/logo.png?X-Amz-Signature=abc&X-Amz-Expires=3600',
            }],
        })

        result = fetch_codabench_competitions(self.platform)

        self.assertEqual(result[0]['image_url'], 'https://minio.example.org/logo.png')

    # Two things get mocked here because the function under test touches two real
    # dependencies when paginating: requests.get (so we control the fake responses)
    # and time.sleep (so the test doesn't actually wait 10 real seconds). Decorators
    # apply bottom-up but their mocks are injected top-down, so the parameter order
    # below matches: requests.get (closest decorator) -> mock_get, time.sleep -> mock_sleep.
    @mock.patch('external_competitions.fetchers.codabench_fetcher.time.sleep')
    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_follows_pagination_and_sleeps_between_pages(self, mock_get, mock_sleep):
        """
        Fetches two pages linked by "next" and checks both pages' results are
        combined into one list, with exactly one sleep call between the requests.
        """
        # side_effect as a list makes the mock return a different value on each
        # successive call: the 1st call to requests.get(...) returns the page 1
        # response, the 2nd call returns page 2. (return_value can only ever give
        # back one fixed answer, which won't work once there's more than one call.)
        mock_get.side_effect = [
            _mock_response({
                'next': 'https://codabench.example.org/api/competitions/public/?page=2',
                'results': [{'id': 1, 'title': 'Comp 1'}],
            }),
            _mock_response({
                'next': None,
                'results': [{'id': 2, 'title': 'Comp 2'}],
            }),
        ]

        result = fetch_codabench_competitions(self.platform)

        # result is one flat list from the single function call - seeing both
        # 'Comp 1' (page 1) and 'Comp 2' (page 2) here proves they were combined.
        self.assertEqual([c['name'] for c in result], ['Comp 1', 'Comp 2'])
        # call_args_list is the full history of calls made to the mock, in order.
        # This proves the function paged itself via page=1, page=2 on the same
        # fetch url - it only reads "next" to know whether to keep going, it
        # doesn't follow it as a URL.
        self.assertEqual(mock_get.call_args_list, [
            mock.call(self.platform.competitions_fetch_url, params={'page': 1}, timeout=mock.ANY),
            mock.call(self.platform.competitions_fetch_url, params={'page': 2}, timeout=mock.ANY),
        ])
        mock_sleep.assert_called_once()

    @mock.patch('external_competitions.fetchers.codabench_fetcher.time.sleep')
    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_does_not_sleep_after_last_page(self, mock_get, mock_sleep):
        """
        Fetches a single page with no "next" link and checks sleep is never
        called, since there's no next request to throttle before.
        """
        mock_get.return_value = _mock_response({'next': None, 'results': []})

        fetch_codabench_competitions(self.platform)

        mock_sleep.assert_not_called()

    @mock.patch('external_competitions.fetchers.codabench_fetcher.time.sleep')
    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_stops_at_max_pages(self, mock_get, mock_sleep):
        """
        Simulates a "next" link that never runs out (e.g. a broken or malicious
        platform) and checks the loop stops after MAX_PAGES requests, not forever.
        """
        # Every page "returns" the same response, whose 'next' never becomes falsy -
        # so nothing here ever ends the loop naturally. The only thing that can stop
        # it is the fetcher's own MAX_PAGES cap.
        mock_get.return_value = _mock_response({
            'next': 'https://codabench.example.org/api/competitions/public/?page=999',
            'results': [{'id': 1, 'title': 'Comp'}],
        })

        result = fetch_codabench_competitions(self.platform)

        self.assertEqual(mock_get.call_count, 100)
        self.assertEqual(len(result), 100)
        # 'next' never goes falsy, so sleep is called after every page too - 100 times.
        self.assertEqual(mock_sleep.call_count, 100)

    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_http_error_propagates(self, mock_get):
        """
        Fails the very first page's request and checks the original HTTPError
        propagates as-is, since there's no earlier page data to salvage.
        """
        mock_get.return_value = _mock_response({}, raise_for_status=HTTPError('500 Server Error'))

        with self.assertRaises(HTTPError):
            fetch_codabench_competitions(self.platform)

    @mock.patch('external_competitions.fetchers.codabench_fetcher.time.sleep')
    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_partial_fetch_error_when_later_page_fails(self, mock_get, mock_sleep):
        """
        Succeeds on page 1 then fails on page 2, and checks a PartialFetchError is
        raised carrying page 1's results plus the original error that caused it.
        """
        page_two_url = 'https://codabench.example.org/api/competitions/public/?page=2'
        error = HTTPError('500 Server Error')
        # Same side_effect-list trick as the pagination test: 1st call succeeds
        # (page 1), 2nd call's raise_for_status() raises our error (page 2 fails).
        mock_get.side_effect = [
            _mock_response({
                'next': page_two_url,
                'results': [{'id': 1, 'title': 'Comp 1'}],
            }),
            _mock_response({}, raise_for_status=error),
        ]

        # assertRaises as a context manager gives us `cm.exception` afterwards - the
        # actual exception instance that was raised, so we can inspect its attributes.
        with self.assertRaises(PartialFetchError) as cm:
            fetch_codabench_competitions(self.platform)

        self.assertEqual([c['name'] for c in cm.exception.competitions], ['Comp 1'])
        self.assertIs(cm.exception.original_exception, error)

    @mock.patch('external_competitions.fetchers.codabench_fetcher.requests.get')
    def test_empty_results(self, mock_get):
        """
        Fetches a page with an empty "results" list and checks the function
        returns an empty list instead of erroring.
        """
        mock_get.return_value = _mock_response({'next': None, 'results': []})

        self.assertEqual(fetch_codabench_competitions(self.platform), [])


class FetchCodalabCompetitionsTests(TestCase):
    def setUp(self):
        self.platform = ExternalPlatformFactory(
            competitions_fetch_url='https://codalab.example.org/api/competition/',
            competition_base_url='https://codalab.example.org/competitions',
        )

    @mock.patch('external_competitions.fetchers.codalab_fetcher.requests.get')
    def test_flat_list_response(self, mock_get):
        """
        Fetches CodaLab's flat (non-paginated) list response and checks each item
        is mapped to the right fields, with organizer_name and created_when unset.
        """
        mock_get.return_value = _mock_response([{
            'id': 7,
            'title': 'Vision Challenge',
            'description': 'A challenge',
            'image': 'https://codalab.example.org/logo.png',
            'start_date': '2026-02-01T00:00:00Z',
        }])

        result = fetch_codalab_competitions(self.platform)

        self.assertEqual(result, [{
            'name': 'Vision Challenge',
            'description': 'A challenge',
            'image_url': 'https://codalab.example.org/logo.png',
            'organizer_name': '',
            'competition_url': 'https://codalab.example.org/competitions/7',
            'competition_created_when': None,
            'competition_started_when': '2026-02-01T00:00:00Z',
        }])
        mock_get.assert_called_once_with(self.platform.competitions_fetch_url, timeout=mock.ANY)

    @mock.patch('external_competitions.fetchers.codalab_fetcher.requests.get')
    def test_empty_list(self, mock_get):
        """
        Fetches an empty list response and checks the function returns an empty
        list instead of erroring.
        """
        mock_get.return_value = _mock_response([])

        self.assertEqual(fetch_codalab_competitions(self.platform), [])

    @mock.patch('external_competitions.fetchers.codalab_fetcher.requests.get')
    def test_http_error_propagates(self, mock_get):
        """
        Fails the request and checks the original HTTPError propagates as-is,
        since CodaLab's fetch is a single request with nothing to salvage.
        """
        mock_get.return_value = _mock_response([], raise_for_status=HTTPError('500 Server Error'))

        with self.assertRaises(HTTPError):
            fetch_codalab_competitions(self.platform)
