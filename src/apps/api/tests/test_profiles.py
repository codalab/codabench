from django.urls import reverse
from rest_framework.test import APITestCase
from json import dumps
from api.serializers.profiles import OrganizationSerializer
from factories import UserFactory, OrganizationFactory
from profiles.models import Membership


class OrganizationPermissionTests(APITestCase):
    def setUp(self):
        self.random_user = UserFactory()
        # Organizations Setup
        self.owner = UserFactory(username='owner')
        self.manager = UserFactory(username='manager')
        self.participant = UserFactory(username='participant')
        self.member = UserFactory(username='member')
        self.member2 = UserFactory(username='member2')
        self.invited = UserFactory(username='invited')
        self.organization = OrganizationFactory()
        self.organization.users.add(*[
            self.owner,
            self.manager,
            self.participant,
            self.member,
            self.member2,
            self.invited,
        ])
        self.organization.membership_set.filter(user=self.owner).update(group=Membership.OWNER)
        self.organization.membership_set.filter(user=self.manager).update(group=Membership.MANAGER)
        self.organization.membership_set.filter(user=self.participant).update(group=Membership.PARTICIPANT)
        self.organization.membership_set.filter(user=self.member).update(group=Membership.MEMBER)
        self.organization.membership_set.filter(user=self.member2).update(group=Membership.MEMBER)
        self.organization.membership_set.filter(user=self.invited).update(group=Membership.INVITED)

        # Urls
        self.update_member_group = reverse('organizations-update-member-group', args=[self.organization.id])
        self.delete_member = reverse('organizations-delete-member', args=[self.organization.id])
        self.validate_invite = reverse('organizations-validate-invite')
        self.invite_response = reverse('organizations-invite-response')
        self.invite_user = reverse('organizations-invite-users', args=[self.organization.id])
        self.url_organizations = reverse('organizations-detail', args=[self.organization.id])

    def get_membership_id_for_user(self, user_id):
        return self.organization.membership_set.get(user=user_id).id

    def get_token_for_user(self, user_id):
        return self.organization.membership_set.get(user=user_id).token

    def test_non_admin_org_members_cannot_raise_permission_group_of_themselves(self):
        self.client.force_login(user=self.member)
        data = {
            'membership': self.get_membership_id_for_user(self.member.id),
            'group': Membership.MANAGER,
        }
        resp = self.client.post(self.update_member_group, data=data)
        assert resp.status_code == 403

    def test_non_admin_org_members_cannot_raise_permission_group_of_others(self):
        self.client.force_login(user=self.member)
        data = {
            'membership': self.get_membership_id_for_user(self.member2.id),
            'group': Membership.MANAGER,
        }
        resp = self.client.post(self.update_member_group, data=data)
        assert resp.status_code == 403

    def test_non_org_member_cannot_find_object_when_changing_permission_group_of_others(self):
        self.client.force_login(user=self.random_user)
        data = {
            'membership': self.get_membership_id_for_user(self.member2.id),
            'group': Membership.MANAGER,
        }
        resp = self.client.post(self.update_member_group, data=data)
        assert resp.status_code == 404

    def test_admin_org_members_can_raise_permission_group_of_others(self):
        self.client.force_login(user=self.manager)
        data = {
            'membership': self.get_membership_id_for_user(self.member2.id),
            'group': Membership.MANAGER,
        }
        resp = self.client.post(self.update_member_group, data=data)
        assert resp.status_code == 200

    def test_admin_org_members_can_lower_permission_group_of_others(self):
        self.client.force_login(user=self.manager)
        data = {
            'membership': self.get_membership_id_for_user(self.member2.id),
            'group': Membership.MEMBER,
        }
        resp = self.client.post(self.update_member_group, data=data)
        assert resp.status_code == 200

    def test_admin_org_members_cannot_lower_permission_group_of_owner(self):
        self.client.force_login(user=self.manager)
        data = {
            'membership': self.get_membership_id_for_user(self.owner.id),
            'group': Membership.MEMBER,
        }
        resp = self.client.post(self.update_member_group, data=data)
        assert resp.status_code == 403

    def test_admin_org_members_cannot_raise_permission_group_of_invited(self):
        self.client.force_login(user=self.manager)
        data = {
            'membership': self.get_membership_id_for_user(self.invited.id),
            'group': Membership.MEMBER,
        }
        resp = self.client.post(self.update_member_group, data=data)
        assert resp.status_code == 403

    def test_admin_org_members_cannot_delete_org_owner(self):
        self.client.force_login(user=self.manager)
        data = {
            'membership': self.get_membership_id_for_user(self.owner.id)
        }
        resp = self.client.delete(self.delete_member, data=data)
        assert resp.status_code == 403

    def test_non_admin_org_members_cannot_delete_org_member(self):
        self.client.force_login(user=self.participant)
        data = {
            'membership': self.get_membership_id_for_user(self.member.id)
        }
        resp = self.client.delete(self.delete_member, data=data)
        assert resp.status_code == 403

    def test_admin_org_members_can_delete_org_member(self):
        self.client.force_login(user=self.manager)
        data = {
            'membership': self.get_membership_id_for_user(self.member2.id)
        }
        resp = self.client.delete(self.delete_member, data=data)
        assert resp.status_code == 200
        self.organization.users.add(self.member2)
        self.organization.membership_set.filter(user=self.member2).update(group=Membership.MEMBER)

    def test_admin_org_members_can_delete_org_invited(self):
        self.client.force_login(user=self.manager)
        data = {
            'membership': self.get_membership_id_for_user(self.invited.id)
        }
        resp = self.client.delete(self.delete_member, data=data)
        assert resp.status_code == 200
        self.organization.users.add(self.invited)
        self.organization.membership_set.filter(user=self.invited).update(group=Membership.INVITED)

    def test_invited_org_member_invite_token_validates(self):
        self.client.force_login(user=self.invited)
        data = {
            'token': self.get_token_for_user(self.invited)
        }
        resp = self.client.post(self.validate_invite, data=data)
        assert resp.status_code == 200

    def test_invited_org_member_can_accept_invite(self):
        self.client.force_login(user=self.invited)
        data = {
            'token': self.get_token_for_user(self.invited)
        }
        resp = self.client.post(self.invite_response, data=data)
        assert resp.status_code == 200
        self.organization.membership_set.filter(user=self.invited).update(group=Membership.INVITED)

    def test_invited_org_member_can_reject_invite(self):
        self.client.force_login(user=self.invited)
        data = {
            'token': self.get_token_for_user(self.invited)
        }
        resp = self.client.delete(self.invite_response, data=data)
        assert resp.status_code == 200
        self.organization.membership_set.filter(user=self.invited).update(group=Membership.INVITED)

    def test_org_member_cannot_accept_invite_for_other(self):
        self.client.force_login(user=self.member)
        data = {
            'token': self.get_token_for_user(self.invited)
        }
        resp = self.client.post(self.invite_response, data=data)
        assert resp.status_code == 403

    def test_org_member_cannot_reject_invite_for_other(self):
        self.client.force_login(user=self.member)
        data = {
            'token': self.get_token_for_user(self.invited)
        }
        resp = self.client.delete(self.invite_response, data=data)
        assert resp.status_code == 403

    def test_org_member_cannot_invite_user(self):
        self.client.force_login(user=self.member)
        data = {'users': [self.random_user.id]}
        resp = self.client.post(self.invite_user, data=dumps(data), content_type='application/json')
        assert resp.status_code == 403

    def test_admin_org_member_can_invite_user(self):
        self.client.force_login(user=self.manager)
        data = {
            'users': [self.random_user.id],
        }
        resp = self.client.post(self.invite_user, data=dumps(data), content_type='application/json')
        assert resp.status_code == 200

    def test_admin_org_member_can_edit_organization(self):
        self.client.force_login(user=self.manager)
        data = OrganizationSerializer(instance=self.organization).data
        data['name'] = "Changed_Name"
        data = {k: v for k, v in data.items() if v}
        resp = self.client.put(self.url_organizations, data=dumps(data), content_type='application/json')
        assert resp.status_code == 200

    def test_org_member_cannot_edit_organization(self):
        self.client.force_login(user=self.member)
        data = OrganizationSerializer(instance=self.organization).data
        data['name'] = "Changed_Name2"
        data = {k: v for k, v in data.items() if v}
        resp = self.client.put(self.url_organizations, data=dumps(data), content_type='application/json')
        assert resp.status_code == 403
