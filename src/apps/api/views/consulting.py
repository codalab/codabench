from django.db.models.functions import Lower
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import LargePagination
from api.serializers.consulting import ConsultingListingSerializer, MyConsultingListingSerializer
from consulting.emails import send_listing_submitted_email, send_listing_deleted_email
from consulting.models import ConsultingListing


class ConsultingListingListView(generics.ListAPIView):
    serializer_class = ConsultingListingSerializer
    permission_classes = (AllowAny,)
    pagination_class = LargePagination

    # Oldest/newest go by id (the order listings were added in), not by created_when
    ORDERINGS = {
        'oldest': ('id',),
        'newest': ('-id',),
        'alphabetical': (Lower('title'), 'id'),
    }

    def get_queryset(self):
        # e.g. ?ordering=alphabetical
        ordering = self.request.query_params.get('ordering') or 'oldest'
        if ordering not in self.ORDERINGS:
            raise ValidationError({'ordering': f"Expected one of: {', '.join(self.ORDERINGS)}"})

        return ConsultingListing.objects.filter(
            status=ConsultingListing.STATUS_APPROVED,
            is_active=True,
        ).order_by(*self.ORDERINGS[ordering])


class MyConsultingListingView(APIView):
    """
    The logged-in user's own listing (one per user).

    POST and PATCH take multipart form data, with the picture as a file. The picture
    is not sent as base64 in JSON like other images. Allowed size for picture is 5 MB.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = MyConsultingListingSerializer

    def get_listing(self):
        return ConsultingListing.objects.filter(owner=self.request.user).first()

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', {'request': self.request})
        return self.serializer_class(*args, **kwargs)

    def get(self, request):
        """Returns the user's listing in any status, or an empty 204 if they have none."""
        listing = self.get_listing()
        if listing is None:
            # Not a 404: having no listing yet is a normal state for the consulting pages
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(self.get_serializer(listing).data)

    def post(self, request):
        """Creates the user's listing as pending and emails the superusers. Refused if they already have one."""
        if self.get_listing() is not None:
            raise ValidationError({'detail': 'You already have a consulting listing.'})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = serializer.save(owner=request.user)
        send_listing_submitted_email(request=request, listing=listing)
        return Response(self.get_serializer(listing).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        """
        Edits the user's listing, sends it back to pending and emails the superusers.
        Refused while the listing is pending.
        """
        listing = self.get_listing()
        if listing is None:
            raise NotFound('You do not have a consulting listing.')
        if listing.status == ConsultingListing.STATUS_PENDING:
            raise ValidationError({'detail': 'Your listing is pending review. You cannot edit it until an admin has reviewed it.'})

        serializer = self.get_serializer(listing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # Any edit has to be reviewed again
        listing = serializer.save(status=ConsultingListing.STATUS_PENDING, rejection_reason='')
        send_listing_submitted_email(request=request, listing=listing, resubmitted=True)
        return Response(self.get_serializer(listing).data)

    def delete(self, request):
        """Deletes the user's listing (and its picture) and emails the superusers."""
        listing = self.get_listing()
        if listing is None:
            raise NotFound('You do not have a consulting listing.')

        title = listing.title
        listing.delete()
        send_listing_deleted_email(request=request, owner=request.user, title=title)
        return Response(status=status.HTTP_204_NO_CONTENT)
