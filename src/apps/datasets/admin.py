from django.contrib import admin
from profiles.models import User
from . import models


@admin.action(description="Deactivate Account and Delete Item")
def DeactivateAccount(modeladmin, request, queryset):
    for obj in queryset:
        user = User.objects.get(id=obj.created_by_id)
        user.is_banned = True
        user.save()
    queryset.delete()


class DataExpansion(admin.ModelAdmin):
    raw_id_fields = ["created_by", "competition"]
    list_display = [
        "id",
        "name",
        "description",
        "created_by",
        "type",
        "is_public",
        "is_verified",
        "file_size",
    ]
    search_fields = [
        "id",
        "created_by__username",
        "name",
        "type",
        "description",
        "file_name",
        "file_size",
    ]
    list_filter = ["is_public", "is_verified"]
    actions = [DeactivateAccount]


admin.site.register(models.Data, DataExpansion)
