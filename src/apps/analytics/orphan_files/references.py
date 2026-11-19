
from collections import defaultdict

from django.apps import apps


# Model references are resolved lazily to avoid import cycles.
FILE_FIELDS = (
    ("datasets", "Data", "data_file"),
    ("competitions", "SubmissionDetails", "data_file"),
    ("competitions", "Submission", "prediction_result"),
    ("competitions", "Submission", "scoring_result"),
    ("competitions", "Submission", "detailed_result"),
    ("profiles", "User", "photo"),
    ("profiles", "Organization", "photo"),
    ("competitions", "Competition", "logo"),
    ("competitions", "Competition", "logo_icon"),
)


def iter_file_references(chunk_size=2000):
    """
    Yield (bucket_name, object_key) for every non-empty
    FileField/ImageField stored in the database.

    Uses the storage configured on each model field.
    """
    for app_label, model_name, field_name in FILE_FIELDS:
        model = apps.get_model(app_label, model_name)
        field = model._meta.get_field(field_name)

        bucket_name = field.storage.bucket_name

        queryset = (
            model.objects
            .exclude(**{f"{field_name}__isnull": True})
            .exclude(**{field_name: ""})
            .values_list(field_name, flat=True)
        )

        for key in queryset.iterator(chunk_size=chunk_size):
            if key:
                yield bucket_name, key


def collect_file_references(chunk_size=2000):
    """
    Return references grouped by bucket.

    Example:
        {
            "private": {"dataset/...", "scoring_result/..."},
            "public": {"logos/...", "profile_photos/..."},
        }
    """
    references = defaultdict(set)

    for bucket_name, key in iter_file_references(chunk_size):
        references[bucket_name].add(key)

    return dict(references)


def get_reference_counts(chunk_size=2000):
    """
    Return the number of unique referenced keys per bucket.
    """
    references = collect_file_references(chunk_size)

    return {
        bucket: len(keys)
        for bucket, keys in references.items()
    }
