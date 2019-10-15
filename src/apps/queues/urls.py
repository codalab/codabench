from django.conf.urls import url
from django.urls import path


from . import views

app_name = "queues"


urlpatterns = [
    # url(r'^$', views.QueueListView.as_view(), name='list'),
    path('', views.QueueListView.as_view(), name='list'),
    # url(r'^create$', views.QueueCreateView.as_view(), name='create'),
    path('create/', views.QueueCreateView.as_view(), name='create'),
    # url(r'^update/(?P<pk>\d+)$', views.QueueUpdateView.as_view(), name='update'),
    path('update/<int:pk>', views.QueueUpdateView.as_view(), name='update'),
    path('delete/<int:pk>', views.QueueDeleteView.as_view(), name='delete'),
]
