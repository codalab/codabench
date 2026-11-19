
from dataclasses import dataclass, field
from datetime import timedelta

from django.apps import apps
from django.utils import timezone

from .references import FILE_FIELDS, collect_file_references
from .scanner import scan_orphan_files
from .storage import ALLOWED_PREFIXES, get_storage_backends
from datetime import timezone as datetime_timezone
from contextlib import contextmanager
from django.db import connection

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
    return (
        bucket in ALLOWED_PREFIXES
        and isinstance(key, str)
        and any(
            key.startswith(prefix)
            for prefix in ALLOWED_PREFIXES[bucket]
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
    grace_period_days=7,
    selected_objects=None,
    dry_run=True,
):
    with orphan_cleanup_lock():
        return _cleanup_orphan_files(
            grace_period_days=grace_period_days,
            selected_objects=selected_objects,
            dry_run=dry_run,
        )


def _cleanup_orphan_files(
    grace_period_days=7,
    selected_objects=None,
    dry_run=True,
):
    """
    Re-scan and clean eligible objects.

    selected_objects:
        None -> all eligible orphans
        list -> only the specified objects

    IMPORTANT:
        Actual deletion requires write activity affecting
        managed objects/references to be paused externally.

        S3 HEAD + DELETE is not atomic on an unversioned bucket.
    """
    if (
        isinstance(grace_period_days, bool)
        or not isinstance(grace_period_days, int)
        or not 0 <= grace_period_days <= MAX_GRACE_DAYS
    ):
        raise ValueError("Invalid grace period")

    if selected_objects is not None:
        if not isinstance(selected_objects, list):
            raise ValueError("selected_objects must be a list")

        if not 1 <= len(selected_objects) <= MAX_SELECTED_OBJECTS:
            raise ValueError("Invalid selected objects count")

        normalized = set()

        for item in selected_objects:
            if not isinstance(item, dict):
                raise ValueError("Invalid selected object")

            bucket = item.get("bucket")
            key = item.get("key")

            if not is_allowed_object(bucket, key):
                raise ValueError("Object outside allowed prefixes")

            normalized.add((bucket, key))

        if len(normalized) != len(selected_objects):
            raise ValueError("Duplicate selected objects")

        mode = "selected"
    else:
        normalized = None
        mode = "all"

    result = CleanupResult(mode=mode)

    # Rebuild the candidate list instead of trusting the
    # earlier API preview.
    scan = scan_orphan_files(
        grace_period_days=grace_period_days
    )

    backends = get_storage_backends()
    cutoff = timezone.now() - timedelta(
        days=grace_period_days
    )

    # Snapshot used only as an additional filter.
    references = collect_file_references()

    for obj in scan.orphaned:
        identity = (obj.bucket, obj.key)

        if normalized is not None and identity not in normalized:
            continue

        result.candidates += 1

        if not is_allowed_object(obj.bucket, obj.key):
            result.skipped += 1
            continue

        if obj.key in references.get(obj.bucket, set()):
            result.skipped += 1
            continue

        storage = backends.get(obj.bucket)

        if storage is None:
            result.skipped += 1
            continue

        client = storage.connection.meta.client

        try:
            current = get_current_object(
                client, obj.bucket, obj.key
            )

            if current is None:
                result.skipped += 1
                continue

            current_etag = current.get("ETag", "").strip('"')

            if not obj.etag or not current_etag or obj.etag != current_etag:
                result.skipped += 1
                continue

            # Do not delete objects modified since scanning.
            if (
                not same_s3_timestamp(
                    obj.last_modified,
                    current["LastModified"],
                )
                or current["ContentLength"] != obj.size
                or current["LastModified"] > cutoff
            ):
                result.skipped += 1
                continue

            if is_still_referenced(obj.bucket, obj.key):
                result.skipped += 1
                continue

            # The caller must ensure managed-object writes
            # are paused during real cleanup.
            client.delete_object(
                Bucket=obj.bucket,
                Key=obj.key,
            )

            result.deleted += 1

        except Exception as exc:
            result.failed += 1

            if len(result.errors) < 100:
                result.errors.append({
                    "bucket": obj.bucket,
                    "key": obj.key,
                    "error": str(exc),
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