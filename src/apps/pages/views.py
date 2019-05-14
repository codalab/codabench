from django.views.generic import TemplateView

from competitions.models import Competition
from competitions.utils import get_featured_competitions, get_popular_competitions


class HomeView(TemplateView):
    template_name = 'pages/home.html'


class OrganizeView(TemplateView):
    template_name = 'pages/organize.html'


class SearchView(TemplateView):
    template_name = 'search/form.html'


class ServerStatusView(TemplateView):
    template_name = 'pages/server_status.html'
