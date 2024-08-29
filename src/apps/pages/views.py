from datetime import timedelta
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.db.models import Count, Q

from competitions.models import Competition, Submission
from profiles.models import User
from announcements.models import Announcement, NewsPost

from django.shortcuts import render


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        data = Competition.objects.aggregate(
            count=Count('*'),
            published_comps=Count('pk', filter=Q(published=True)),
            unpublished_comps=Count('pk', filter=Q(published=False)),
        )

        public_competitions = data['published_comps']
        users = User.objects.all().count()
        submissions = Submission.objects.all().count()

        context['general_stats'] = [
            {'label': "Public Competitions", 'count': public_competitions},
            {'label': "Users", 'count': users},
            {'label': "Submissions", 'count': submissions},
        ]

        announcement = Announcement.objects.all().first()
        context['announcement'] = announcement.text if announcement else None

        news_posts = NewsPost.objects.all().order_by('-id')
        context['news_posts'] = news_posts

        return context


class OrganizeView(TemplateView):
    template_name = 'pages/organize.html'


class SearchView(TemplateView):
    template_name = 'search/form.html'


class ServerStatusView(TemplateView):
    template_name = 'pages/server_status.html'

    def get_context_data(self, *args, **kwargs):

        show_child_submissions = self.request.GET.get('show_child_submissions', False)

        # Get all submissions
        qs = Submission.objects.all()

        # Only if user is authenticated
        if self.request.user.is_authenticated:
            # If user is not super user then:
            # filter this user's own submissions
            # and
            # submissions running on queue which belongs to this user
            if not self.request.user.is_superuser:
                qs = qs.filter(
                    Q(owner=self.request.user) |
                    Q(phase__competition__queue__isnull=False, phase__competition__queue__owner=self.request.user)
                )
        else:
            qs = qs.none()  # This returns an empty queryset

        # Filter for fetching last 2 days submissions
        qs = qs.filter(created_when__gte=now() - timedelta(days=2))

        # Filter out child submissions i.e. submission has no parent
        if not show_child_submissions:
            qs = qs.filter(parent__isnull=True)

        qs = qs.order_by('-created_when')
        qs = qs.select_related('phase__competition', 'owner')

        context = super().get_context_data(*args, **kwargs)
        context['submissions'] = qs[:250]
        context['show_child_submissions'] = show_child_submissions

        for submission in context['submissions']:
            # Get filesize from each submissions's data
            submission.file_size = self.format_file_size(submission.data.file_size)

            # Get queue from each submission
            queue_name = ""
            # if submission has parent get queue from parent otherwise from the submission iteset
            if submission.parent:
                queue_name = "*" if submission.parent.queue is None else submission.parent.queue.name
            else:
                queue_name = "*" if submission.queue is None else submission.queue.name
            submission.competition_queue = queue_name

            # Add submission owner display name
            submission.owner_display_name = submission.owner.display_name if submission.owner.display_name else submission.owner.username

        return context

    def format_file_size(self, file_size):
        """
        A custom function to convert file size to KB, MB, GB and return with the unit
        """
        try:
            n = float(file_size)
        except Exception:
            return ""

        units = ['KB', 'MB', 'GB']
        i = 0
        while n >= 1000 and i < len(units) - 1:
            n /= 1000
            i += 1

        return f"{n:.1f} {units[i]}"


def page_not_found_view(request, exception):
    print(request)
    return render(request, '404.html', status=404)
