'''
Serializers for the data shown on the home page
'''
from django.utils import dateformat
from django.utils.timezone import localtime
from rest_framework import serializers

from announcements.models import Announcement, NewsPost
from competitions.models import Competition

# e.g. "Sep 23, 2026"
DATE_FORMAT = "M j, Y"


def format_date(value):
    """Format a datetime for display in the local timezone, or return None when there is no date."""
    return dateformat.format(localtime(value), DATE_FORMAT) if value else None


class HomePageAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = (
            'title',
            'text',
            'level',
        )


class HomePageNewsPostSerializer(serializers.ModelSerializer):
    created_when = serializers.SerializerMethodField()

    class Meta:
        model = NewsPost
        fields = (
            'title',
            'link',
            'text',
            'created_when',
        )

    def get_created_when(self, obj):
        return format_date(obj.created_when)


class HomePageBenchmarkSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    owner_display_name = serializers.SerializerMethodField()
    first_phase_start = serializers.SerializerMethodField()

    class Meta:
        model = Competition
        fields = (
            'id',
            'title',
            'description',
            'competition_type',
            'logo_url',
            'owner_display_name',
            'first_phase_start',
            'participants_count',
            'submissions_count',
            'reward',
        )

    def get_logo_url(self, obj):
        # Prefer the small logo icon, fall back to the full logo
        logo = obj.logo_icon or obj.logo
        return logo.url if logo else None

    def get_owner_display_name(self, obj):
        # Display name if set, otherwise username, nothing if the creator was deleted
        if not obj.created_by:
            return None
        return obj.created_by.display_name or obj.created_by.username

    def get_first_phase_start(self, obj):
        return format_date(obj.first_phase_start)
