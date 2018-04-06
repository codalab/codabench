from django.views.generic import TemplateView


class SubmissionsView(TemplateView):
    template_name = 'management/submissions.html'


class UserManagementView(TemplateView):
    template_name = 'management/user_management.html'
