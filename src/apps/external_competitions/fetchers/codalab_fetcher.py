import requests

REQUEST_TIMEOUT = 300  # seconds - the CodaLab list endpoint returns every competition in one
# unpaginated response (no `next`/`results` wrapper, no page/limit params), so this single
# request can be very large and slow.


def fetch_codalab_competitions(platform):
    """
    Fetch competitions from a CodaLab instance's competitions API
    (`platform.competitions_fetch_url`, e.g. .../api/competition/). Unlike Codabench,
    this endpoint returns a single flat JSON array with no pagination and no
    organizer display name (only a numeric `creator` user id), so `organizer_name`
    is left blank here. It also has no creation-date field - only `start_date`
    (mapped to competition_started_when) and `last_modified` - so
    competition_created_when is left blank rather than mapped to something that
    means a different thing.
    """
    response = requests.get(platform.competitions_fetch_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    items = response.json()

    return [
        {
            'name': item.get('title', ''),
            'description': item.get('description') or '',
            'image_url': item.get('image') or '',
            'organizer_name': '',
            'competition_url': f"{platform.competition_base_url.rstrip('/')}/{item['id']}",
            'competition_created_when': None,
            'competition_started_when': item.get('start_date'),
        }
        for item in items
    ]
