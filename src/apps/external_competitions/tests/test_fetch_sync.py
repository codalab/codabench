from unittest import mock

from django.test import TestCase, override_settings

from external_competitions.tasks import fetch_external_competitions, sync_platform
from external_competitions.fetchers.exceptions import PartialFetchError
from external_competitions.models import ExternalCompetition, ExternalFetchLog, ExternalPlatform
from factories import ExternalCompetitionFactory, ExternalPlatformFactory


def _competition_data(n, **overrides):
    """
    Builds one fake fetched-competition dict, in the shape a fetcher would hand
    back to sync_platform. `n` makes name/competition_url unique per call (so
    e.g. _competition_data(1) and _competition_data(2) don't collide), and any
    keyword args in **overrides replace just those fields, e.g.
    _competition_data(1, name='New Name') keeps every other default as-is.
    """
    data = {
        'name': f'Competition {n}',
        'description': '',
        'image_url': '',
        'organizer_name': '',
        'competition_url': f'https://example.org/competitions/{n}/',
        'competition_created_when': None,
        'competition_started_when': None,
    }
    data.update(overrides)
    return data


class SyncPlatformTests(TestCase):
    def setUp(self):
        self.platform = ExternalPlatformFactory(platform_type=ExternalPlatform.PLATFORM_TYPE_CODABENCH)

    def _sync_with(self, fetched_data):
        """
        Runs sync_platform() for self.platform as if a fetcher had returned
        fetched_data, without any real HTTP call. Swaps the real FETCHERS entry
        for this platform's type with a fake fetcher that just returns
        fetched_data, only for the duration of the `with` block.
        """
        fetcher = mock.Mock(return_value=fetched_data)
        with mock.patch.dict('external_competitions.tasks.FETCHERS', {self.platform.platform_type: fetcher}):
            sync_platform(self.platform)
        return fetcher

    def test_creates_new_competitions_on_first_fetch(self):
        """
        Syncs a platform with no existing competitions and checks a row is
        created for each fetched item, logged as a success with new_count set.
        """
        self._sync_with([_competition_data(1), _competition_data(2)])

        self.assertEqual(ExternalCompetition.objects.filter(platform=self.platform).count(), 2)
        log = ExternalFetchLog.objects.get(platform=self.platform)
        self.assertEqual(log.status, ExternalFetchLog.STATUS_SUCCESS)
        self.assertEqual(log.total_fetched, 2)
        self.assertEqual(log.new_count, 2)
        self.assertEqual(log.updated_count, 0)
        self.assertEqual(log.deleted_count, 0)
        self.assertIsNotNone(log.finished_at)

    def test_refetching_identical_data_updates_not_recreates(self):
        """
        Syncs the same platform twice with unchanged data and checks the second
        sync updates the existing rows in place (same ids) instead of duplicating them.
        """
        self._sync_with([_competition_data(1), _competition_data(2)])
        ids_before = set(ExternalCompetition.objects.filter(platform=self.platform).values_list('id', flat=True))

        self._sync_with([_competition_data(1), _competition_data(2)])

        ids_after = set(ExternalCompetition.objects.filter(platform=self.platform).values_list('id', flat=True))
        self.assertEqual(ids_before, ids_after)
        log = ExternalFetchLog.objects.filter(platform=self.platform).latest('id')
        self.assertEqual(log.new_count, 0)
        self.assertEqual(log.updated_count, 2)
        self.assertEqual(log.deleted_count, 0)

    def test_missing_competition_is_deleted(self):
        """
        Syncs a platform, then re-syncs with one of the two competitions no
        longer in the fetched data, and checks that missing one gets deleted.
        """
        self._sync_with([_competition_data(1), _competition_data(2)])
        self._sync_with([_competition_data(1)])

        self.assertEqual(ExternalCompetition.objects.filter(platform=self.platform).count(), 1)
        log = ExternalFetchLog.objects.filter(platform=self.platform).latest('id')
        self.assertEqual(log.new_count, 0)
        self.assertEqual(log.updated_count, 1)
        self.assertEqual(log.deleted_count, 1)

    def test_changed_field_updates_existing_row(self):
        """
        Re-syncs the same competition_url with a changed name and checks the
        existing row's name is updated in place, without creating a duplicate.
        """
        self._sync_with([_competition_data(1, name='Old Name')])

        self._sync_with([_competition_data(1, name='New Name')])

        self.assertEqual(ExternalCompetition.objects.filter(platform=self.platform).count(), 1)
        competition = ExternalCompetition.objects.get(platform=self.platform)
        self.assertEqual(competition.name, 'New Name')
        log = ExternalFetchLog.objects.filter(platform=self.platform).latest('id')
        self.assertEqual(log.updated_count, 1)

    def test_unknown_platform_type_fails_gracefully(self):
        """
        Syncs a platform whose type has no matching entry in FETCHERS and checks
        it's logged as a failure with a "No fetcher implemented" message, no crash.
        """
        self.platform.platform_type = 'not_a_real_type'
        self.platform.save()

        sync_platform(self.platform)

        log = ExternalFetchLog.objects.get(platform=self.platform)
        self.assertEqual(log.status, ExternalFetchLog.STATUS_FAILURE)
        self.assertIn('No fetcher implemented', log.error_message)

    def test_fetcher_exception_fails_gracefully_without_partial_writes(self):
        """
        Makes the fetcher raise a plain exception and checks the sync is logged
        as a failure while existing competitions for that platform are left untouched.
        """
        ExternalCompetitionFactory(platform=self.platform, competition_url='https://example.org/competitions/1/')
        count_before = ExternalCompetition.objects.filter(platform=self.platform).count()

        fetcher = mock.Mock(side_effect=ConnectionError('unreachable'))
        with mock.patch.dict('external_competitions.tasks.FETCHERS', {self.platform.platform_type: fetcher}):
            sync_platform(self.platform)

        self.assertEqual(ExternalCompetition.objects.filter(platform=self.platform).count(), count_before)
        log = ExternalFetchLog.objects.get(platform=self.platform)
        self.assertEqual(log.status, ExternalFetchLog.STATUS_FAILURE)
        self.assertIn('unreachable', log.error_message)

    def test_partial_fetch_error_saves_partial_data_and_skips_delete(self):
        """
        Makes the fetcher raise PartialFetchError and checks the partial data is
        saved, an unrelated existing competition is kept (not wrongly deleted),
        and the log is marked PARTIAL_SUCCESS with the original error message.
        """
        # Pre-existing row for this platform, so we can check it survives a partial sync.
        stale = ExternalCompetitionFactory(
            platform=self.platform, competition_url='https://example.org/competitions/stale/'
        )

        # The fetcher's fetched data won't include `stale` above. On a full success
        # that would delete `stale` as no-longer-listed, but a partial one must not.
        fetcher = mock.Mock(side_effect=PartialFetchError([_competition_data(1)], ConnectionError('Connection refused')))
        with mock.patch.dict('external_competitions.tasks.FETCHERS', {self.platform.platform_type: fetcher}):
            sync_platform(self.platform)

        self.assertTrue(ExternalCompetition.objects.filter(platform=self.platform, id=stale.id).exists())
        self.assertTrue(
            ExternalCompetition.objects.filter(
                platform=self.platform, competition_url='https://example.org/competitions/1/'
            ).exists()
        )
        log = ExternalFetchLog.objects.get(platform=self.platform)
        self.assertEqual(log.status, ExternalFetchLog.STATUS_PARTIAL_SUCCESS)
        self.assertEqual(log.deleted_count, 0)
        self.assertEqual(log.error_message, 'Connection refused')


class FetchExternalCompetitionsTests(TestCase):
    @override_settings(EXTERNAL_COMPETITIONS_ENABLED=False)
    @mock.patch('external_competitions.tasks.sync_platform')
    def test_does_nothing_when_disabled(self, mock_sync_platform):
        """
        Runs the task with the feature flag off and checks sync_platform is never
        called, even though an active platform exists.
        """
        ExternalPlatformFactory(is_active=True)

        fetch_external_competitions()

        mock_sync_platform.assert_not_called()

    @override_settings(EXTERNAL_COMPETITIONS_ENABLED=True)
    @mock.patch('external_competitions.tasks.sync_platform')
    def test_does_nothing_when_no_platforms(self, mock_sync_platform):
        """
        Runs the task with the flag on but no ExternalPlatform rows at all, and
        checks it exits quietly without calling sync_platform or erroring.
        """
        fetch_external_competitions()

        mock_sync_platform.assert_not_called()

    @override_settings(EXTERNAL_COMPETITIONS_ENABLED=True)
    @mock.patch('external_competitions.tasks.sync_platform')
    def test_only_fetches_active_platforms(self, mock_sync_platform):
        """
        Creates one active and one inactive platform and checks sync_platform is
        called only for the active one.
        """
        active = ExternalPlatformFactory(is_active=True)
        ExternalPlatformFactory(is_active=False)

        fetch_external_competitions()

        mock_sync_platform.assert_called_once_with(active)

    @override_settings(EXTERNAL_COMPETITIONS_ENABLED=True)
    def test_one_platform_failing_does_not_stop_the_others(self):
        """
        Runs two platforms where one's fetcher raises an exception, and checks
        the other platform still syncs successfully instead of the loop aborting.
        """
        failing_platform = ExternalPlatformFactory(platform_type=ExternalPlatform.PLATFORM_TYPE_CODABENCH)
        healthy_platform = ExternalPlatformFactory(platform_type=ExternalPlatform.PLATFORM_TYPE_CODALAB)

        failing_fetcher = mock.Mock(side_effect=ConnectionError('unreachable'))
        healthy_fetcher = mock.Mock(return_value=[_competition_data(1)])
        fetchers = {
            ExternalPlatform.PLATFORM_TYPE_CODABENCH: failing_fetcher,
            ExternalPlatform.PLATFORM_TYPE_CODALAB: healthy_fetcher,
        }
        with mock.patch.dict('external_competitions.tasks.FETCHERS', fetchers):
            fetch_external_competitions()

        failing_log = ExternalFetchLog.objects.get(platform=failing_platform)
        healthy_log = ExternalFetchLog.objects.get(platform=healthy_platform)
        self.assertEqual(failing_log.status, ExternalFetchLog.STATUS_FAILURE)
        self.assertEqual(healthy_log.status, ExternalFetchLog.STATUS_SUCCESS)
