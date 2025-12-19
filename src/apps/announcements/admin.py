from django.contrib import admin
from . import models


admin.site.register(models.Announcement)
admin.site.register(models.NewsPost)
