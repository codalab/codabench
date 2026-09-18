from django.views.generic import TemplateView


class ExternalCompetitionsPublic(TemplateView):
    template_name = 'external_competitions/public.html'
