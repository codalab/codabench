from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin


class DashboardView(PermissionRequiredMixin, TemplateView):
    permission_required = ('is_superuser',)
    template_name = 'dashboard/dashboard.html'
