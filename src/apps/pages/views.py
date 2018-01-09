from django.views.generic import TemplateView, DetailView
from django.views.generic import CreateView
from django.views.generic.base import ContextMixin

from leaderboards.forms import MetricForm
from leaderboards.forms import ColumnForm

from leaderboards.models import Metric
from competitions.models import Competition


class HomeView(TemplateView):
    template_name = 'pages/home.html'


class CompetitionListTestView(TemplateView):
    template_name = 'pages/competition_list.html'


class CompetitionFormView(TemplateView, ContextMixin):
    template_name = 'competitions/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['leaderboard'] = {
        #     'metric_form': MetricForm(),
        #     'column_form': ColumnForm()
        # }
        context['metric_form'] = MetricForm()
        context['column_form'] = ColumnForm()
        return context


class CompetitionDetailView(DetailView, ContextMixin):
    template_name = 'competitions/detail.html'
    # queryset = Competition.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['competition'] = self.object
        return context

    def get_object(self, queryset=None):
        competition = None
        comp_pk = self.kwargs.pop('competition_pk')
        if comp_pk:
            competition = Competition.objects.get(pk=comp_pk)
            print("Self.object is {}".format(competition))
        return competition



class SearchView(TemplateView):
    template_name = 'search/form.html'


# class CreateMetricView(CreateView, ContextMixin):
#     model = Metric
#     fields = '__all__'
#     template_name = 'leaderboards/metric_form.html'
#     success_url = '/'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # context['leaderboard'] = {
#         #     'metric_form': MetricForm(),
#         #     'column_form': ColumnForm()
#         # }
#         context['metric_form'] = MetricForm()
#         context['column_form'] = ColumnForm()
#         return context