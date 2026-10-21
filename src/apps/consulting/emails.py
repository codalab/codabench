from django.contrib.auth import get_user_model

from utils.email import codalab_send_mail, get_link_context


# Starts the subject of every consulting email
SUBJECT_PREFIX = '[Codabench Consulting]'


def get_superuser_emails():
    User = get_user_model()
    return list(User.objects.filter(is_superuser=True, is_deleted=False).values_list('email', flat=True))


def _send_to_superusers(request, context, subject, template):
    to_email = get_superuser_emails()
    if not to_email:
        return
    codalab_send_mail(
        context_data={**context, **get_link_context(request)},
        subject=f'{SUBJECT_PREFIX} {subject}',
        html_file=f'consulting/emails/{template}.html',
        text_file=f'consulting/emails/{template}.txt',
        to_email=to_email
    )


def _send_to_owner(request, listing, subject, template):
    if listing.owner.is_deleted:
        return
    codalab_send_mail(
        context_data={'listing': listing, 'user': listing.owner, **get_link_context(request)},
        subject=f'{SUBJECT_PREFIX} {subject}',
        html_file=f'consulting/emails/{template}.html',
        text_file=f'consulting/emails/{template}.txt',
        to_email=listing.owner.email
    )


def send_listing_submitted_email(request, listing, resubmitted=False):
    """Notify superusers that a listing is waiting for review (new, or edited and sent back to pending)"""
    action = 'updated' if resubmitted else 'submitted'
    _send_to_superusers(
        request=request,
        context={'listing': listing, 'resubmitted': resubmitted},
        subject=f'Listing {action} by {listing.owner.username}',
        template='listing_submitted'
    )


def send_listing_deleted_email(request, owner, title):
    """Notify superusers that a user removed their listing"""
    _send_to_superusers(
        request=request,
        context={'owner': owner, 'title': title},
        subject=f'Listing deleted by {owner.username}',
        template='listing_deleted'
    )


def send_listing_approved_email(request, listing):
    _send_to_owner(
        request=request,
        listing=listing,
        subject='Your listing was approved',
        template='listing_approved'
    )


def send_listing_rejected_email(request, listing):
    _send_to_owner(
        request=request,
        listing=listing,
        subject='Your listing was rejected',
        template='listing_rejected'
    )
