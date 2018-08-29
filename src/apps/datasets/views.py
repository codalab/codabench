from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from datasets.models import Data
from utils.data import _make_url_sassy


class DataManagement(LoginRequiredMixin, TemplateView):
    template_name = 'datasets/management.html'


def download(request, key):
    data = get_object_or_404(Data, key=key)
    if settings.STORAGE_IS_LOCAL:
        try:
            return FileResponse(open(data.data_file.path, 'rb'), as_attachment=True)
        except FileNotFoundError:
            raise Http404()
    else:
        return HttpResponseRedirect(_make_url_sassy(data.data_file.name))
        # raise NotImplementedError()
