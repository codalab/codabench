from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from settings.base import BundleStorage


def _make_url_sassy(path, permission='r', duration=60 * 60 * 24, content_type='application/zip'):
    if settings.STORAGE_IS_AWS:
        # Remove the beginning of the URL (before bucket name) so we just have the path to the file
        path = path.split(settings.AWS_STORAGE_PRIVATE_BUCKET_NAME)[-1]

        # Spaces replaced with +'s, so we have to replace those...
        path = path.replace('+', ' ')

        params = {
            'Bucket': settings.AWS_STORAGE_PRIVATE_BUCKET_NAME,
            'Key': path,
        }

        # AWS uses method instead of permission
        if permission == 'r':
            client_method = 'get_object'
        elif permission == 'w':
            client_method = 'put_object'
            params["ContentType"] = content_type
        else:
            raise NotImplementedError()

        return BundleStorage.bucket.meta.client.generate_presigned_url(
            client_method,
            Params=params,
            ExpiresIn=duration,
        )
    elif settings.STORAGE_IS_GCS:
        bucket = BundleStorage.client.get_bucket(settings.GS_PRIVATE_BUCKET_NAME)
        return bucket.blob(path).generate_signed_url(expiration=timezone.now() + timedelta(seconds=duration), method=method)
    elif settings.STORAGE_IS_AZURE:
        #     sassy_url = make_blob_sas_url(
        #         settings.BUNDLE_AZURE_ACCOUNT_NAME,
        #         settings.BUNDLE_AZURE_ACCOUNT_KEY,
        #         settings.BUNDLE_AZURE_CONTAINER,
        #         path,
        #         permission=permission,
        #         duration=duration
        #     )
        #
        #     # Ugly way to check if we didn't get the path, should work...
        #     if '<Code>InvalidUri</Code>' not in sassy_url:
        #         return sassy_url
        #     else:
        #         return ''
        raise NotImplementedError()
    elif settings.STORAGE_IS_LOCAL:
        raise NotImplementedError()



