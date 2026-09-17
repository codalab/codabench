# Named tasks.py (not fetch_sync.py) on purpose: celery_config.py's
# autodiscover_tasks() only auto-imports each app's `tasks.py` module, so a
# differently-named module here would never get imported, its @app.task
# would never register, and celery beat's scheduled calls would fail with
# NotRegistered.
import logging

from django.conf import settings
from django.utils.timezone import now

from celery_config import app
from external_competitions.fetchers import FETCHERS
from external_competitions.fetchers.exceptions import PartialFetchError
from external_competitions.models import ExternalCompetition, ExternalFetchLog, ExternalPlatform

logger = logging.getLogger(__name__)


@app.task(queue="site-worker")
def fetch_external_competitions():
    if not settings.EXTERNAL_COMPETITIONS_ENABLED:
        logger.info("External competitions feature is disabled, skipping fetch")
        return

    logger.info("External competitions fetch started")

    platforms = ExternalPlatform.objects.filter(is_active=True)
    if not platforms:
        logger.info("No active external platforms to fetch")
        return

    for platform in platforms:
        sync_platform(platform)

    logger.info("External competitions fetch ended")


def sync_platform(platform):
    logger.info(f"Fetching competitions for platform '{platform.name}'")
    log = ExternalFetchLog.objects.create(platform=platform)

    try:
        fetcher = FETCHERS.get(platform.platform_type)
        if fetcher is None:
            raise ValueError(f"No fetcher implemented for platform type '{platform.platform_type}'")

        partial_error = None
        try:
            fetched_competitions = fetcher(platform)
        except PartialFetchError as e:
            fetched_competitions = e.competitions
            partial_error = str(e.original_exception)

        fetched_urls = set()
        new_count = 0
        updated_count = 0
        for competition_data in fetched_competitions:
            competition_url = competition_data['competition_url']
            fetched_urls.add(competition_url)
            defaults = {key: value for key, value in competition_data.items() if key != 'competition_url'}
            defaults['platform'] = platform
            _, created = ExternalCompetition.objects.update_or_create(
                competition_url=competition_url,
                defaults=defaults,
            )
            if created:
                new_count += 1
            else:
                updated_count += 1

        if partial_error:
            # We don't have the full picture of what's currently live on the
            # platform, so we can't tell which existing rows are actually stale -
            # skip the delete step rather than risk dropping valid competitions
            # from the pages we didn't get to.
            deleted_count = 0
        else:
            # Diff-based sync: anything for this platform that wasn't in this fetch is gone from the source, so drop it
            deleted_count, _ = ExternalCompetition.objects.filter(platform=platform).exclude(
                competition_url__in=fetched_urls
            ).delete()

        log.status = ExternalFetchLog.STATUS_PARTIAL_SUCCESS if partial_error else ExternalFetchLog.STATUS_SUCCESS
        log.total_fetched = len(fetched_urls)
        log.new_count = new_count
        log.updated_count = updated_count
        log.deleted_count = deleted_count
        log.error_message = partial_error or ''
        log.finished_at = now()
        log.save()
        logger.info(f"Finished fetching platform '{platform.name}'" + (" (partial success)" if partial_error else ""))
    except Exception as e:
        logger.exception(f"Failed to fetch competitions for platform '{platform.name}'")
        log.status = ExternalFetchLog.STATUS_FAILURE
        log.error_message = str(e)
        log.finished_at = now()
        log.save()
