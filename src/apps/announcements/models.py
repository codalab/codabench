from django.db import models
from django.utils.timezone import now


class Announcement(models.Model):
    LEVEL_CRITICAL = "critical"
    LEVEL_WARNING = "warning"
    LEVEL_INFO = "info"
    LEVEL_PLAIN = "plain"
    LEVELS = [
        (LEVEL_CRITICAL, "Critical"),
        (LEVEL_WARNING, "Warning"),
        (LEVEL_INFO, "Info"),
        (LEVEL_PLAIN, "Plain"),
    ]

    PLACEMENT_HOME_PAGE = "home_page"
    PLACEMENT_PLATFORM = "platform"
    PLACEMENTS = [
        (PLACEMENT_HOME_PAGE, "Home page"),
        (PLACEMENT_PLATFORM, "All pages"),
    ]

    title = models.CharField(max_length=200, blank=True)
    text = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=10, choices=LEVELS, default=LEVEL_INFO)
    placement = models.CharField(
        max_length=20,
        choices=PLACEMENTS,
        default=PLACEMENT_HOME_PAGE,
        help_text="Home page: shown on the home page only. All pages: shown in a banner above the header on every page.",
    )
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0, help_text="Lower priority is shown first.")
    created_when = models.DateTimeField(default=now)

    def __str__(self):
        return self.title or f"Announcement {self.pk}"


class NewsPost(models.Model):
    title = models.CharField(max_length=40)
    link = models.URLField(max_length=200, blank=True)
    created_when = models.DateTimeField(default=now)
    text = models.TextField(null=True, blank=True)
