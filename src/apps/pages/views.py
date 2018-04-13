from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'pages/home.html'


class OrganizeView(TemplateView):
    template_name = 'pages/organize.html'


class SearchView(TemplateView):
    template_name = 'search/form.html'


class ServerStatusView(TemplateView):
    template_name = 'pages/server_status.html'
