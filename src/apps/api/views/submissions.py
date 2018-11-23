import uuid
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.serializers.submissions import SubmissionCreationSerializer, SubmissionSerializer
from competitions.models import Submission


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all()
    permission_classes = []
    # TODO! Security, who can access/delete/etc this?

    def check_object_permissions(self, request, obj):
        try:
            if uuid.UUID(request.data.get('secret')) != obj.secret:
                raise PermissionDenied("Submission secrets do not match")
        except TypeError:
            raise ValidationError("Secret not a valid UUID")

    def get_serializer_context(self):
        # Have to do this because of docs sending blank requests (?)
        if not self.request:
            return {}

        return {
            "owner": self.request.user
        }

    def get_serializer_class(self):
        if self.request and self.request.method == 'POST':
            return SubmissionCreationSerializer
        else:
            return SubmissionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user != instance.owner:
            raise PermissionDenied("Cannot interact with submission you did not make")

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
