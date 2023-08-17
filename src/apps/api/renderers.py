from rest_framework.renderers import BaseRenderer
from rest_framework.renderers import BrowsableAPIRenderer


class ZipRenderer(BaseRenderer):
    media_type = 'application/zip'
    format = 'zip'


class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    """Overrides the standard DRF Browsable API renderer."""

    def get_context(self, *args, **kwargs):
        context = super(CustomBrowsableAPIRenderer, self).get_context(*args, **kwargs)
        # Remove "HTML" tabs
        context["post_form"] = None
        context["put_form"] = None
        return context
