
from dataclasses import dataclass, field
from datetime import timedelta

from django.apps import apps
from django.utils import timezone

from .references import FILE_FIELDS
from .storage import get_allowed_prefixes_by_bucket, get_storage_backends
from datetime import timezone as datetime_timezone
from contextlib import contextmanager
from django.db import connection
from django.db.models import Q

from analytics.models import OrphanFilesJob, OrphanFileCandidate

MAX_GRACE_DAYS = 3650
MAX_SELECTED_OBJECTS = 100


@dataclass
class CleanupResult:
    mode: str
    candidates: int = 0
    deleted: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list = field(default_factory=list)

    def as_dict(self):
        return {
            "mode": self.mode,
            "candidates": self.candidates,
            "deleted": self.deleted,
            "skipped": self.skipped,
            "failed": self.failed,
            "errors": self.errors[:100],
        }


def is_allowed_object(bucket, key):
    allowed_prefixes = get_allowed_prefixes_by_bucket()

    return (
        isinstance(bucket, str)
        and bucket in allowed_prefixes
        and isinstance(key, str)
        and any(
            key.startswith(prefix)
            for prefix in allowed_prefixes[bucket]
        )
        and not key.endswith("/")
    )


def is_still_referenced(bucket, key):
    """
    Check the database again immediately before deletion.

    This does not prevent a concurrent transaction from
    creating a new reference after the check.
    """
    for app_label, model_name, field_name in FILE_FIELDS:
        model = apps.get_model(app_label, model_name)
        field = model._meta.get_field(field_name)

        if field.storage.bucket_name != bucket:
            continue

        if model.objects.filter(**{field_name: key}).exists():
            return True

    return False


def get_current_object(client, bucket, key):
    try:
        return client.head_object(Bucket=bucket, Key=key)
    except client.exceptions.ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def same_s3_timestamp(list_timestamp, head_timestamp):
    """
    Compare S3 timestamps at second precision.

    MinIO list_objects_v2 can return microseconds while
    head_object returns timestamps rounded to seconds.
    """
    list_timestamp = list_timestamp.astimezone(
        datetime_timezone.utc
    ).replace(microsecond=0)

    head_timestamp = head_timestamp.astimezone(
        datetime_timezone.utc
    ).replace(microsecond=0)

    return list_timestamp == head_timestamp


def cleanup_orphan_files(
    scan_job,
    cleanup_job,
    mode="all",
    selected_objects=None,
):
    with orphan_cleanup_lock():
        return _cleanup_orphan_files(
            scan_job=scan_job,
            cleanup_job=cleanup_job,
            mode=mode,
            selected_objects=selected_objects,
        )


def _cleanup_orphan_files(
    scan_job,
    cleanup_job,
    mode="all",
    selected_objects=None,
):
    """
    Delete eligible candidates from a persisted scan.

    No full S3 listing is performed.

    Managed storage and reference writes must be paused
    externally during physical deletion.
    """
    if scan_job.job_type != OrphanFilesJob.JobType.SCAN:
        raise ValueError("Invalid source scan")

    if scan_job.status != OrphanFilesJob.Status.SUCCESS:
        raise ValueError("Source scan is not successful")

    if cleanup_job.source_scan_id != scan_job.pk:
        raise ValueError("Cleanup source scan mismatch")

    if mode not in ("all", "selected"):
        raise ValueError("Invalid cleanup mode")

    candidates = scan_job.candidates.filter(
        status__in=[
            OrphanFileCandidate.Status.PENDING,
            OrphanFileCandidate.Status.FAILED,
        ]
    )

    if mode == "selected":

        if (
            not isinstance(selected_objects, list)
            or not 1 <= len(selected_objects) <= MAX_SELECTED_OBJECTS
        ):
            raise ValueError("Invalid selected objects")

        identities = set()
        selection = Q()

        for item in selected_objects:
            if not isinstance(item, dict):
                raise ValueError("Invalid selected object")

            bucket = item.get("bucket")
            key = item.get("key")

            if not is_allowed_object(bucket, key):
                raise ValueError("Object outside allowed prefixes")

            identities.add((bucket, key))
            selection |= Q(bucket=bucket, key=key)

        if len(identities) != len(selected_objects):
            raise ValueError("Duplicate selected objects")

        candidates = candidates.filter(selection)

        if candidates.count() != len(identities):
            raise ValueError("Some selected candidates are not eligible")

    elif selected_objects is not None:
        raise ValueError("Invalid selection for all mode")

    result = CleanupResult(mode=mode)
    result.candidates = candidates.count()

    backends = get_storage_backends()

    clients = {
        bucket: storage.connection.meta.client
        for bucket, storage in backends.items()
    }

    cutoff = timezone.now() - timedelta(
        days=scan_job.grace_period_days
    )

    last_heartbeat = timezone.now()
    last_pk = 0

    while True:

        batch = list(
            candidates.filter(pk__gt=last_pk)
            .order_by("pk")[:500]
        )

        if not batch:
            break

        for candidate in batch:

            last_pk = candidate.pk

            now = timezone.now()

            if (
                now - last_heartbeat
            ).total_seconds() >= 30:

                OrphanFilesJob.objects.filter(
                    pk=cleanup_job.pk,
                ).update(
                    heartbeat_at=now,
                    result=result.as_dict(),
                )

                last_heartbeat = now

            candidate_status = (
                OrphanFileCandidate.Status.SKIPPED
            )
            error = ""

            try:
                if not is_allowed_object(
                    candidate.bucket,
                    candidate.key,
                ):
                    error = "Object outside allowed prefixes"

                elif candidate.bucket not in clients:
                    raise RuntimeError("Storage backend unavailable")

                else:
                    client = clients[candidate.bucket]

                    current = get_current_object(
                        client,
                        candidate.bucket,
                        candidate.key,
                    )

                    if current is None:
                        error = "Object no longer exists"

                    elif (
                        not candidate.etag
                        or current.get("ETag", "").strip('"')
                        != candidate.etag
                    ):
                        error = "Object ETag has changed"

                    elif not same_s3_timestamp(
                        candidate.last_modified,
                        current["LastModified"],
                    ):
                        error = "Object modification date has changed"

                    elif current["ContentLength"] != candidate.size:
                        error = "Object size has changed"

                    elif current["LastModified"] > cutoff:
                        error = "Object is inside the grace period"

                    elif is_still_referenced(
                        candidate.bucket,
                        candidate.key,
                    ):
                        error = "Object is referenced in PostgreSQL"

                    else:
                        client.delete_object(
                            Bucket=candidate.bucket,
                            Key=candidate.key,
                        )

                        candidate_status = (
                            OrphanFileCandidate.Status.DELETED
                        )

            except Exception as exc:

                candidate_status = (
                    OrphanFileCandidate.Status.FAILED
                )
                error = str(exc)

            candidate.status = candidate_status
            candidate.error = error
            candidate.processed_at = timezone.now()

            candidate.save(
                update_fields=[
                    "status",
                    "error",
                    "processed_at",
                ],
            )

            if candidate_status == OrphanFileCandidate.Status.DELETED:
                result.deleted += 1

            elif candidate_status == OrphanFileCandidate.Status.SKIPPED:
                result.skipped += 1

            else:
                result.failed += 1

                if len(result.errors) < 100:
                    result.errors.append({
                        "bucket": candidate.bucket,
                        "key": candidate.key,
                        "error": error,
                    })

    return result.as_dict()


@contextmanager
def orphan_cleanup_lock():
    """
    Prevent two cleanup operations from running simultaneously.

    PostgreSQL session-level advisory lock.
    """
    lock_id = 7819453201

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_try_advisory_lock(%s)",
            [lock_id],
        )
        acquired = cursor.fetchone()[0]

    if not acquired:
        raise RuntimeError(
            "Another orphan files cleanup is already running."
        )

    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_unlock(%s)",
                [lock_id],
            )
