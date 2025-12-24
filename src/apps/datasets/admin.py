from django.contrib import admin
from profiles.models import User
from . import models
from django.template.defaultfilters import filesizeformat


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
        "description_limited",
        "created_by",
        "type",
        "is_public",
        "is_verified",
        "filesize_human",
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

    @admin.display(description="Description", ordering="description")
    def description_limited(self, obj):
        if not obj.description:
            return "-"
        if len(obj.description) > 500:
            return obj.description[:500] + "(...)"
        else:
            return obj.description[:500]

    # Convert the file size from bytes to KB,MB,GB etc to make it more readable in the list_display
    @admin.display(description="File size", ordering="file_size")
    def filesize_human(self, obj):
        if not obj.file_size:
            return "-"
        return filesizeformat(obj.file_size)

    actions = [DeactivateAccount]


admin.site.register(models.Data, DataExpansion)
