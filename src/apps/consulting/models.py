from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.timezone import now

from utils.data import PathWrapper


class ConsultingListing(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    )

    # One listing per user
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consulting_listing')
    title = models.CharField(max_length=150)
    picture = models.ImageField(upload_to=PathWrapper('consulting'))
    website_url = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    github_url = models.URLField(blank=True, default='')
    description = models.TextField(help_text="Markdown")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True, default='', help_text="Shown to the owner when the listing is rejected")
    is_active = models.BooleanField(default=True, help_text="Inactive listings are hidden from the public list, even when approved")
    created_when = models.DateTimeField(default=now)
    updated_when = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.owner.username})"


# A signal rather than a delete() override, so the picture is also removed on
# bulk deletes (Django admin "delete selected") and cascades from the owner
@receiver(post_delete, sender=ConsultingListing)
def delete_listing_picture(sender, instance, **kwargs):
    if instance.picture:
        instance.picture.delete(save=False)  # Delete file from storage
