import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from queues.models import Queue

logger = logging.getLogger(__name__)


class QueueListView(LoginRequiredMixin, TemplateView):
    template_name = 'queues/list.html'


class QueueFormView(LoginRequiredMixin, TemplateView):
    template_name = 'queues/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs.get('pk'):
            try:
                context['queue'] = Queue.objects.get(pk=self.kwargs.get('pk'))
            except Queue.DoesNotExist:
                logger.info("Queue not found!")
        return context
