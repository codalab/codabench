from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView, DetailView

from .models import Competition


class CompetitionManagement(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/management.html'


class CompetitionForm(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/form.html'


class CompetitionUpload(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/upload.html'


class CompetitionDetail(LoginRequiredMixin, DetailView):
    queryset = Competition.objects.all()
    template_name = 'competitions/detail.html'

    def get_object(self, *args, **kwargs):
        competition = super().get_object(*args, **kwargs)

        if self.request.user.is_superuser:
            return competition

        if competition.published or self.request.user == competition.created_by or self.request.user in competition.collaborators.all():
            return competition
        elif self.request.GET.get('secret_key') == str(competition.secret_key):
            return competition
        else:
            raise Http404()

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # # context['number'] = random.randrange(1, 100)
    #     # try:
    #     #     my_pk = kwargs.pop('pk')
    #     #     comp = Competition.objects.get(pk=my_pk)
    #     #     context['comp'] = comp
    #     #     context['comp_pk'] = comp.pk
    #     # except KeyError:
    #     #     print("Key error oh no")
    #     return context
