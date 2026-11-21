
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from django.utils import timezone
from .storage import ALLOWED_PREFIXES
from .references import collect_file_references
from .storage import iter_managed_objects, StorageObject


@dataclass
class ScanResult:
    referenced_count: int = 0
    referenced_size: int = 0

    orphaned: list[StorageObject] = field(default_factory=list)
    recent_unreferenced: list[StorageObject] = field(default_factory=list)

    missing: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )

    scanned_count: int = 0
    scanned_size: int = 0


def scan_orphan_files(grace_period_days=7, page_size=1000):
    """
    Compare PostgreSQL FileField references with MinIO objects.

    Read-only scan:
      - No database modifications
      - No S3 modifications
      - No file downloads

    Unreferenced objects younger than the grace period are
    reported separately, not considered eligible for deletion.
    """
    if grace_period_days < 0:
        raise ValueError("grace_period_days must be >= 0")

    references = collect_file_references()

    remaining = {
        bucket: {
            key
            for key in keys
            if any(
                key.startswith(prefix)
                for prefix in ALLOWED_PREFIXES.get(bucket, ())
            )
        }
        for bucket, keys in references.items()
        if bucket in ALLOWED_PREFIXES
    }

    cutoff = timezone.now() - timedelta(days=grace_period_days)

    result = ScanResult()

    for obj in iter_managed_objects(page_size=page_size):
        result.scanned_count += 1
        result.scanned_size += obj.size

        bucket_references = remaining.get(obj.bucket)

        if bucket_references is not None and obj.key in bucket_references:
            result.referenced_count += 1
            result.referenced_size += obj.size
            bucket_references.remove(obj.key)
            continue

        if obj.last_modified > cutoff:
            result.recent_unreferenced.append(obj)
        else:
            result.orphaned.append(obj)

    for bucket, keys in remaining.items():
        result.missing[bucket].update(keys)

    return result
