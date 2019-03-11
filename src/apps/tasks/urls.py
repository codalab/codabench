from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path('', views.TaskManagement.as_view(), name='task_management'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='detail')
]
