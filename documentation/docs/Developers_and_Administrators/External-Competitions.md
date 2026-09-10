External Competitions lets a Codabench instance show a browsable list of public competitions hosted on *other* Codabench and CodaLab instances, fetched and synced automatically once a day. It's off by default and intended for the main `codabench.org` instance rather than self-hosted deployments.

## For Codabench administrators

### Enabling the feature

Set the following in your `.env` file:

```
EXTERNAL_COMPETITIONS_ENABLED=True
```

This turns on the External Competitions page, a banner/link to it on the public benchmarks and competitions page, the two read-only API endpoints, and the daily Celery beat task that fetches and syncs competitions. Leaving it `False` (the default) disables all of it - the API endpoints return a 404, and the page and the banner linking to it aren't shown.

### Adding a platform to sync from

Platforms are managed from the Django admin, under **External Competitions -> External platforms -> Add**. Each platform needs:

| Field | Description |
|---|---|
| Name | Display name shown on the competition tiles (e.g. "Codabench @ LISN") |
| Platform type | `Codabench instance` or `CodaLab instance` |
| Competitions fetch URL | The API endpoint to get that platform's list of public competitions |
| Competition base URL | The base URL used to create complete link for each competition |
| Active | Unchecking this skips the platform in the daily fetch (already-synced competitions stay visible - see note below) |

Once saved, the platform is picked up by the next scheduled fetch (or trigger one manually, see below).

### How the sync works

`fetch_external_competitions` (`src/apps/external_competitions/tasks.py`) runs once a day via Celery beat. For each active platform it calls the fetcher matching its platform type (`codabench_fetcher.py` or `codalab_fetcher.py`) and then diffs the result against what's already stored:

- Competitions present in the fetch are created or updated (matched by `competition_url`).
- Competitions no longer present in the fetch are deleted.

Each run writes an `ExternalFetchLog` entry (visible in the admin) recording the outcome (`SUCCESS`/`FAILURE`), counts (`new_count`/`updated_count`/`deleted_count`), and, on failure, an error message - check there first if a platform's competitions look stale or missing.

!!! note
    Deactivating a platform (`is_active=False`) only stops it from being fetched going forward - competitions already synced from it stay visible on the public list until manually removed.

To trigger a fetch immediately instead of waiting for the daily schedule:

```bash
docker compose exec django ./manage.py shell -c "from external_competitions.tasks import fetch_external_competitions; fetch_external_competitions()"
```

## For platform administrators

If you run your own Codabench or CodaLab instance and would like your public competitions to be discoverable on `codabench.org`'s External Competitions page, you can request to be added.

### Registering your platform

Send an email to **info@codabench.org** with the subject **"Platform Registration for External Competitions"**, including:

- **Your platform's name and type** (Codabench, CodaLab instance, or other).
- **Your competitions fetch URL** - the API endpoint we'll use once a day to retrieve your list of public competitions (for example, a Codabench instance's `.../api/competitions/public/`). This endpoint must be publicly reachable without authentication, since the fetch runs unattended.
- **Your competition base URL** - the base URL used to build the link back to each competition on your site, so visitors clicking a competition on `codabench.org` land on the right page on yours.

Please share as much detail as you can, **especially about the fetch URL** - pagination behavior, response format, expected size of the response, rate limits, or anything else likely to affect an automated daily fetch. The more we know upfront, the more reliably we can keep your competitions in sync.

### Unregistering your platform

To have your platform's competitions removed or paused, email **info@codabench.org** asking us to deactivate (or delete) fetching for your platform, including your platform's name and/or URL so we can identify it.
