from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from datasets.models import Data
from utils.data import make_url_sassy
from api.serializers.datasets import DatasetSerializer
from competitions.models import Competition, CompetitionParticipant

def user_can_download(user, data):
    if data.is_public:
        return True
    if not user.is_authenticated:
        return False
    if data.created_by == user:
        return True

    # Organizers (creator + collaborators) can download any dataset in their competition
    organizer_qs = Competition.objects.filter(
        Q(created_by=user) | Q(collaborators=user)
    ).filter(
        Q(phases__public_data=data) |
        Q(phases__starting_kit=data) |
        Q(phases__task_instances__task__input_data=data) |
        Q(phases__task_instances__task__reference_data=data) |
        Q(phases__task_instances__task__scoring_program=data) |
        Q(phases__task_instances__task__ingestion_program=data)
    )
    if data.type == Data.SUBMISSION and data.competition:
        organizer_qs = organizer_qs | Competition.objects.filter(
            Q(created_by=user) | Q(collaborators=user),
            pk=data.competition_id,
        )
    if organizer_qs.exists():
        return True

    # Reference data and solutions are never accessible to participants
    if data.type in (Data.REFERENCE_DATA, Data.SOLUTION, Data.SUBMISSION, Data.COMPETITION_BUNDLE):
        return False

    approved_participant = Q(
        participants__user=user,
        participants__status=CompetitionParticipant.APPROVED,
    )

    if data.type in (Data.PUBLIC_DATA, Data.STARTING_KIT):
        return Competition.objects.filter(approved_participant).filter(
            Q(phases__public_data=data) | Q(phases__starting_kit=data)
        ).exists()

    if data.type == Data.INPUT_DATA:
        return Competition.objects.filter(approved_participant, make_input_data_available=True).filter(
            phases__task_instances__task__input_data=data
        ).exists()

    if data.type in (Data.SCORING_PROGRAM, Data.INGESTION_PROGRAM):
        return Competition.objects.filter(approved_participant, make_programs_available=True).filter(
            Q(phases__task_instances__task__scoring_program=data) |
            Q(phases__task_instances__task__ingestion_program=data)
        ).exists()

    return False


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
    if not user_can_download(request.user, data):
        if request.user.is_authenticated:
            raise PermissionDenied()
        raise Http404()
    return HttpResponseRedirect(make_url_sassy(data.data_file.name))


def download_by_pk(request, pk):
    dataset = get_object_or_404(Data, pk=pk)
    if not user_can_download(request.user, dataset):
        if request.user.is_authenticated:
            raise PermissionDenied()
        raise Http404()
    dataset.downloads = (dataset.downloads or 0) + 1
    dataset.save(update_fields=["downloads"])
    return HttpResponseRedirect(make_url_sassy(dataset.data_file.name))
