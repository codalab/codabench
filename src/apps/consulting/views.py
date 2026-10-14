from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ConsultingPublic(TemplateView):
    template_name = 'consulting/public.html'


class ConsultingMyListing(LoginRequiredMixin, TemplateView):
    template_name = 'consulting/my_listing.html'
