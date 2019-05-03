from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView

from .models import Task


class TaskManagement(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/management.html'


class TaskDetailView(LoginRequiredMixin, DetailView):
    queryset = Task.objects.all()
    template_name = 'tasks/task_detail.html'
