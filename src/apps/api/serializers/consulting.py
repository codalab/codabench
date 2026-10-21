from rest_framework import serializers

from consulting.models import ConsultingListing


class ConsultingListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultingListing
        fields = (
            'id',
            'title',
            'picture',
            'website_url',
            'linkedin_url',
            'github_url',
            'description',
            'created_when',
        )


class MyConsultingListingSerializer(serializers.ModelSerializer):
    MAX_PICTURE_SIZE = 5 * 1024 * 1024  # 5 MB

    class Meta:
        model = ConsultingListing
        fields = (
            'id',
            'title',
            'picture',
            'website_url',
            'linkedin_url',
            'github_url',
            'description',
            'status',
            'rejection_reason',
            'is_active',
            'created_when',
        )
        # Only admins review listings (in Django admin), so owners can't set these
        read_only_fields = (
            'status',
            'rejection_reason',
            'is_active',
            'created_when',
        )

    def validate_picture(self, picture):
        if picture.size > self.MAX_PICTURE_SIZE:
            raise serializers.ValidationError('The picture must be 5 MB or smaller.')
        return picture
