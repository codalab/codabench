from itertools import islice

from analytics.models import OrphanFileCandidate
from django.db.models import Count, Sum
from .reports import serialize_object


def save_scan_candidates(scan_job, orphaned_objects, batch_size=5000):
    """
    Persist orphaned objects in PostgreSQL using batched inserts.
    """
    candidates = (
        OrphanFileCandidate(
            scan=scan_job,
            bucket=obj.bucket,
            key=obj.key,
            size=obj.size,
            last_modified=obj.last_modified,
            etag=obj.etag,
        )
        for obj in orphaned_objects
    )

    while True:
        batch = list(islice(candidates, batch_size))

        if not batch:
            break

        OrphanFileCandidate.objects.bulk_create(
            batch,
            batch_size=batch_size,
        )


def get_current_scan_result(scan_job):
    """
    Return the original scan report with the current
    remaining cleanup candidates.

    No S3 request is performed.
    """
    if not scan_job.result:
        return None

    result = dict(scan_job.result)
    summary = dict(result["summary"])

    candidates = scan_job.candidates.filter(
        status__in=[
            OrphanFileCandidate.Status.PENDING,
            OrphanFileCandidate.Status.FAILED,
        ]
    )

    totals = candidates.aggregate(
        count=Count("id"),
        size=Sum("size"),
    )

    summary["orphaned_count"] = totals["count"]
    summary["orphaned_size"] = totals["size"] or 0

    preview_limit = result.get("preview_limit", 100)

    result["summary"] = summary

    result["orphaned_preview"] = [
        serialize_object(candidate)
        for candidate in candidates.order_by("id")[:preview_limit]
    ]

    return result