from django.contrib import admin

from . import models


admin.site.register(models.Data)
admin.site.register(models.DataGroup)
