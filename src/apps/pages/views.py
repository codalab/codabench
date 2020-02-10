from datetime import timedelta

from django.http import HttpResponse
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.db.models import Count, Q

from competitions.models import Competition, Submission, CompetitionParticipant
from profiles.models import User


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        data = Competition.objects.aggregate(
            count=Count('*'),
            published_comps=Count('pk', filter=Q(published=True)),
            unpublished_comps=Count('pk', filter=Q(published=False)),
        )

        total_competitions = data['count']
        public_competitions = data['published_comps']
        private_competitions = data['unpublished_comps']
        users = User.objects.all().count()
        competition_participants = CompetitionParticipant.objects.all().count()
        submissions = Submission.objects.all().count()

        context['general_stats'] = [
            {'label': "Total Competitions", 'count': total_competitions},
            {'label': "Public Competitions", 'count': public_competitions},
            {'label': "Private Competitions", 'count': private_competitions},
            {'label': "Users", 'count': users},
            {'label': "Competition Participants", 'count': competition_participants},
            {'label': "Submissions", 'count': submissions},
        ]
        return context


class OrganizeView(TemplateView):
    template_name = 'pages/organize.html'


class SearchView(TemplateView):
    template_name = 'search/form.html'


class ServerStatusView(TemplateView):
    template_name = 'pages/server_status.html'

    def get_context_data(self, *args, **kwargs):
        if not self.request.user.is_staff:
            raise HttpResponse(status=404)

        qs = Submission.objects.all()
        qs = qs.filter(created_when__gte=now() - timedelta(days=2))
        qs = qs.order_by('-created_when')
        qs = qs.select_related('phase__competition', 'owner')

        context = super().get_context_data(*args, **kwargs)
        context['submissions'] = qs[:250]
        return context

