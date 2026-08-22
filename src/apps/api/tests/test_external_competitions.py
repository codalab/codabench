import importlib

from django.test import TestCase, override_settings
from django.urls import clear_url_caches
from rest_framework.test import APIClient

from external_competitions.models import ExternalPlatform
from factories import ExternalCompetitionFactory, ExternalPlatformFactory


def _reload_api_urls():
    # api/urls.py only adds the external_competitions paths to urlpatterns when
    # it first runs, based on the setting's value at that moment. To pick up a
    # changed setting, we need Django to re-run that file - reloading the module
    # does that. But reloading api.urls by itself isn't enough: the root urls.py
    # did `path('api/', include('api.urls'))`, and that include() already built a
    # URLResolver object which cached the old urlpatterns list from api.urls the
    # first time it ran. So we also reload the root urls module, which re-runs
    # include('api.urls') and builds a fresh resolver pointing at the new list.
    # clear_url_caches() then drops Django's cached lookup of the whole urlconf,
    # so the next request resolves routes against these freshly reloaded modules.
    import api.urls
    importlib.reload(api.urls)
    import urls
    importlib.reload(urls)
    clear_url_caches()


class ExternalCompetitionsApiFunctionalTests(TestCase):
    """
    Covers the endpoints' behavior with the feature flag on. `api/urls.py` only
    registers these paths at import time when EXTERNAL_COMPETITIONS_ENABLED is True,
    so the flag is forced on and the urlconf reloaded for the lifetime of this class.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # override_settings only patches the setting value - it doesn't touch
        # api/urls.py's already-built urlpatterns, since those were compiled once
        # at import time (before any test ran). We store the override on cls (not
        # self) because setUpClass/tearDownClass are classmethods that run once for
        # the whole class, outside of any test instance, and both need to reference
        # the same override object to enable/disable it.
        cls._settings_override = override_settings(EXTERNAL_COMPETITIONS_ENABLED=True)
        cls._settings_override.enable()
        # Force api/urls.py (and the root urlconf that includes it) to re-run now
        # that the setting is True, so these endpoints actually get registered.
        _reload_api_urls()

    @classmethod
    def tearDownClass(cls):
        cls._settings_override.disable()
        # Reload again with the real setting restored, so api.urls doesn't leak
        # the forced-True urlpatterns into whatever test module runs next.
        _reload_api_urls()
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()

        self.codabench_platform = ExternalPlatformFactory(
            name='Some Codabench',
            platform_type=ExternalPlatform.PLATFORM_TYPE_CODABENCH,
        )
        self.codalab_platform = ExternalPlatformFactory(
            name='Some CodaLab',
            platform_type=ExternalPlatform.PLATFORM_TYPE_CODALAB,
        )
        self.inactive_platform = ExternalPlatformFactory(
            name='Inactive Platform',
            platform_type=ExternalPlatform.PLATFORM_TYPE_CODABENCH,
            is_active=False,
        )

        self.competition1 = ExternalCompetitionFactory(
            platform=self.codabench_platform,
            name='AI Challenge',
            description='An AI competition',
            organizer_name='Jane Doe',
        )
        self.competition2 = ExternalCompetitionFactory(
            platform=self.codalab_platform,
            name='Vision Contest',
        )
        self.inactive_platform_competition = ExternalCompetitionFactory(
            platform=self.inactive_platform,
            name='Old Contest',
        )

    def test_list_returns_expected_fields(self):
        """
        Calls the list endpoint and checks the response is a 200 containing one
        of the competitions we created, with every field holding the right value.
        """
        response = self.client.get('/api/external_competitions/')

        self.assertEqual(response.status_code, 200)
        result = next(r for r in response.data['results'] if r['id'] == self.competition1.id)
        self.assertEqual(result['name'], 'AI Challenge')
        self.assertEqual(result['description'], 'An AI competition')
        self.assertEqual(result['organizer_name'], 'Jane Doe')
        self.assertEqual(result['competition_url'], self.competition1.competition_url)
        self.assertEqual(result['platform'], self.codabench_platform.id)
        self.assertEqual(result['platform_name'], 'Some Codabench')
        self.assertEqual(result['platform_type'], ExternalPlatform.PLATFORM_TYPE_CODABENCH)
        self.assertIn('image_url', result)
        self.assertIn('competition_created_when', result)
        self.assertIn('competition_started_when', result)

    def test_list_pagination_shape(self):
        """
        Calls the list endpoint and checks the response has the pagination fields
        (count, next, previous, page_size, results), not just a plain list.
        """
        response = self.client.get('/api/external_competitions/')

        self.assertEqual(response.status_code, 200)
        for key in ('count', 'next', 'previous', 'page_size', 'results'):
            self.assertIn(key, response.data)

    def test_search_filter(self):
        """
        Searches for "vision" and checks only the competition matching that term
        comes back in the results, and the other competition is left out.
        """
        response = self.client.get('/api/external_competitions/?search=vision')

        self.assertEqual(response.status_code, 200)
        ids = [r['id'] for r in response.data['results']]
        self.assertIn(self.competition2.id, ids)
        self.assertNotIn(self.competition1.id, ids)

    def test_platform_filter(self):
        """
        Filters by one platform's id and checks only that platform's competition
        comes back, while the other platform's competition is left out.
        """
        response = self.client.get(f'/api/external_competitions/?platform={self.codabench_platform.id}')

        self.assertEqual(response.status_code, 200)
        ids = [r['id'] for r in response.data['results']]
        self.assertIn(self.competition1.id, ids)
        self.assertNotIn(self.competition2.id, ids)

    def test_platform_filter_accepts_comma_separated_ids(self):
        """
        Filters by both platforms' ids joined with a comma, and checks that both
        platforms' competitions come back in the results.
        """
        response = self.client.get(
            f'/api/external_competitions/?platform={self.codabench_platform.id},{self.codalab_platform.id}'
        )

        self.assertEqual(response.status_code, 200)
        ids = [r['id'] for r in response.data['results']]
        self.assertIn(self.competition1.id, ids)
        self.assertIn(self.competition2.id, ids)

    def test_competitions_from_inactive_platform_still_listed(self):
        """
        Checks that a competition from a deactivated platform still shows up in
        the list - being inactive only skips future fetches, not visibility.
        """
        response = self.client.get('/api/external_competitions/')

        self.assertEqual(response.status_code, 200)
        ids = [r['id'] for r in response.data['results']]
        self.assertIn(self.inactive_platform_competition.id, ids)

    def test_platforms_endpoint_returns_all_platforms_unpaginated(self):
        """
        Calls the platforms endpoint and checks it returns every platform, active
        or not, as a plain list (no pagination), sorted alphabetically by name.
        """
        response = self.client.get('/api/external_competitions/platforms/')

        self.assertEqual(response.status_code, 200)
        names = [p['name'] for p in response.data]
        self.assertIn('Some Codabench', names)
        self.assertIn('Some CodaLab', names)
        self.assertIn('Inactive Platform', names)
        self.assertEqual(names, sorted(names))


class ExternalCompetitionsUrlGatingTests(TestCase):
    """
    Covers that the endpoints only exist when EXTERNAL_COMPETITIONS_ENABLED is True,
    isolated from the functional tests above so each test controls its own flag state.
    """

    def setUp(self):
        self.client = APIClient()

    def tearDown(self):
        # Restore api.urls to match the real (non-overridden) settings, so later
        # test modules in the same run aren't affected by our reloads.
        _reload_api_urls()

    def test_urls_return_404_when_disabled(self):
        with override_settings(EXTERNAL_COMPETITIONS_ENABLED=False):
            _reload_api_urls()

            self.assertEqual(self.client.get('/api/external_competitions/').status_code, 404)
            self.assertEqual(self.client.get('/api/external_competitions/platforms/').status_code, 404)

    def test_urls_return_200_when_enabled(self):
        with override_settings(EXTERNAL_COMPETITIONS_ENABLED=True):
            _reload_api_urls()

            self.assertEqual(self.client.get('/api/external_competitions/').status_code, 200)
            self.assertEqual(self.client.get('/api/external_competitions/platforms/').status_code, 200)
