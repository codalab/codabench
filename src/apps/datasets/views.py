from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DataManagement(LoginRequiredMixin, TemplateView):
    template_name = 'datasets/management.html'
