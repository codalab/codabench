from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView, DetailView

from .models import Competition, CompetitionParticipant
from django.core.serializers.json import DjangoJSONEncoder

from django.db.models import Q
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from django.contrib import messages


from profiles.models import CustomGroup, User
from queues.models import Queue



class CompetitionManagement(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/management.html'


class CompetitionPublic(TemplateView):
    template_name = 'competitions/public.html'


class CompetitionCreateForm(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/form.html'


class CompetitionUpdateForm(LoginRequiredMixin, DetailView):
    template_name = 'competitions/form.html'
    queryset = Competition.objects.all()


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        comp = self.object

        groups_qs = CustomGroup.objects.filter(
            Q(id__in=comp.participant_groups.values_list('id', flat=True))
        ).select_related('queue').prefetch_related('user_set')

        participant_user_ids = list(
            CompetitionParticipant.objects.filter(competition=comp)
            .values_list('user_id', flat=True)
        )

        ctx['available_groups_json'] = json.dumps([
            {
                'id': g.id,
                'name': g.name,
                'queue': g.queue.name if g.queue else None,
                'members': [u.username for u in g.user_set.filter(pk__in=participant_user_ids)],
            }
            for g in groups_qs
        ], cls=DjangoJSONEncoder)

        ctx['selected_group_ids_json'] = json.dumps(
            list(comp.participant_groups.values_list('id', flat=True)),
            cls=DjangoJSONEncoder
        )

        ctx['available_queues_json'] = json.dumps(
            list(Queue.objects.all().values('id', 'name')),
            cls=DjangoJSONEncoder
        )

        ctx['available_users_json'] = json.dumps(
            list(
                User.objects
                    .filter(pk__in=participant_user_ids, is_active=True)
                    .values('id', 'username', 'email')
            ),
            cls=DjangoJSONEncoder
        )
        return ctx

    def get_object(self, *args, **kwargs):
        competition = super().get_object(*args, **kwargs)

        is_admin, is_creator, is_collaborator = False, False, False

        # check if user is loggedin
        if self.request.user.is_authenticated:

            # check if user is admin
            is_admin = self.request.user.is_superuser

            # check if user is the creator of this competition
            is_creator = self.request.user == competition.created_by

            # check if user is collaborator of this competition
            is_collaborator = self.request.user in competition.collaborators.all()

        if (
            is_admin or
            is_creator or
            is_collaborator
        ):
            return competition
        raise Http404()


class CompetitionUpload(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/upload.html'


class CompetitionDetail(DetailView):
    queryset = Competition.objects.all()
    template_name = 'competitions/detail.html'

    def get_object(self, *args, **kwargs):
        competition = super().get_object(*args, **kwargs)

        is_admin, is_creator, is_collaborator, is_participant = False, False, False, False

        # check if user is loggedin
        if self.request.user.is_authenticated:

            # check if user is admin
            is_admin = self.request.user.is_superuser

            # check if user is the creator of this competition
            is_creator = self.request.user == competition.created_by

            # check if user is collaborator of this competition
            is_collaborator = self.request.user in competition.collaborators.all()

            # check if user is a participant of this competition
            # get participants from CompetitionParticipant where user=user and competition=competition
            is_participant = CompetitionParticipant.objects.filter(user=self.request.user, competition=competition).count() > 0

        # check if secret key provided is valid, 
        valid_secret_key = self.request.GET.get('secret_key') == str(competition.secret_key)

        if (
            is_admin or
            is_creator or
            is_collaborator or
            competition.published or
            valid_secret_key or
            is_participant
        ):
            return competition
        raise Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the secret_key from the request.GET dictionary
        secret_key = self.request.GET.get('secret_key')

        # Add the secret_key to the context dictionary
        context['secret_key'] = secret_key

        return context


class CompetitionDetailedResults(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/detailed_results.html'


@login_required
@require_POST
def competition_create_group(request, pk):
    competition = get_object_or_404(Competition, pk=pk)

    user = request.user
    if not (user.is_superuser or user == competition.created_by or user in competition.collaborators.all()):
        return HttpResponseForbidden("Not allowed")

    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode())
        except Exception:
            return HttpResponseBadRequest("Invalid JSON")
        name = (payload.get('name') or '').strip()
        queue_id = payload.get('queue_id')
        user_ids = payload.get('user_ids') or []
    else:
        name = (request.POST.get('name') or '').strip()
        queue_id = request.POST.get('queue_id') or None
        user_ids = request.POST.getlist('user_ids') or []
        if not user_ids and request.POST.get('user_ids'):
            user_ids = [u.strip() for u in request.POST.get('user_ids').split(',') if u.strip()]

    if not name:
        return HttpResponseBadRequest("Missing name")

    allowed_user_ids = set(
        CompetitionParticipant.objects.filter(competition=competition)
        .values_list('user_id', flat=True)
    )

    try:
        with transaction.atomic():
            group = CustomGroup(name=name)
            if queue_id:
                try:
                    queue = Queue.objects.get(pk=queue_id)
                    group.queue = queue
                except Queue.DoesNotExist:
                    group.queue = None
            group.save()

            user_ids_int = []
            try:
                user_ids_int = [int(u) for u in user_ids]
            except Exception:
                user_ids_int = []

            if user_ids_int:
                invalid = [uid for uid in user_ids_int if uid not in allowed_user_ids]
                if invalid:
                    raise ValueError(f"Some users are not participants of this competition: {invalid}")

                users_qs = User.objects.filter(pk__in=user_ids_int)
                group.user_set.set(users_qs)

            competition.participant_groups.add(group)

            members = list(group.user_set.values_list('username', flat=True))
            group_data = {
                'id': group.id,
                'name': group.name,
                'queue': group.queue.name if group.queue else None,
                'members': members,
            }
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest("Error creating group: %s" % str(e))

    if (
        request.content_type.startswith('application/json')
        or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
    ):
        return JsonResponse({'status': 'ok', 'group': group_data})


    messages.success(request, "Groupe créé")
    return HttpResponseRedirect(reverse('competitions:edit', kwargs={'pk': competition.pk}))


@login_required
@require_POST
def competition_update_group(request, pk, group_id):
    competition = get_object_or_404(Competition, pk=pk)
    group = get_object_or_404(CustomGroup, pk=group_id)

    user = request.user
    if not (user.is_superuser or user == competition.created_by or user in competition.collaborators.all()):
        return HttpResponseForbidden("Not allowed")

    if not competition.participant_groups.filter(pk=group.pk).exists():
        return HttpResponseBadRequest("Group does not belong to this competition")

    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode())
        except Exception:
            return HttpResponseBadRequest("Invalid JSON")
        name = (payload.get('name') or '').strip()
        queue_id = payload.get('queue_id')
        user_ids = payload.get('user_ids', []) or []
    else:
        name = (request.POST.get('name') or '').strip()
        queue_id = request.POST.get('queue_id') or None
        user_ids = request.POST.getlist('user_ids[]') or []
        if not user_ids and request.POST.get('user_ids'):
            user_ids = [u.strip() for u in request.POST.get('user_ids').split(',') if u.strip()]

    if not name:
        return HttpResponseBadRequest("Missing name")

    allowed_user_ids = set(
        CompetitionParticipant.objects.filter(competition=competition)
        .values_list('user_id', flat=True)
    )

    try:
        with transaction.atomic():
            group.name = name
            if queue_id:
                group.queue = Queue.objects.filter(pk=queue_id).first()
            else:
                group.queue = None
            group.save()

            try:
                user_ids_int = [int(u) for u in user_ids]
            except Exception:
                user_ids_int = []

            if user_ids_int:
                invalid = [uid for uid in user_ids_int if uid not in allowed_user_ids]
                if invalid:
                    raise ValueError(f"Some users are not participants of this competition: {invalid}")

            group.user_set.set(User.objects.filter(pk__in=user_ids_int))
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest("Error updating group: %s" % str(e))

    resp = {
        'status': 'ok',
        'group': {
            'id': group.id,
            'name': group.name,
            'queue': group.queue.name if group.queue else None,
            'members': list(group.user_set.values_list('username', flat=True)),
        }
    }

    if (
        request.content_type.startswith('application/json')
        or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
    ):
        return JsonResponse(resp)


    messages.success(request, "Groupe modifié")
    return HttpResponseRedirect(reverse('competitions:edit', kwargs={'pk': competition.pk}))


@login_required
@require_POST
def competition_delete_group(request, pk, group_id):
    competition = get_object_or_404(Competition, pk=pk)
    group = get_object_or_404(CustomGroup, pk=group_id)

    user = request.user
    if not (user.is_superuser or user == competition.created_by or user in competition.collaborators.all()):
        return HttpResponseForbidden("Not allowed")

    if not competition.participant_groups.filter(pk=group.pk).exists():
        return HttpResponseBadRequest("Group does not belong to this competition")

    try:
        with transaction.atomic():
            competition.participant_groups.remove(group)
            group.delete()
    except Exception as e:
        return HttpResponseBadRequest("Error deleting group: %s" % str(e))

    if (
        request.content_type.startswith('application/json')
        or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
    ):
        return JsonResponse({'status': 'ok', 'group_id': group_id})


    messages.success(request, "Groupe supprimé")
    return HttpResponseRedirect(reverse('competitions:edit', kwargs={'pk': competition.pk}))
