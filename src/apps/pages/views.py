from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'pages/home.html'


class CompetitionListTestView(TemplateView):
    template_name = 'pages/competition_list.html'


class CompetitionFormView(TemplateView):
    template_name = 'competitions/form.html'
