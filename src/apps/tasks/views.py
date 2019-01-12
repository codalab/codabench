from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class TaskManagement(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/management.html'
