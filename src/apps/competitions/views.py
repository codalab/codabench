from django.views.generic import TemplateView


class CompetitionManagement(TemplateView):
    template_name = 'competitions/management.html'


class CompetitionForm(TemplateView):
    template_name = 'competitions/form.html'
