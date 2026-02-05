from django.contrib import admin
from queues import models
import json
import csv
from django.http import HttpResponse
from profiles.models import User


# This will export the email of all the selected competition creators, removing duplications and banned users
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="email_username_list.csv"'
        },
    )
    writer = csv.writer(response)
    writer.writerow(["Username", "Email", "Queue_Name"])
    email_list = {}
    for obj in queryset:
        user = User.objects.get(id=obj.owner_id)
        if not user.is_banned and user.email not in email_list.values():
            email_list.update({user.username: user.email})
            writer.writerow([user.username, user.email, obj.name])
    return response


# This will export the email of all the selected competition creators, removing duplications and banned users
def export_as_json(modeladmin, request, queryset):
    email_list = {}
    for obj in queryset:
        user = User.objects.get(id=obj.owner_id)
        if not user.is_banned and user.email not in email_list.values():
            email_list.update({user.username: user.email})
    return HttpResponse(json.dumps(email_list), content_type="application/json")


class QueueExpansion(admin.ModelAdmin):
    raw_id_fields = ["owner", "organizers"]
    list_display = ["id", "name", "owner", "is_public"]
    list_display_links = ["id", "name"]
    list_filter = ["is_public"]
    search_fields = ["id", "name", "owner__username", "organizers__username"]
    actions = [export_as_csv, export_as_json]


admin.site.register(models.Queue, QueueExpansion)
