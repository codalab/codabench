from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import TemplateView
from django.db.models import Q

from competitions.models import Submission
from announcements.models import Announcement, NewsPost
from pages.home_page import get_featured_benchmarks, get_popular_benchmarks, get_recent_benchmarks
from pages.serializers import HomePageAnnouncementSerializer, HomePageNewsPostSerializer, HomePageBenchmarkSerializer

from utils.data import pretty_bytes


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Platform announcements are shown in the banner above the header, not here
        announcements = Announcement.objects.filter(
            is_active=True,
            placement=Announcement.PLACEMENT_HOME_PAGE,
        ).order_by("priority", "-created_when")
        context['announcements'] = HomePageAnnouncementSerializer(announcements, many=True).data

        # Only the latest posts are shown on the home page, the rest are on the news page
        news_posts = NewsPost.objects.all().order_by('-id')[:3]
        context['news_posts'] = HomePageNewsPostSerializer(news_posts, many=True).data

        # Recent leaves out the popular benchmarks so none is shown twice
        popular = get_popular_benchmarks()
        recent = get_recent_benchmarks(exclude_ids=[competition.id for competition in popular])
        context['featured_benchmarks'] = HomePageBenchmarkSerializer(get_featured_benchmarks(), many=True).data
        context['popular_benchmarks'] = HomePageBenchmarkSerializer(popular, many=True).data
        context['recent_benchmarks'] = HomePageBenchmarkSerializer(recent, many=True).data

        return context


class OrganizeView(TemplateView):
    template_name = 'pages/organize.html'


class SearchView(TemplateView):
    template_name = 'search/form.html'


class ServerStatusView(TemplateView):
    template_name = 'pages/server_status.html'

    def get_context_data(self, *args, **kwargs):

        show_child_submissions = self.request.GET.get('show_child_submissions', False)
        page = self.request.GET.get('page', 1)
        submissions_per_page = 50

        # Start with an empty queryset
        qs = Submission.objects.none()

        user = self.request.user
        # Only if user is authenticated
        if user.is_authenticated:
            # If user is not super user then filter:
            # - this user's own submissions
            # - submissions running on competitions where the user is owner or collaborator
            # - submissions running on queue where the user is owner or organizer
            # NOTE: exclude all soft-deleted submissions
            if not user.is_superuser:
                qs = Submission.objects.filter(is_soft_deleted=False).filter(
                    Q(owner=user) |
                    Q(phase__competition__created_by=user) |
                    Q(phase__competition__collaborators=user) |
                    Q(queue__owner=user, queue__isnull=False) |
                    Q(queue__organizers=user, queue__isnull=False)
                ).distinct()
            else:
                qs = Submission.objects.filter(is_soft_deleted=False)

        # Filter out child submissions i.e. submission has no parent
        if not show_child_submissions:
            qs = qs.filter(parent__isnull=True)

        qs = qs.order_by('-created_when')
        qs = qs.select_related('phase__competition', 'owner')

        # Paginate the queryset
        paginator = Paginator(qs, submissions_per_page)

        try:
            submissions = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            submissions = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results.
            submissions = paginator.page(paginator.num_pages)

        context = super().get_context_data(*args, **kwargs)
        context['submissions'] = submissions
        context['show_child_submissions'] = show_child_submissions

        for submission in context['submissions']:
            # Get filesize from each submissions's data
            if submission.data:
                submission.file_size = pretty_bytes(submission.data.file_size)
            else:
                submission.file_size = pretty_bytes(0)

            # Get queue from each submission
            submission.competition_queue = "*" if submission.queue is None else submission.queue.name

            # Add submission owner display name
            submission.owner_display_name = submission.owner.display_name if submission.owner.display_name else submission.owner.username

        context['paginator'] = paginator
        context['is_paginated'] = paginator.num_pages > 1

        return context


class MonitorQueuesView(TemplateView):
    template_name = 'pages/monitor_queues.html'
