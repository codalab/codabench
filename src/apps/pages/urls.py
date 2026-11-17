from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path('', views.HomeView.as_view(), name="home"),
    # path(r'^competition/create', views.CompetitionFormView.as_view(), name="competition_create"),
    # path('competition/view/<int:competition_pk>/', views.CompetitionDetailView.as_view()),
    path('news/', views.NewsView.as_view(), name="news"),
    path('server_status', views.ServerStatusView.as_view(), name="server_status"),
    path('monitor_queues', views.MonitorQueuesView.as_view(), name="monitor_queues"),
    # path('test', views.CompetitionListTestView.as_view()),
]
