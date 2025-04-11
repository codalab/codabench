from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from api.serializers.competitions import CompetitionParticipantSerializer
from competitions.emails import (
    send_participation_accepted_emails,
    send_participation_denied_emails,
    send_direct_participant_email
)
from competitions.models import CompetitionParticipant


class CompetitionParticipantViewSet(ModelViewSet):
    queryset = CompetitionParticipant.objects.all()
    serializer_class = CompetitionParticipantSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('user__username', 'user__email', 'status', 'competition', 'user__is_deleted')
    search_fields = ('user__username', 'user__email',)

    def get_queryset(self):

        # a boolean set to true if the request is considered valid
        # i.e. it is either GET request with `competition``
        # or patch request with `status`
        # or post request with `message`
        is_valid_request = False

        if self.request.method == "PATCH":
            # PATCH request is considered valid if it has `status`
            if 'status' in self.request.data:
                is_valid_request = True

        if self.request.method == "POST":
            # POST request is considered valid if it has `message`
            if 'message' in self.request.data:
                is_valid_request = True

        if self.request.method == "GET":
            # GET request is considered valid if it has `competition``
            # if there is no competition then it si called from /api/participants/
            # URL which is not considered valid
            if 'competition' in self.request.GET:
                is_valid_request = True

        if is_valid_request:
            # API to act normally i.e return participants
            qs = super().get_queryset()
            user = self.request.user
            if not user.is_superuser:
                qs = qs.filter(competition__in=user.competitions.all() | user.collaborations.all())
            qs = qs.select_related('user').order_by('user__username')
            return qs
        else:
            # API will work but will return empty participants list
            return CompetitionParticipant.objects.none()

    def update(self, request, *args, **kwargs):
        if request.method == 'PATCH' and 'status' in request.data:
            participation_status = request.data['status']
            participant = self.get_object()

            # Check if the new status is the same as the current status
            if participation_status == participant.status:
                return Response(
                    {"error": f"Status is already set to `{participation_status}`"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            emails = {
                'approved': send_participation_accepted_emails,
                'denied': send_participation_denied_emails,
            }
            if participation_status in emails:
                emails[participation_status](participant)

        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=('POST',))
    def send_email(self, request, pk):
        participant = self.get_object()
        competition = participant.competition
        if not competition.user_has_admin_permission(self.request.user):
            raise PermissionDenied('You do not have permission to email participants')
        try:
            message = request.data['message']
        except KeyError:
            return Response({'detail': 'A message is required to send an email'}, status=status.HTTP_400_BAD_REQUEST)
        send_direct_participant_email(participant=participant, content=message)
        return Response({}, status=status.HTTP_200_OK)
