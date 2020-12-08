from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from api.fields import NamedBase64ImageField
from profiles.models import GithubUserInfo, Organization

User = get_user_model()


class GithubUserInfoSerializer(ModelSerializer):

    class Meta:
        model = GithubUserInfo
        fields = [
            'uid',
            'login',
            'avatar_url',
            'gravatar_id',
            'html_url',
            'name',
            'company',
            'bio',
            'location',
            'created_at',
            'updated_at',
            'node_id',
            'url',
            'followers_url',
            'following_url',
            'gists_url',
            'starred_url',
            'subscriptions_url',
            'organizations_url',
            'repos_url',
            'events_url',
            'received_events_url'
        ]


class MyProfileSerializer(ModelSerializer):

    github_info = GithubUserInfoSerializer(read_only=True, required=False, many=False)

    class Meta:
        model = User
        fields = (
            'username',
            'name',
            'email',
            'github_info'
        )


class CollaboratorSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'username',
        )


class UserSerializer(ModelSerializer):
    photo = NamedBase64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'username',
            'photo',
            'email',
            'display_name',
            'first_name',
            'last_name',
            'title',
            'location',
            'biography',
            'personal_url',
            'linkedin_url',
            'twitter_url',
            'github_url',
        )


class OrganizationSerializer(ModelSerializer):
    photo = NamedBase64ImageField(required=False, allow_null=True)

    class Meta:
        model = Organization
        fields = (
            'id',
            'name',
            'photo',
            'email',
            'location',
            'description',
            'website_url',
            'linkedin_url',
            'twitter_url',
            'github_url',
        )


class OrganizationCreationSerializer(OrganizationSerializer):
    redirect_url = SerializerMethodField(read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + (
            'redirect_url',
        )

    def get_redirect_url(self, instance):
        return reverse('profiles:organization_profile', args=[instance.id])

