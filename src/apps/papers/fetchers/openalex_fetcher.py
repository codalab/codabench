import datetime

import requests

from papers.fetchers.exceptions import PartialFetchError

OPENALEX_API = "https://api.openalex.org"
USER_AGENT = "Codabench/1.0 (https://www.codabench.org)"
REQUEST_TIMEOUT = 20  # seconds
MAX_PAGES = 100  # safety cap so pagination cannot loop forever


def _extract_authors(work):
    names = [
        auth['author']['display_name'].strip()
        for auth in work.get('authorships', [])
        if auth.get('author') and auth['author'].get('display_name')
    ]
    return ', '.join(names)


def _extract_venue(work):
    # Prefer a journal or conference over a preprint repository (e.g. arXiv)
    for loc in work.get('locations') or []:
        source = (loc or {}).get('source') or {}
        if source.get('type') in ('journal', 'conference') and source.get('display_name'):
            return source['display_name']
    primary_source = ((work.get('primary_location') or {}).get('source') or {})
    return primary_source.get('display_name') or ''


def parse_openalex_work(work):
    title = (work.get('display_name') or '').strip()
    doi_url = (work.get('doi') or '').strip()
    doi = doi_url.removeprefix('https://doi.org/').strip().lower()
    # DOI is our unique key across sources, so we skip works that don't have one
    if not title or not doi:
        return None

    primary = work.get('primary_location') or {}
    best_oa = work.get('best_oa_location') or {}
    raw_date = work.get('publication_date')

    return {
        'doi': doi,
        'title': title,
        'authors': _extract_authors(work),
        'venue': _extract_venue(work),
        'publication_date': datetime.date.fromisoformat(raw_date[:10]) if raw_date else None,
        'citation_count': work.get('cited_by_count') or 0,
        'url': primary.get('landing_page_url') or doi_url,
        'pdf_url': best_oa.get('pdf_url') or primary.get('pdf_url') or '',
    }


def fetch_openalex_papers(doi):
    """
    Fetch all works citing the given DOI from the OpenAlex API using cursor
    pagination, and normalize them to the fields Paper needs.
    """
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})

    # Resolve the target DOI to its OpenAlex work ID so we can filter by cites:<id>
    clean_doi = doi.removeprefix('https://doi.org/').strip()
    resp = session.get(f"{OPENALEX_API}/works/https://doi.org/{clean_doi}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    target_id = resp.json()['id'].rsplit('/', 1)[-1]

    papers = []
    cursor = '*'
    for _ in range(MAX_PAGES):
        try:
            page_resp = session.get(
                f"{OPENALEX_API}/works",
                params={
                    'filter': f'cites:{target_id}',
                    'per-page': 200,
                    'cursor': cursor,
                    'sort': 'publication_date:desc',
                },
                timeout=REQUEST_TIMEOUT,
            )
            page_resp.raise_for_status()
            payload = page_resp.json()
        except Exception as e:
            # Salvage already-fetched pages instead of discarding them on a mid-sync failure
            if papers:
                raise PartialFetchError(papers, e) from e
            raise

        results = payload.get('results', [])
        for work in results:
            parsed = parse_openalex_work(work)
            if parsed:
                papers.append(parsed)

        next_cursor = payload.get('meta', {}).get('next_cursor')
        if not next_cursor or next_cursor == cursor or not results:
            break
        cursor = next_cursor

    return papers
