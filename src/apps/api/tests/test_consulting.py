import io
import os

from django.core import mail
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from consulting.models import ConsultingListing
from factories import ConsultingListingFactory, UserFactory


def _picture(file_name='picture.png', over_size_limit=False):
    """Builds an uploaded PNG file: a small one, or one a little under 6 MB"""
    buffer = io.BytesIO()
    if over_size_limit:
        # Random pixels don't compress, so this PNG is a little under 6 MB
        Image.frombytes('RGB', (1400, 1400), os.urandom(1400 * 1400 * 3)).save(buffer, format='PNG')
    else:
        Image.new('RGB', (10, 10), color='blue').save(buffer, format='PNG')
    return SimpleUploadedFile(file_name, buffer.getvalue(), content_type='image/png')


class ConsultingListingListTests(TestCase):
    """Covers the public list endpoint: visibility, ordering and pagination."""

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse('consulting_listing_list')  # /api/consulting/
        # Created in this order, so their ids go up from first to third
        self.approved_first = ConsultingListingFactory(title='Zeta Consulting', status=ConsultingListing.STATUS_APPROVED)
        self.approved_second = ConsultingListingFactory(title='alpha Consulting', status=ConsultingListing.STATUS_APPROVED)
        self.approved_third = ConsultingListingFactory(title='Mu Consulting', status=ConsultingListing.STATUS_APPROVED)
        self.pending = ConsultingListingFactory(status=ConsultingListing.STATUS_PENDING)
        self.rejected = ConsultingListingFactory(status=ConsultingListing.STATUS_REJECTED, rejection_reason='Not relevant')
        self.inactive = ConsultingListingFactory(status=ConsultingListing.STATUS_APPROVED, is_active=False)

    def _ids(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return [result['id'] for result in response.data['results']]

    def test_list_is_public_and_only_shows_approved_active_listings(self):
        """
        Calls the list endpoint without logging in and checks only the approved and
        active listings come back - pending, rejected and inactive ones are left out.
        """
        ids = self._ids(self.list_url)

        self.assertCountEqual(ids, [self.approved_first.id, self.approved_second.id, self.approved_third.id])

    def test_list_does_not_expose_review_fields(self):
        """
        Calls the list endpoint and checks each result holds the listing content
        (title, picture, links, description) but not the review fields (status,
        rejection reason, is_active) or the owner.
        """
        response = self.client.get(self.list_url)

        result = next(r for r in response.data['results'] if r['id'] == self.approved_first.id)
        self.assertEqual(result['title'], 'Zeta Consulting')
        for key in ('picture', 'website_url', 'linkedin_url', 'github_url', 'description', 'created_when'):
            self.assertIn(key, result)
        for key in ('status', 'rejection_reason', 'is_active', 'owner'):
            self.assertNotIn(key, result)

    def test_default_ordering_is_first_added_first(self):
        """
        Calls the list endpoint without an ordering parameter and checks the
        listings come back oldest first (lowest id first).
        """
        ids = self._ids(self.list_url)

        self.assertEqual(ids, [self.approved_first.id, self.approved_second.id, self.approved_third.id])

    def test_newest_ordering(self):
        """
        Calls the list endpoint with ?ordering=newest and checks the listings come
        back with the most recently added one first (highest id first).
        """
        ids = self._ids(f'{self.list_url}?ordering=newest')

        self.assertEqual(ids, [self.approved_third.id, self.approved_second.id, self.approved_first.id])

    def test_alphabetical_ordering_ignores_case(self):
        """
        Calls the list endpoint with ?ordering=alphabetical and checks the listings
        come back sorted by title ignoring case: 'alpha' before 'Mu' before 'Zeta'.
        """
        ids = self._ids(f'{self.list_url}?ordering=alphabetical')

        self.assertEqual(ids, [self.approved_second.id, self.approved_third.id, self.approved_first.id])

    def test_invalid_ordering_is_rejected(self):
        """
        Calls the list endpoint with an unknown ordering value and checks the
        response is a 400 with an error on 'ordering', instead of it being ignored.
        """
        response = self.client.get(f'{self.list_url}?ordering=random')

        self.assertEqual(response.status_code, 400)
        self.assertIn('ordering', response.data)

    def test_list_is_paginated_with_20_per_page(self):
        """
        Adds enough listings to go over one page and checks the first page holds 20
        of them and the response has the pagination fields.
        """
        ConsultingListingFactory.create_batch(20, status=ConsultingListing.STATUS_APPROVED)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 23)
        self.assertEqual(response.data['page_size'], 20)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(len(self._ids(f'{self.list_url}?page=2')), 3)


class MyConsultingListingTests(TestCase):
    """Covers the owner's endpoint: create, read, edit and delete of their own listing."""

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse('consulting_listing_list')  # /api/consulting/
        self.my_listing_url = reverse('my_consulting_listing')  # /api/consulting/mine/
        self.user = UserFactory()
        self.admin = UserFactory(super_user=True)
        self.client.force_authenticate(self.user)
        self.data = {
            'title': 'My Consulting',
            'picture': _picture(),
            'website_url': 'https://example.org',
            'linkedin_url': '',
            'github_url': '',
            'description': 'I help with **benchmarks**.',
        }

    def test_anonymous_user_cannot_use_endpoint(self):
        """
        Calls GET, POST, PATCH and DELETE on the owner endpoint without logging in
        and checks each one is refused (401/403) and no listing gets created.
        """
        self.client.force_authenticate(None)

        self.assertIn(self.client.get(self.my_listing_url).status_code, (401, 403))
        self.assertIn(self.client.post(self.my_listing_url, self.data, format='multipart').status_code, (401, 403))
        self.assertIn(self.client.patch(self.my_listing_url, {'title': 'x'}, format='multipart').status_code, (401, 403))
        self.assertIn(self.client.delete(self.my_listing_url).status_code, (401, 403))
        self.assertEqual(ConsultingListing.objects.count(), 0)

    def test_get_without_listing_returns_no_content(self):
        """
        Calls GET as a user that has no listing and checks the response is an
        empty 204, not a 404.
        """
        response = self.client.get(self.my_listing_url)

        self.assertEqual(response.status_code, 204)

    def test_get_returns_own_listing_with_review_fields(self):
        """
        Calls GET as a user whose listing was rejected and checks they get their
        own listing (not someone else's) with its status, rejection reason and is_active.
        """
        ConsultingListingFactory(owner=self.user, status=ConsultingListing.STATUS_REJECTED, rejection_reason='Too short')
        ConsultingListingFactory()  # someone else's listing

        response = self.client.get(self.my_listing_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], ConsultingListing.STATUS_REJECTED)
        self.assertEqual(response.data['rejection_reason'], 'Too short')
        self.assertTrue(response.data['is_active'])

    def test_create_makes_pending_listing_and_emails_superusers(self):
        """
        Creating a listing stores it as pending for the logged-in user and sends
        one email to the superusers.
        """
        response = self.client.post(self.my_listing_url, self.data, format='multipart')

        self.assertEqual(response.status_code, 201)
        listing = ConsultingListing.objects.get(owner=self.user)
        self.assertEqual(listing.title, 'My Consulting')
        self.assertEqual(listing.status, ConsultingListing.STATUS_PENDING)
        self.assertTrue(listing.picture)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.admin.email])
        self.assertIn(self.user.username, mail.outbox[0].subject)

    def test_create_cannot_set_review_fields(self):
        """
        Creates a listing while also sending status, rejection reason and is_active
        and checks those are ignored: the listing is saved as pending, active and
        with no rejection reason.
        """
        self.data.update({'status': ConsultingListing.STATUS_APPROVED, 'rejection_reason': 'x', 'is_active': False})

        response = self.client.post(self.my_listing_url, self.data, format='multipart')

        self.assertEqual(response.status_code, 201)
        listing = ConsultingListing.objects.get(owner=self.user)
        self.assertEqual(listing.status, ConsultingListing.STATUS_PENDING)
        self.assertEqual(listing.rejection_reason, '')
        self.assertTrue(listing.is_active)

    def test_create_requires_title_picture_and_description(self):
        """
        Creates a listing with only a link, then with an empty picture, and checks
        both are refused with a 400 naming the missing required fields (title,
        picture, description) and no listing gets created.
        """
        response = self.client.post(self.my_listing_url, {'website_url': 'https://example.org'}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertCountEqual(response.data.keys(), ['title', 'picture', 'description'])

        self.data['picture'] = ''
        response = self.client.post(self.my_listing_url, self.data, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertCountEqual(response.data.keys(), ['picture'])
        self.assertEqual(ConsultingListing.objects.count(), 0)

    def test_create_rejects_picture_over_5mb(self):
        """
        Creates a listing with a picture larger than 5 MB and checks the response
        is a 400 with an error on the picture and no listing gets created.
        """
        self.data['picture'] = _picture(over_size_limit=True)

        response = self.client.post(self.my_listing_url, self.data, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertIn('5 MB', response.data['picture'][0])
        self.assertEqual(ConsultingListing.objects.count(), 0)

    def test_create_rejects_invalid_url(self):
        """
        Creates a listing with a LinkedIn link that is not a valid URL and checks
        the response is a 400 with an error on that field.
        """
        self.data['linkedin_url'] = 'not a url'

        response = self.client.post(self.my_listing_url, self.data, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertIn('linkedin_url', response.data)

    def test_only_one_listing_per_user(self):
        """
        Creates a listing as a user that already has one and checks the response
        is a 400 and the user still has only one listing.
        """
        ConsultingListingFactory(owner=self.user)

        response = self.client.post(self.my_listing_url, self.data, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ConsultingListing.objects.filter(owner=self.user).count(), 1)

    def test_edit_approved_listing_sends_it_back_to_pending(self):
        """
        Editing an approved listing saves the change, moves it back to pending
        (so it leaves the public list) and emails the superusers.
        """
        listing = ConsultingListingFactory(owner=self.user, status=ConsultingListing.STATUS_APPROVED)

        response = self.client.patch(self.my_listing_url, {'title': 'New title'}, format='multipart')

        self.assertEqual(response.status_code, 200)
        listing.refresh_from_db()
        self.assertEqual(listing.title, 'New title')
        self.assertEqual(listing.status, ConsultingListing.STATUS_PENDING)
        self.assertTrue(listing.picture)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.admin.email])
        self.assertEqual(self.client.get(self.list_url).data['count'], 0)

    def test_edit_rejected_listing_clears_rejection_reason(self):
        """
        Edits a rejected listing and checks it moves back to pending and the old
        rejection reason is cleared.
        """
        listing = ConsultingListingFactory(owner=self.user, status=ConsultingListing.STATUS_REJECTED, rejection_reason='Too short')

        response = self.client.patch(self.my_listing_url, {'description': 'A longer description'}, format='multipart')

        self.assertEqual(response.status_code, 200)
        listing.refresh_from_db()
        self.assertEqual(listing.status, ConsultingListing.STATUS_PENDING)
        self.assertEqual(listing.rejection_reason, '')

    def test_edit_can_replace_picture(self):
        """
        Edits an approved listing sending only a new picture and checks the stored
        picture is replaced by the new file.
        """
        listing = ConsultingListingFactory(owner=self.user, status=ConsultingListing.STATUS_APPROVED)
        old_picture_name = listing.picture.name

        response = self.client.patch(self.my_listing_url, {'picture': _picture('new_picture.png')}, format='multipart')

        self.assertEqual(response.status_code, 200)
        listing.refresh_from_db()
        self.assertNotEqual(listing.picture.name, old_picture_name)
        self.assertIn('new_picture', listing.picture.name)

    def test_cannot_edit_pending_listing(self):
        """
        Edits a listing that is still pending and checks the response is a 400
        saying it is pending review, the listing is unchanged and no email is sent.
        """
        listing = ConsultingListingFactory(owner=self.user, title='Original', status=ConsultingListing.STATUS_PENDING)

        response = self.client.patch(self.my_listing_url, {'title': 'New title'}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertIn('pending review', response.data['detail'])
        listing.refresh_from_db()
        self.assertEqual(listing.title, 'Original')
        self.assertEqual(len(mail.outbox), 0)

    def test_can_edit_inactive_listing(self):
        """
        Edits an approved listing that an admin has deactivated (is_active False)
        and checks it is saved like any other edit: the change is stored, the
        listing goes back to pending and it stays deactivated.
        """
        listing = ConsultingListingFactory(
            owner=self.user, title='Original', status=ConsultingListing.STATUS_APPROVED, is_active=False
        )

        response = self.client.patch(self.my_listing_url, {'title': 'New title'}, format='multipart')

        self.assertEqual(response.status_code, 200)
        listing.refresh_from_db()
        self.assertEqual(listing.title, 'New title')
        self.assertEqual(listing.status, ConsultingListing.STATUS_PENDING)
        self.assertFalse(listing.is_active)

    def test_edit_without_listing_returns_404(self):
        """
        Tries to edit when the user has no listing and checks the response is a
        404 and no listing gets created.
        """
        response = self.client.patch(self.my_listing_url, {'title': 'New title'}, format='multipart')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ConsultingListing.objects.count(), 0)

    def test_delete_removes_listing_and_emails_superusers(self):
        """
        Deleting removes only the owner's listing (allowed in any status, here
        pending) and its picture file from storage, and emails the superusers
        with the username and title. Someone else's listing and picture are kept.
        """
        listing = ConsultingListingFactory(owner=self.user, title='To remove', status=ConsultingListing.STATUS_PENDING)
        other_listing = ConsultingListingFactory()
        picture_name = listing.picture.name
        self.assertTrue(default_storage.exists(picture_name))

        response = self.client.delete(self.my_listing_url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(default_storage.exists(picture_name))
        self.assertTrue(default_storage.exists(other_listing.picture.name))
        self.assertFalse(ConsultingListing.objects.filter(owner=self.user).exists())
        self.assertTrue(ConsultingListing.objects.filter(pk=other_listing.pk).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.admin.email])
        self.assertIn(self.user.username, mail.outbox[0].subject)
        self.assertIn('To remove', mail.outbox[0].body)

    def test_can_delete_inactive_listing(self):
        """
        Deletes a listing that an admin has deactivated (is_active False) and
        checks it is removed like any other listing, with a 204 response.
        """
        listing = ConsultingListingFactory(owner=self.user, status=ConsultingListing.STATUS_APPROVED, is_active=False)

        response = self.client.delete(self.my_listing_url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(ConsultingListing.objects.filter(pk=listing.pk).exists())

    def test_delete_without_listing_returns_404(self):
        """
        Tries to delete when the user has no listing and checks the response is a
        404 and no email is sent to the superusers.
        """
        response = self.client.delete(self.my_listing_url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(mail.outbox), 0)

    def test_emails_go_to_superusers_only(self):
        """
        Creates a listing when there are two superusers and one staff user that is
        not a superuser, and checks the notification goes to the two superusers only.
        """
        staff_user = UserFactory()
        staff_user.is_staff = True
        staff_user.save()
        other_admin = UserFactory(super_user=True)

        self.client.post(self.my_listing_url, self.data, format='multipart')

        self.assertEqual(len(mail.outbox), 1)
        self.assertCountEqual(mail.outbox[0].to, [self.admin.email, other_admin.email])
