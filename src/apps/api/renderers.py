from rest_framework.renderers import BaseRenderer

class ZipRenderer(BaseRenderer):
    media_type = 'application/zip'
    format = 'zip'
