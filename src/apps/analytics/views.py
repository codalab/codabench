from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/analytics.html'

