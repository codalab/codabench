from django import forms
from django.contrib import admin
from django.utils.html import format_html

from consulting.emails import send_listing_approved_email, send_listing_rejected_email
from consulting.models import ConsultingListing


STATUS_COLORS = {
    ConsultingListing.STATUS_PENDING: "#f2c037",
    ConsultingListing.STATUS_APPROVED: "#21ba45",
    ConsultingListing.STATUS_REJECTED: "#db2828",
}


class ConsultingListingAdminForm(forms.ModelForm):
    class Meta:
        model = ConsultingListing
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('status') == ConsultingListing.STATUS_REJECTED and not cleaned_data.get('rejection_reason'):
            self.add_error('rejection_reason', 'A reason is required to reject a listing.')
        return cleaned_data


def approve_listings(modeladmin, request, queryset):
    approved_count = 0
    for listing in queryset.exclude(status=ConsultingListing.STATUS_APPROVED):
        listing.status = ConsultingListing.STATUS_APPROVED
        listing.rejection_reason = ''
        listing.save()
        send_listing_approved_email(request=request, listing=listing)
        approved_count += 1
    modeladmin.message_user(request, f'{approved_count} listing(s) approved.')


approve_listings.short_description = 'Approve selected listings'


class ConsultingListingAdmin(admin.ModelAdmin):
    form = ConsultingListingAdminForm
    list_display = ['id', 'title', 'owner', 'status_badge', 'is_active', 'created_when', 'updated_when']
    list_filter = ['status', 'is_active']
    search_fields = ['title', 'owner__username', 'owner__email']
    raw_id_fields = ['owner']
    actions = [approve_listings]

    @admin.display(description="status", ordering="status")
    def status_badge(self, obj):
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
            STATUS_COLORS.get(obj.status, "#767676"),
            obj.get_status_display(),
        )

    def save_model(self, request, obj, form, change):
        status_changed = 'status' in form.changed_data
        if obj.status == ConsultingListing.STATUS_APPROVED:
            obj.rejection_reason = ''
        super().save_model(request, obj, form, change)

        # Notify the owner of the review decision
        if status_changed and obj.status == ConsultingListing.STATUS_APPROVED:
            send_listing_approved_email(request=request, listing=obj)
        elif status_changed and obj.status == ConsultingListing.STATUS_REJECTED:
            send_listing_rejected_email(request=request, listing=obj)


admin.site.register(ConsultingListing, ConsultingListingAdmin)
