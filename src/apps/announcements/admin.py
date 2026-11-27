from django.contrib import admin
from django.utils.html import format_html
from . import models


class NewsPostExpansion(admin.ModelAdmin):
    list_display = ["id", "title", "link"]
    list_display_links = ["id", "title"]
    search_fields = ["id", "title", "link"]


LEVEL_COLORS = {
    models.Announcement.LEVEL_CRITICAL: "#db2828",
    models.Announcement.LEVEL_WARNING: "#f2c037",
    models.Announcement.LEVEL_INFO: "#2185d0",
}


class AnnouncementExpansion(admin.ModelAdmin):
    list_display = ["id", "level_badge", "title", "text_limited", "placement", "is_active", "priority"]
    list_display_links = ["id", "title", "text_limited"]
    list_filter = ["level", "placement", "is_active"]
    search_fields = ["title", "text"]
    ordering = ('-id',)
    fields = ("title", "level", "placement", "text", "is_active", "priority")

    @admin.display(description="level", ordering="level")
    def level_badge(self, obj):
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
            LEVEL_COLORS.get(obj.level, "#767676"),
            obj.get_level_display(),
        )

    @admin.display(description="text", ordering="text")
    def text_limited(self, obj):
        if not obj.text:
            return "-"
        if len(obj.text) > 500:
            return obj.text[:500] + "(...)"
        else:
            return obj.text[:500]


admin.site.register(models.Announcement, AnnouncementExpansion)
admin.site.register(models.NewsPost, NewsPostExpansion)
