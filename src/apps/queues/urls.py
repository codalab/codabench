from django.urls import path
from queues import views

app_name = "queues"


urlpatterns = [
    path('', views.QueueListView.as_view(), name='list'),
    path('create/', views.QueueCreateView.as_view(), name='create'),
    path('update/<int:pk>', views.QueueUpdateView.as_view(), name='update'),
    path('delete/<int:pk>', views.QueueDeleteView.as_view(), name='delete'),
]
