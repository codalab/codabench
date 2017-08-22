from django.views.generic import TemplateView


class CompetitionListTestView(TemplateView):
    template_name = 'pages/competition_list.html'
