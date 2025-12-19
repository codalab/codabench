from django.contrib import admin
from django.utils.translation import gettext_lazy as _
import json
import csv
from django.http import HttpResponse
from profiles.models import User
from . import models


class privateCompetitionsFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Private non-test")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "private"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("privateSmall", _("Submissions >= 10 and Participants >= 5")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Only show private competitions with >= 10 submissions and >=5 participants
        if self.value() == "privateSmall":
            return queryset.filter(
                published=False, submissions_count__gte=10, participants_count__gte=5
            )


# This will export the email of all the selected competition creators, removing duplications and banned users
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="email_username_list.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow(["Username", "Email", "Competition title", "Participants Count", "Submissions Count"])
    email_list = {}
    for obj in queryset:
        user = User.objects.get(id=obj.created_by_id)
        if not user.is_banned and user.email not in email_list.values():
            email_list.update({user.username: user.email})
            writer.writerow([user.username, user.email, obj.title, obj.participants_count, obj.submissions_count])
    return response


# This will export the email of all the selected competition creators, removing duplications and banned users
def export_as_json(modeladmin, request, queryset):
    email_list = {}
    for obj in queryset:
        user = User.objects.get(id=obj.created_by_id)
        if not user.is_banned and user.email not in email_list.values():
            email_list.update({user.username: user.email})
    return HttpResponse(json.dumps(email_list), content_type="application/json")


class CompetitionAdmin(admin.ModelAdmin):
    search_fields = ["title", "docker_image", "created_by__username"]
    list_display = ["id", "title", "created_by", "is_featured"]
    list_display_links = ["id", "title"]
    actions = [export_as_json, export_as_csv]
    list_filter = ["is_featured", privateCompetitionsFilter]


admin.site.register(models.Competition, CompetitionAdmin)
admin.site.register(models.CompetitionCreationTaskStatus)
admin.site.register(models.CompetitionParticipant)
admin.site.register(models.Page)
admin.site.register(models.Phase)
admin.site.register(models.Submission)
