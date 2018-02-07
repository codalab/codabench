from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class CompetitionManagement(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/management.html'


class CompetitionForm(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/form.html'


class CompetitionDetail(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/detail.html'
