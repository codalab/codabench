
from dataclasses import dataclass
from datetime import datetime
from django.conf import settings
from django.apps import apps

from analytics.orphan_files.references import FILE_FIELDS

ALLOWED_PREFIXES = {
    "private": (
        "dataset/",
        "submission_details/",
        "prediction_result/",
        "scoring_result/",
        "detailed_result/",
    ),
    "public": (
        "logos/",
        "profile_photos/",
        "organization_photos/",
    ),
}


def get_allowed_prefixes_by_bucket():
    mapping = {}

    bucket_mapping = {
        "private": settings.AWS_STORAGE_PRIVATE_BUCKET_NAME,
        "public": settings.AWS_STORAGE_BUCKET_NAME,
    }

    for logical_name, prefixes in ALLOWED_PREFIXES.items():
        bucket_name = bucket_mapping[logical_name]
        mapping.setdefault(bucket_name, []).extend(prefixes)

    return {
        bucket: tuple(prefixes)
        for bucket, prefixes in mapping.items()
    }


def get_allowed_prefixes():
    """
    Return all managed application prefixes.
    """
    return sorted({
        prefix
        for prefixes in ALLOWED_PREFIXES.values()
        for prefix in prefixes
    })


def get_scan_prefixes_by_bucket(prefix=None):
    """
    Return managed prefixes restricted to the requested scope.

    None means all managed prefixes.
    """
    allowed_prefixes = get_allowed_prefixes_by_bucket()

    if prefix is None:
        return allowed_prefixes

    if (
        not isinstance(prefix, str)
        or prefix not in get_allowed_prefixes()
    ):
        raise ValueError("Invalid storage prefix")

    return {
        bucket: (prefix,)
        for bucket, prefixes in allowed_prefixes.items()
        if prefix in prefixes
    }


@dataclass(frozen=True)
class StorageObject:
    bucket: str
    key: str
    size: int
    last_modified: datetime
    etag: str = ""


def get_storage_backends():
    """
    Return the effective storage backend for each bucket.

    Resolve backends from the actual model fields rather than
    assuming that BundleStorage always uses 'private'.
    """
    backends = {}

    for app_label, model_name, field_name in FILE_FIELDS:
        model = apps.get_model(app_label, model_name)
        storage = model._meta.get_field(field_name).storage

        backends.setdefault(storage.bucket_name, storage)

    return backends


def iter_storage_objects(bucket_name, prefixes, page_size=1000):
    """
    Iterate over S3 objects using paginated list_objects_v2.

    Read-only: no objects are downloaded or deleted.
    """
    backends = get_storage_backends()

    if bucket_name not in backends:
        raise ValueError(f"No storage backend for bucket: {bucket_name}")

    storage = backends[bucket_name]
    client = storage.connection.meta.client

    paginator = client.get_paginator("list_objects_v2")

    for prefix in prefixes:
        pages = paginator.paginate(
            Bucket=bucket_name,
            Prefix=prefix,
            PaginationConfig={"PageSize": page_size},
        )

        for page in pages:
            for obj in page.get("Contents", []):
                yield StorageObject(
                    bucket=bucket_name,
                    key=obj["Key"],
                    size=obj["Size"],
                    last_modified=obj["LastModified"],
                    etag=obj.get("ETag", "").strip('"'),
                )


def iter_managed_objects(page_size=1000, prefix=None):
    """
    Iterate over objects in managed application prefixes.

    If a prefix is provided, only scan that prefix.
    """
    backends = get_storage_backends()

    prefixes_by_bucket = get_scan_prefixes_by_bucket(prefix)

    for bucket_name, prefixes in prefixes_by_bucket.items():

        if bucket_name not in backends:
            raise ValueError(
                f"No storage backend found for bucket: {bucket_name}"
            )

        yield from iter_storage_objects(
            bucket_name=bucket_name,
            prefixes=prefixes,
            page_size=page_size,
        )
