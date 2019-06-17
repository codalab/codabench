from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin


class AnalyticsView(PermissionRequiredMixin, TemplateView):
    permission_required = ('is_superuser',)
    template_name = 'analytics/analytics.html'
