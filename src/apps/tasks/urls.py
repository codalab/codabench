from django.urls import path

from . import views
from api.views.tasks import TaskViewSet

app_name = "tasks"

urlpatterns = [
    path('', views.TaskManagement.as_view(), name='task_management'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='detail'),
    path('upload_task/', TaskViewSet.as_view({'post': 'upload_task'}), name='upload_task'),
]
