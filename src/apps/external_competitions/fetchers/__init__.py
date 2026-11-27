from external_competitions.fetchers.codabench_fetcher import fetch_codabench_competitions
from external_competitions.fetchers.codalab_fetcher import fetch_codalab_competitions
from external_competitions.models import ExternalPlatform

FETCHERS = {
    ExternalPlatform.PLATFORM_TYPE_CODABENCH: fetch_codabench_competitions,
    ExternalPlatform.PLATFORM_TYPE_CODALAB: fetch_codalab_competitions,
}
