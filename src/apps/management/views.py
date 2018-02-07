from django.views.generic import TemplateView


class SubmissionsView(TemplateView):
    template_name = 'management/submissions.html'
