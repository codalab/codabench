from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name="home"),
    url(r'test', views.CompetitionListTestView.as_view()),
]
