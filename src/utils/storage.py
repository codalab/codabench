import hashlib

from django.conf import settings

# Import only the required backend
if settings.STORAGE_IS_S3:
    # Create separate instances for Bundle and Public storage
    BundleStorage = StorageClass()
    BundleStorage.bucket_name = settings.AWS_STORAGE_PRIVATE_BUCKET_NAME  # Set the private bucket
    PublicStorage = StorageClass()
    PublicStorage.bucket_name = settings.AWS_STORAGE_BUCKET_NAME  # Set the public bucket

elif settings.STORAGE_IS_GCS:
    # For GCS
    BundleStorage = StorageClass()
    BundleStorage.bucket_name = settings.GS_PRIVATE_BUCKET_NAME  # Set the private bucket
    PublicStorage = StorageClass()
    PublicStorage.bucket_name = settings.GS_PUBLIC_BUCKET_NAME  # Set the public bucket

elif settings.STORAGE_IS_AZURE:
    # For Azure
    BundleStorage = StorageClass()
    BundleStorage.azure_container = settings.BUNDLE_AZURE_CONTAINER  # Set the private container
    PublicStorage = StorageClass()
    PublicStorage.azure_container = settings.AZURE_CONTAINER  # Set the public container

else:
    raise NotImplementedError()


def md5(filename):
    """Given some file return its md5, works well on large files"""
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
