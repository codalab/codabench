from django.core import mail
from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse

from consulting.models import ConsultingListing
from factories import ConsultingListingFactory, UserFactory


class ConsultingListingAdminTests(TestCase):
    """Covers the review of listings in Django admin and the emails sent to the owner."""

    def setUp(self):
        self.admin = UserFactory(super_user=True)
        self.client.force_login(self.admin)
        self.listing = ConsultingListingFactory(status=ConsultingListing.STATUS_PENDING)
        self.change_url = reverse('admin:consulting_consultinglisting_change', args=[self.listing.pk])
        self.changelist_url = reverse('admin:consulting_consultinglisting_changelist')

    def _form_data(self, **overrides):
        data = {
            'owner': self.listing.owner.pk,
            'title': self.listing.title,
            'website_url': self.listing.website_url,
            'linkedin_url': self.listing.linkedin_url,
            'github_url': self.listing.github_url,
            'description': self.listing.description,
            'status': self.listing.status,
            'rejection_reason': self.listing.rejection_reason,
            'is_active': 'on',
            'created_when_0': self.listing.created_when.strftime('%Y-%m-%d'),
            'created_when_1': self.listing.created_when.strftime('%H:%M:%S'),
        }
        data.update(overrides)
        return data

    def test_approve_in_form_emails_owner(self):
        """
        Sets the status to approved in the admin change form and checks the listing
        is saved as approved and one approval email is sent to the owner.
        """
        response = self.client.post(self.change_url, self._form_data(status=ConsultingListing.STATUS_APPROVED))

        self.assertRedirects(response, self.changelist_url)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ConsultingListing.STATUS_APPROVED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.listing.owner.email])
        self.assertIn('approved', mail.outbox[0].subject)

    def test_reject_requires_reason(self):
        """
        Sets the status to rejected in the admin change form without a reason and
        checks the form shows an error on the reason, the listing stays pending and
        no email is sent.
        """
        response = self.client.post(self.change_url, self._form_data(status=ConsultingListing.STATUS_REJECTED))

        self.assertEqual(response.status_code, 200)
        self.assertIn('rejection_reason', response.context['adminform'].form.errors)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ConsultingListing.STATUS_PENDING)
        self.assertEqual(len(mail.outbox), 0)

    def test_reject_with_reason_emails_owner_the_reason(self):
        """
        Sets the status to rejected with a reason in the admin change form and
        checks both are saved and the owner gets one email containing the reason.
        """
        response = self.client.post(self.change_url, self._form_data(
            status=ConsultingListing.STATUS_REJECTED,
            rejection_reason='Not related to Codabench',
        ))

        self.assertRedirects(response, self.changelist_url)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ConsultingListing.STATUS_REJECTED)
        self.assertEqual(self.listing.rejection_reason, 'Not related to Codabench')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.listing.owner.email])
        self.assertIn('rejected', mail.outbox[0].subject)
        self.assertIn('Not related to Codabench', mail.outbox[0].body)

    def test_toggling_is_active_sends_no_email(self):
        """
        Unchecks is_active on an approved listing in the admin change form and
        checks the listing is deactivated, stays approved and no email is sent.
        """
        self.listing.status = ConsultingListing.STATUS_APPROVED
        self.listing.save()
        data = self._form_data()
        del data['is_active']

        response = self.client.post(self.change_url, data)

        self.assertRedirects(response, self.changelist_url)
        self.listing.refresh_from_db()
        self.assertFalse(self.listing.is_active)
        self.assertEqual(self.listing.status, ConsultingListing.STATUS_APPROVED)
        self.assertEqual(len(mail.outbox), 0)

    def test_approve_action_approves_and_emails_owners(self):
        """
        The "Approve selected listings" action approves the pending and rejected
        listings it is given (clearing the old reason) and emails each owner once.
        Already approved listings are left alone and get no email.
        """
        rejected = ConsultingListingFactory(status=ConsultingListing.STATUS_REJECTED, rejection_reason='Too short')
        already_approved = ConsultingListingFactory(status=ConsultingListing.STATUS_APPROVED)

        response = self.client.post(self.changelist_url, {
            'action': 'approve_listings',
            '_selected_action': [self.listing.pk, rejected.pk, already_approved.pk],
        })

        self.assertRedirects(response, self.changelist_url)
        self.listing.refresh_from_db()
        rejected.refresh_from_db()
        self.assertEqual(self.listing.status, ConsultingListing.STATUS_APPROVED)
        self.assertEqual(rejected.status, ConsultingListing.STATUS_APPROVED)
        self.assertEqual(rejected.rejection_reason, '')
        recipients = [email.to[0] for email in mail.outbox]
        self.assertCountEqual(recipients, [self.listing.owner.email, rejected.owner.email])

    def test_delete_selected_action_removes_picture_files(self):
        """
        Deletes a listing with the admin "delete selected" action (a bulk delete)
        and checks both the listing and its picture file in storage are removed.
        """
        picture_name = self.listing.picture.name
        self.assertTrue(default_storage.exists(picture_name))

        response = self.client.post(self.changelist_url, {
            'action': 'delete_selected',
            '_selected_action': [self.listing.pk],
            'post': 'yes',
        })

        self.assertRedirects(response, self.changelist_url)
        self.assertFalse(ConsultingListing.objects.filter(pk=self.listing.pk).exists())
        self.assertFalse(default_storage.exists(picture_name))
