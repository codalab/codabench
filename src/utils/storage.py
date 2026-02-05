import hashlib
from django.conf import settings

# Fallbacks
PublicStorageClass = object
PrivateStorageClass = object

# Import only the required backend
if settings.STORAGE_IS_S3:
    try:
        from storages.backends.s3boto3 import S3Boto3Storage

        class PublicStorageClass(S3Boto3Storage):
            bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)

        class PrivateStorageClass(S3Boto3Storage):
            bucket_name = getattr(settings, "AWS_STORAGE_PRIVATE_BUCKET_NAME", None)
    except ImportError:
        raise RuntimeError("S3 backend requested but 'boto3' or 's3boto3' storage is not installed")

elif settings.STORAGE_IS_GCS:
    try:
        from storages.backends.gcloud import GoogleCloudStorage

        class PublicStorageClass(GoogleCloudStorage):
            bucket_name = getattr(settings, "GS_PUBLIC_BUCKET_NAME", None)

        class PrivateStorageClass(GoogleCloudStorage):
            bucket_name = getattr(settings, "GS_PRIVATE_BUCKET_NAME", None)
    except ImportError:
        raise RuntimeError("GCS backend requested but 'google-cloud-storage' is not installed")

elif settings.STORAGE_IS_AZURE:
    try:
        from storages.backends.azure_storage import AzureStorage

        class CodalabAzureStorage(AzureStorage):
            def __init__(self, *args, azure_container=None, **kwargs):
                if azure_container:
                    self.azure_container = azure_container
                super().__init__(*args, **kwargs)

        class PublicStorageClass(CodalabAzureStorage):
            def __init__(self, *args, **kwargs):
                super().__init__(
                    *args,
                    azure_container=settings.AZURE_CONTAINER,
                    account_name=settings.AZURE_ACCOUNT_NAME,
                    account_key=settings.AZURE_ACCOUNT_KEY,
                    **kwargs,
                )

        class PrivateStorageClass(CodalabAzureStorage):
            def __init__(self, *args, **kwargs):
                super().__init__(
                    *args,
                    azure_container=settings.BUNDLE_AZURE_CONTAINER,
                    account_name=settings.BUNDLE_AZURE_ACCOUNT_NAME,
                    account_key=settings.BUNDLE_AZURE_ACCOUNT_KEY,
                    **kwargs,
                )

    except ImportError:
        raise RuntimeError("Azure backend requested but 'azure-storage-blob' is not installed")

else:
    raise NotImplementedError("Must use STORAGE_TYPE of 's3', 'minio', 'gcs', or 'azure'")


# Instantiate the storages
try:
    from django.core.files.storage import storages

    # This one is safe to access — assumes STORAGES["default"] is set correctly
    DefaultStorage = storages["default"]
except Exception as e:
    raise RuntimeError(f"Failed to load default storage from Django STORAGES: {e}")

try:
    BundleStorage = PrivateStorageClass()
except Exception:
    BundleStorage = DefaultStorage

try:
    PublicStorage = PublicStorageClass()
except Exception:
    PublicStorage = DefaultStorage


def md5(filename):
    """Given some file return its md5, works well on large files"""
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
