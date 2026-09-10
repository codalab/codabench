from django.contrib import admin

from external_competitions.models import ExternalPlatform, ExternalCompetition, ExternalFetchLog


class ExternalPlatformAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'platform_type', 'competitions_fetch_url', 'competition_base_url', 'is_active', 'created_when']
    list_filter = ['platform_type', 'is_active']
    search_fields = ['name', 'competitions_fetch_url', 'competition_base_url']


class ExternalCompetitionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'platform', 'organizer_name', 'competition_created_when', 'updated_when']
    list_filter = ['platform']
    search_fields = ['name', 'organizer_name', 'competition_url']


class ExternalFetchLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'platform', 'started_at', 'finished_at', 'status', 'total_fetched', 'new_count', 'updated_count', 'deleted_count']
    list_filter = ['status', 'platform']


admin.site.register(ExternalPlatform, ExternalPlatformAdmin)
admin.site.register(ExternalCompetition, ExternalCompetitionAdmin)
admin.site.register(ExternalFetchLog, ExternalFetchLogAdmin)
