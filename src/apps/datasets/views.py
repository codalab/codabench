from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from datasets.models import Data


class DataManagement(LoginRequiredMixin, TemplateView):
    template_name = 'datasets/management.html'


def download(request, key):
    # TODO: This should redirect to the proper storage with a SAS
    if 'FileSystemStorage' in settings.DEFAULT_FILE_STORAGE:
        data = get_object_or_404(Data, key=key)
        try:
            return FileResponse(open(data.data_file.path, 'rb'), as_attachment=True)
        except FileNotFoundError:
            raise Http404()
    else:
        raise NotImplementedError()
