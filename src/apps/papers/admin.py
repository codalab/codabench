from django.contrib import admin

from papers.models import Paper


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'venue', 'citation_count', 'is_visible')
    list_filter = ('is_visible', 'publication_date')
    search_fields = ('title', 'authors', 'venue', 'doi')
    ordering = ('-publication_date', '-citation_count')
