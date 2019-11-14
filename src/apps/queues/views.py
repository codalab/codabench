from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class QueueManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'queues/management.html'
