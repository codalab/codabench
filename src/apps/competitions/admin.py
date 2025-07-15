from django.contrib import admin

from . import models


class CompetitionAdmin(admin.ModelAdmin):
    search_fields = ['title', 'docker_image', 'created_by__username']
    list_display = ['id', 'title', 'created_by', 'is_featured']
    list_filter = ['is_featured']


admin.site.register(models.Competition, CompetitionAdmin)
admin.site.register(models.CompetitionCreationTaskStatus)
admin.site.register(models.CompetitionParticipant)
admin.site.register(models.Page)
admin.site.register(models.Phase)
admin.site.register(models.Submission)
