from django.conf.urls import url
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "pages"

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name="home"),
    url(r'^competition/create', views.CompetitionFormView.as_view(), name="competition_create"),
    path('competition/view/<int:competition_pk>/', views.CompetitionDetailView.as_view()),
    url(r'^search', views.SearchView.as_view(), name="search"),
    url(r'test', views.CompetitionListTestView.as_view()),
]
