from django.contrib import admin
from . import models


class NewsPostExpansion(admin.ModelAdmin):
    list_display = ["id", "title", "link"]
    list_display_links = ["id", "title"]
    search_fields = ["id", "title", "link"]


class AnnouncementExpansion(admin.ModelAdmin):
    list_display = ["id", "text_limited"]
    list_display_links = ["id", "text_limited"]

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
