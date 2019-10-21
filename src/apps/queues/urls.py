from django.urls import path
from queues import views

app_name = "queues"


urlpatterns = [
    path('', views.QueueListView.as_view(), name='list'),
    path('form/', views.QueueFormView.as_view(), name='form'),
    path('form/<int:pk>', views.QueueFormView.as_view(), name='form')
]
