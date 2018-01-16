from django.conf.urls import url
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "pages"

urlpatterns = [
    path('', views.HomeView.as_view(), name="home"),
    # path(r'^competition/create', views.CompetitionFormView.as_view(), name="competition_create"),
    # path('competition/view/<int:competition_pk>/', views.CompetitionDetailView.as_view()),
    path('search', views.SearchView.as_view(), name="search"),
    path('organize', views.OrganizeView.as_view(), name="organize"),
    # path('test', views.CompetitionListTestView.as_view()),
]
