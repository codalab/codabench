from django.contrib import admin
from django.utils.translation import gettext_lazy as _

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
            ("privateSmall", _("Submission >= 25 & Participants >= 10")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Only show private competitions with >= 25 submissions and >=10 participants
        if self.value() == "privateSmall":
            return queryset.filter(
                published=False,
                submissions_count__gte=25,
                participants_count__gte=10
            )


class CompetitionAdmin(admin.ModelAdmin):
    search_fields = ['title', 'docker_image', 'created_by__username']
    list_display = ['id', 'title', 'created_by', 'is_featured']
    list_filter = ['is_featured', privateCompetitionsFilter]


admin.site.register(models.Competition, CompetitionAdmin)
admin.site.register(models.CompetitionCreationTaskStatus)
admin.site.register(models.CompetitionParticipant)
admin.site.register(models.Page)
admin.site.register(models.Phase)
admin.site.register(models.Submission)
