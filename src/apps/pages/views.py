from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import TemplateView
from django.db.models import Q

from competitions.models import Submission
from announcements.models import Announcement, NewsPost

from django.shortcuts import render
from utils.data import pretty_bytes


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

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
        page = self.request.GET.get('page', 1)
        submissions_per_page = 50

        # Start with an empty queryset
        qs = Submission.objects.none()

        # Only if user is authenticated
        if self.request.user.is_authenticated:
            # If user is not super user then:
            # filter this user's own submissions
            # and
            # submissions running on queue which belongs to this user
            # NOTE: exclude all soft-deleted submissions
            if not self.request.user.is_superuser:
                qs = Submission.objects.filter(
                    Q(is_soft_deleted=False) &
                    (
                        Q(owner=self.request.user) |
                        Q(phase__competition__queue__isnull=False, phase__competition__queue__owner=self.request.user)
                    )
                )
            else:
                qs = Submission.objects.filter(
                    Q(is_soft_deleted=False)
                )

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
            queue_name = ""
            # if submission has parent get queue from parent otherwise from the submission iteset
            if submission.parent:
                queue_name = "*" if submission.parent.queue is None else submission.parent.queue.name
            else:
                queue_name = "*" if submission.queue is None else submission.queue.name
            submission.competition_queue = queue_name

            # Add submission owner display name
            submission.owner_display_name = submission.owner.display_name if submission.owner.display_name else submission.owner.username

        context['paginator'] = paginator
        context['is_paginated'] = paginator.num_pages > 1

        return context


class MonitorQueuesView(TemplateView):
    template_name = 'pages/monitor_queues.html'


def page_not_found_view(request, exception):
    print(request)
    return render(request, '404.html', status=404)
