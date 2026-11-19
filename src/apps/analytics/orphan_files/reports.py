
import json
from datetime import datetime, timezone
from pathlib import Path


def serialize_object(obj):
    return {
        "bucket": obj.bucket,
        "key": obj.key,
        "size": obj.size,
        "last_modified": obj.last_modified.isoformat(),
    }


def build_report(result, grace_period_days):
    orphaned_size = sum(obj.size for obj in result.orphaned)
    recent_size = sum(
        obj.size for obj in result.recent_unreferenced
    )

    missing = [
        {"bucket": bucket, "key": key}
        for bucket, keys in sorted(result.missing.items())
        for key in sorted(keys)
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "grace_period_days": grace_period_days,
        "summary": {
            "scanned_count": result.scanned_count,
            "scanned_size": result.scanned_size,
            "referenced_count": result.referenced_count,
            "referenced_size": result.referenced_size,
            "orphaned_count": len(result.orphaned),
            "orphaned_size": orphaned_size,
            "recent_unreferenced_count": len(
                result.recent_unreferenced
            ),
            "recent_unreferenced_size": recent_size,
            "missing_count": len(missing),
        },
        "orphaned": [
            serialize_object(obj)
            for obj in result.orphaned
        ],
        "recent_unreferenced": [
            serialize_object(obj)
            for obj in result.recent_unreferenced
        ],
        "missing": missing,
    }


def save_json_report(report, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Exclusive creation: never overwrite an existing report.
    with path.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    return path
