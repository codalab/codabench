from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView, DetailView

from .models import Competition, CompetitionParticipant


class CompetitionManagement(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/management.html'


class CompetitionPublic(TemplateView):
    template_name = 'competitions/public.html'


class CompetitionCreateForm(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/form.html'


class CompetitionUpdateForm(LoginRequiredMixin, DetailView):
    template_name = 'competitions/form.html'
    queryset = Competition.objects.all()

    def get_object(self, *args, **kwargs):
        competition = super().get_object(*args, **kwargs)

        is_admin, is_creator, is_collaborator = False, False, False

        # check if user is loggedin
        if self.request.user.is_authenticated:

            # check if user is admin
            is_admin = self.request.user.is_superuser

            # check if user is the creator of this competition
            is_creator = self.request.user == competition.created_by

            # check if user is collaborator of this competition
            is_collaborator = self.request.user in competition.collaborators.all()

        if (
            is_admin or
            is_creator or
            is_collaborator
        ):
            return competition
        raise Http404()


class CompetitionUpload(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/upload.html'


class CompetitionDetail(DetailView):
    queryset = Competition.objects.all()
    template_name = 'competitions/detail.html'

    def get_object(self, *args, **kwargs):
        competition = super().get_object(*args, **kwargs)

        is_admin, is_creator, is_collaborator, is_participant = False, False, False, False

        # check if user is loggedin
        if self.request.user.is_authenticated:

            # check if user is admin
            is_admin = self.request.user.is_superuser

            # check if user is the creator of this competition
            is_creator = self.request.user == competition.created_by

            # check if user is collaborator of this competition
            is_collaborator = self.request.user in competition.collaborators.all()

            # check if user is a participant of this competition
            # get participants from CompetitionParticipant where user=user and competition=competition
            is_participant = CompetitionParticipant.objects.filter(user=self.request.user, competition=competition).count() > 0

        # check if secret key provided is valid
        valid_secret_key = self.request.GET.get('secret_key') == str(competition.secret_key)

        if (
            is_admin or
            is_creator or
            is_collaborator or
            competition.published or
            valid_secret_key or
            is_participant
        ):
            return competition
        raise Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the secret_key from the request.GET dictionary
        secret_key = self.request.GET.get('secret_key')

        # Add the secret_key to the context dictionary
        context['secret_key'] = secret_key

        return context


class CompetitionDetailedResults(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/detailed_results.html'
