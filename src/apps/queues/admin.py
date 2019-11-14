from django.contrib import admin
from queues import models


admin.site.register(models.Queue)
