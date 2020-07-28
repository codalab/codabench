from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, FileResponse
from django.views.generic import TemplateView, DetailView

from .models import Competition


class CompetitionManagement(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/management.html'


class CompetitionForm(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/form.html'


class CompetitionUpload(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/upload.html'


class CompetitionDetail(DetailView):
    queryset = Competition.objects.all()
    template_name = 'competitions/detail.html'

    def get_object(self, *args, **kwargs):
        competition = super().get_object(*args, **kwargs)
        is_creator = self.request.user.is_superuser or self.request.user == competition.created_by
        is_collaborator = self.request.user in competition.collaborators.all()
        valid_secret_key = self.request.GET.get('secret_key') == str(competition.secret_key)
        if is_creator or is_collaborator or competition.published or valid_secret_key:
            return competition
        raise Http404()
