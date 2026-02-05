from django.contrib import admin
from .models import Auth_Organization


class Auth_OrganizationExpansion(admin.ModelAdmin):
    list_display = ["id", "name", "client_id"]
    search_fields = ["id", "name", "client_id"]


admin.site.register(Auth_Organization, Auth_OrganizationExpansion)
