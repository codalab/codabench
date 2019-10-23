from django.urls import path
from queues import views

app_name = "queues"


urlpatterns = [
    path('', views.QueueManagementView.as_view(), name='list'),
]
