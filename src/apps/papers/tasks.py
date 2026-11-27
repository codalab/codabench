# Named tasks.py on purpose so Celery's autodiscover_tasks() registers @app.task
import logging

from django.db import DataError, transaction

from celery_config import app
from papers.fetchers import FETCHERS
from papers.fetchers.exceptions import PartialFetchError
from papers.fetchers.thumbnails import generate_pdf_thumbnail
from papers.models import Paper

logger = logging.getLogger(__name__)

CODABENCH_PAPER_DOI = '10.1016/j.patter.2022.100543'


@app.task(queue="site-worker")
def sync_citing_papers(source='openalex', skip_thumbnails=False):
    doi = CODABENCH_PAPER_DOI
    fetcher = FETCHERS.get(source)
    if fetcher is None:
        raise ValueError(f"No fetcher implemented for paper source '{source}'")

    logger.info(f"Hall of Papers sync started (source={source}, doi={doi})")

    partial_error = None
    try:
        fetched = fetcher(doi)
    except PartialFetchError as e:
        fetched = e.papers
        partial_error = str(e.original_exception)
        logger.warning(f"Partial fetch from '{source}' ({len(fetched)} papers salvaged): {partial_error}")

    created_count = 0
    updated_count = 0
    thumb_count = 0

    for item in fetched:
        # Match on normalized DOI so future sources deduplicate into the same row
        doi = item.pop('doi').strip().lower()
        try:
            # Savepoint ensures a Postgres DataError does not poison an outer transaction
            with transaction.atomic():
                paper = Paper.objects.filter(doi=doi).first()
                if paper is None:
                    paper = Paper.objects.create(doi=doi, **item)
                    created_count += 1
                else:
                    changed = [k for k, v in item.items() if getattr(paper, k) != v]
                    if changed:
                        for k in changed:
                            setattr(paper, k, item[k])
                        paper.save(update_fields=changed)
                        updated_count += 1
        except DataError as exc:
            logger.warning(f"Skipping paper {doi} (field exceeds max_length): {exc}")
            continue

        # Generated once per paper and saved in Django's default storage
        if not skip_thumbnails and not paper.thumbnail and paper.pdf_url:
            # Thumbnails are best-effort: an unexpected failure (odd PDF, PIL/WebP
            # encoding, storage backend) must not abort the sync of remaining papers
            try:
                thumb = generate_pdf_thumbnail(paper.pdf_url)
                if thumb is not None:
                    paper.thumbnail.save(f"{paper.id}.webp", thumb, save=True)
                    thumb_count += 1
            except Exception:
                logger.exception(f"Failed to generate thumbnail for paper {doi} ({paper.pdf_url})")

    logger.info(
        f"Hall of Papers sync finished: {len(fetched)} fetched "
        f"({created_count} new, {updated_count} updated, {thumb_count} thumbnails generated)"
        + (" (partial success)" if partial_error else "")
    )
    return {
        'total': len(fetched),
        'created': created_count,
        'updated': updated_count,
        'thumbnails': thumb_count,
        'partial_error': partial_error,
    }
