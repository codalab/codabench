from django import template

from announcements.models import Announcement

# The tag library for this file.
# Templates load it by the file name: {% load announcement_tags %}
# Why: Django only finds custom tags in a "templatetags" folder inside an installed app.
register = template.Library()


# Registers the function below as the tag {% platform_announcements_banner %}.
# An inclusion tag runs the function, then renders the given template
# with the dictionary the function returns. The tag outputs that HTML.
@register.inclusion_tag("components/platform_announcements_banner.html")
def platform_announcements_banner():
    """
    Render the active platform announcements as a banner above the header.
    Used once in base.html, so the banner shows on every page that extends it.
    Why: a template tag only queries the database on pages that use it.
    A context processor would run the query for every template rendered with a request,
    including pages like the Django admin that never show the banner.
    """
    # Only active announcements meant for all pages.
    # Lower priority first, then newest first. Same order as the home page announcements.
    announcements = Announcement.objects.filter(
        is_active=True,
        placement=Announcement.PLACEMENT_PLATFORM,
    ).order_by("priority", "-created_when")

    # The key becomes a variable in the banner template.
    return {"platform_announcements": announcements}
