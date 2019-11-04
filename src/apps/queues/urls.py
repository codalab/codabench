from django.urls import path
from . import views

app_name = "queues"


urlpatterns = [
    path('', views.QueueManagementView.as_view(), name='management'),
]
