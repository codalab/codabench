from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator

class AnalyticsView(PermissionRequiredMixin, TemplateView):
    permission_required = ('is_superuser',)
    template_name = 'analytics/analytics.html'

#class AnalyticsViewSet(LoginRequiredMixin, TemplateView):
#    template_name = 'analytics/analytics.html'
#
#    @method_decorator(user_passes_test(lambda u: u.is_superuser))
#    def dispatch(self, *args, **kwargs):
#        return super().dispatch(*args, **kwargs)
