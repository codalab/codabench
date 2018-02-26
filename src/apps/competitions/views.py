from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.views.generic import TemplateView, CreateView
from django.views.generic.base import ContextMixin

from .models import Competition, Submission


class CompetitionManagement(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/management.html'


class CompetitionForm(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/form.html'


class CompetitionDetail(LoginRequiredMixin, TemplateView, ContextMixin):
    template_name = 'competitions/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['number'] = random.randrange(1, 100)
        try:
            my_pk = kwargs.pop('pk')
            comp = Competition.objects.get(pk=my_pk)
            context['comp'] = comp
            context['comp_pk'] = comp.pk
        except KeyError:
            print("Key error oh no")
        return context
