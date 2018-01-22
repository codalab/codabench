# from django.conf import settings
#
#
# def _make_url_sassy(path, permission='r', duration=60 * 60 * 24, headers=None):
#
#     if permission == 'r':
#         # GET instead of r (read) for AWS
#         method = 'GET'
#     elif permission == 'w':
#         # GET instead of w (write) for AWS
#         method = 'PUT'
#     else:
#         # Default to get if we don't know
#         method = 'GET'
#
#     # Remove the beginning of the URL (before bucket name) so we just have the path to the file
#     path = path.split(settings.AWS_STORAGE_PRIVATE_BUCKET_NAME)[-1]
#
#     # Spaces replaced with +'s, so we have to replace those...
#     path = path.replace('+', ' ')
#
#     headers = headers or {}
#
#     headers['Content-Length'] =
#
#     return BundleStorage.connection.generate_url(
#         expires_in=duration,
#         method=method,
#         headers=headers,
#         bucket=settings.AWS_STORAGE_PRIVATE_BUCKET_NAME,
#         key=path,
#         query_auth=True,
#     )
