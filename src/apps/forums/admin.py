from django.contrib import admin
from profiles.models import User
from . import models


@admin.action(description="Deactivate Account and Delete Item")
def DeactivateAccountThread(modeladmin, request, queryset):
    for obj in queryset:
        user = User.objects.get(id=obj.started_by_id)
        user.is_banned = True
        user.save()
    queryset.delete()


@admin.action(description="Deactivate Account and Delete Item")
def DeactivateAccountPost(modeladmin, request, queryset):
    for obj in queryset:
        user = User.objects.get(id=obj.posted_by_id)
        user.is_banned = True
        user.save()
    queryset.delete()


class ForumsExpansion(admin.ModelAdmin):
    raw_id_fields = ["competition"]
    list_display = ["id", "competition"]
    search_fields = ["id", "competition"]


class ThreadExpansion(admin.ModelAdmin):
    raw_id_fields = ["forum", "started_by"]
    list_display = ["id", "title", "started_by"]
    search_fields = ["id", "title", "started_by__username"]
    actions = [DeactivateAccountThread]


class PostExpansion(admin.ModelAdmin):
    raw_id_fields = ["thread", "posted_by"]
    list_display = ["id", "content_limited", "posted_by"]
    search_fields = ["id", "content", "posted_by__username"]
    actions = [DeactivateAccountPost]

    @admin.display(description="Content", ordering="content")
    def content_limited(self, obj):
        if not obj.content:
            return "-"
        if len(obj.content) > 500:
            return obj.content[:500] + "(...)"
        else:
            return obj.content[:500]


admin.site.register(models.Forum, ForumsExpansion)
admin.site.register(models.Thread, ThreadExpansion)
admin.site.register(models.Post, PostExpansion)
