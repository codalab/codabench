from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.fields import DateTimeField
from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField

from api.fields import NamedBase64ImageField
from profiles.models import GithubUserInfo, Organization, Membership

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


class SimpleUserSerializer(ModelSerializer):
    name = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'email',
            'slug'
        )

    def get_name(self, instance):
        if instance.display_name:
            return instance.display_name
        elif instance.first_name or instance.last_name:
            return f'{instance.first_name} {instance.last_name}'
        else:
            return instance.username


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


class UserSerializer(ModelSerializer):
    photo = NamedBase64ImageField(required=False, allow_null=True)
    organizations = OrganizationSerializer(many=True)

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
            'organizations',
        )


class MembershipSerializer(ModelSerializer):
    user = SimpleUserSerializer(many=False, read_only=True)
    organization_name = CharField(source='organization.name')
    # date_joined = DateTimeField(format="%m-%d-%Y", read_only=True)

    class Meta:
        model = Membership
        fields = (
            'date_joined',
            'user',
            'organization_name',
        )


class OrganizationMembershipSerializer(ModelSerializer):
    user = SimpleUserSerializer(read_only=True, many=False)
    # date_joined = DateTimeField(format="%m-%d-%Y", read_only=True)

    class Meta:
        model = Membership
        fields = (
            'id',
            'group',
            'date_joined',
            'user'
        )


class OrganizationCreationSerializer(OrganizationSerializer):
    redirect_url = SerializerMethodField(read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + (
            'redirect_url',
        )

    def get_redirect_url(self, instance):
        return reverse('profiles:organization_profile', args=[instance.id])


class OrganizationDetailSerializer(OrganizationSerializer):
    date_created = DateTimeField(format="%m-%d-%Y", read_only=True)
    users = SimpleUserSerializer(many=True, read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + (
            'date_created',
            'users',
        )


class OrganizationEditSerializer(OrganizationSerializer):
    members = OrganizationMembershipSerializer(source='membership_set', many=True, read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + (
            'members',
        )
