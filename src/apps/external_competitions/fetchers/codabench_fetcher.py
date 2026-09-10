import time

import requests

from external_competitions.fetchers.exceptions import PartialFetchError

REQUEST_TIMEOUT = 30  # seconds
MAX_PAGES = 100  # safety cap so a misbehaving/malicious platform can't loop us forever
PAGE_FETCH_DELAY = 10  # seconds - throttle between page requests so we don't hammer the platform


def fetch_codabench_competitions(platform):
    """
    Fetch competitions from a Codabench instance's public competitions API
    (`platform.competitions_fetch_url`, e.g. .../api/competitions/public/), following
    DRF-style pagination (`next`/`results`), and normalize them to the fields
    ExternalCompetition needs.
    """
    competitions = []
    page = 1

    for _ in range(MAX_PAGES):
        try:
            # We drive pagination ourselves with a `page` query param, rather than
            # requesting the URL `next` points to - some platforms return a `next`
            # link built for their own domain/scheme (e.g. behind a proxy), which
            # isn't safe to follow as-is. We only use `next` below to tell whether
            # another page exists.
            response = requests.get(
                platform.competitions_fetch_url, params={'page': page}, timeout=REQUEST_TIMEOUT
            )
            # Raises HTTPError on a 4xx/5xx response, instead of silently continuing to
            # parse an error page's body as JSON below.
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            # If earlier pages already succeeded, hand those back instead of losing
            # them - sync_platform() saves them as a partial success. A failure on
            # the very first page has nothing to salvage, so it just propagates and
            # is logged as a full FAILURE there.
            if competitions:
                raise PartialFetchError(competitions, e) from e
            raise

        for item in data.get('results', []):
            competitions.append({
                'name': item.get('title', ''),
                'description': item.get('description') or '',
                'image_url': (item.get('logo') or '').split('?')[0],
                'organizer_name': item.get('owner_display_name') or item.get('created_by') or '',
                'competition_url': f"{platform.competition_base_url.rstrip('/')}/{item['id']}/",
                'competition_created_when': item.get('created_when'),
                # TODO: Not available on this API yet - fill in once it exposes a start date
                'competition_started_when': None,
            })

        if not data.get('next'):
            break
        page += 1
        time.sleep(PAGE_FETCH_DELAY)

    return competitions
