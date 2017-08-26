from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name="home"),
    url(r'^competition/create', views.CompetitionFormView.as_view(), name="competition_create"),
    url(r'^search', views.SearchView.as_view(), name="search"),
    url(r'test', views.CompetitionListTestView.as_view()),
]
