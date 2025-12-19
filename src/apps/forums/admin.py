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
    list_display = ["competition"]
    search_fields = ["competition"]


class ThreadExpansion(admin.ModelAdmin):
    list_display = ["title", "started_by"]
    search_fields = ["title", "started_by__username"]
    actions = [DeactivateAccountThread]


class PostExpansion(admin.ModelAdmin):
    list_display = ["content", "posted_by"]
    search_fields = []
    actions = [DeactivateAccountPost]


admin.site.register(models.Forum, ForumsExpansion)
admin.site.register(models.Thread, ThreadExpansion)
admin.site.register(models.Post, PostExpansion)
