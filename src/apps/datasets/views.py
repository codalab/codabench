from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView

from datasets.models import Data
from utils.data import make_url_sassy
from api.serializers.datasets import DatasetSerializer


class DataManagement(LoginRequiredMixin, TemplateView):
    template_name = 'datasets/management.html'


class DatasetsPublic(TemplateView):
    template_name = 'datasets/public.html'


class DatasetCreate(LoginRequiredMixin, TemplateView):
    template_name = 'datasets/create.html'


class DatasetDetail(DetailView):
    queryset = Data.objects.filter(type__in=[Data.PUBLIC_DATA, Data.INPUT_DATA, Data.REFERENCE_DATA])
    template_name = 'datasets/detail.html'

    def get_object(self, *args, **kwargs):
        dataset = super().get_object(*args, **kwargs)

        # If dataset is public or (user is authenticated and is owner), return dataset
        if dataset.is_public or (
            self.request.user.is_authenticated and dataset.created_by == self.request.user
        ):
            return dataset

        # Otherwise return 404
        raise Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dataset = context["object"]

        serializer = DatasetSerializer(dataset)
        context["object"] = serializer.data
        return context


def download(request, key):
    data = get_object_or_404(Data, key=key)
    return HttpResponseRedirect(make_url_sassy(data.data_file.name))


def download_by_pk(request, pk):
    dataset = get_object_or_404(Data, pk=pk)

    if dataset.is_public or dataset.created_by == request.user:
        # Increment download count
        dataset.downloads = (dataset.downloads or 0) + 1
        dataset.save(update_fields=["downloads"])

        # Redirect to the actual file URL
        return HttpResponseRedirect(make_url_sassy(dataset.data_file.name))

    raise Http404()
