<organization-user-management>
    <div class="ui raised segment">
        <h1 class="ui dividing header">User Management:</h1>
            <div class="ui right floated small green button" id="invite-user-button" onclick="{invite_users.bind(this)}">
                Invite Users
                <i class="user plus icon right"></i>
            </div>
        <table class="ui striped table">
            <thead>
            <tr>
                <th>Name</th>
                <th>E-mail</th>
                <th>Date Joined</th>
                <th>Group</th>
                <th>Remove</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{user in members}">
                <td><a href="/profiles/user/{user.user.slug}/">{user.user.name}</a></td>
                <td><a href="mailto:{user.user.email}">{user.user.email}</a></td>
                <td>{user.date_joined}</td>
                <td if="{user['group'] !== 'OWNER' && user['group'] !== 'INVITED'}">
                    <span>
                    <div class="ui inline dropdown">
                        <div class="text">{capitalize(user['group'])}
                        </div>
                        <i class="dropdown icon"></i>
                        <div class="menu">
                            <div class="header">Adjust Member Permissions</div>
                            <div class="item" data-member="{user.id}" data-value="MANAGER"    >Manager</div>
                            <div class="item" data-member="{user.id}" data-value="PARTICIPANT">Participant</div>
                            <div class="item" data-member="{user.id}" data-value="MEMBER"     >Member</div>
                        </div>
                    </div>
                    <div class="ui tiny inline loader"></div>
                </span>
                </td>
                <td if="{user['group'] === 'OWNER' || user['group'] === 'INVITED'}">
                    <span class="text">{capitalize(user['group'])}</span>
                </td>
                <td if="{user['group'] !== 'OWNER'}"><button class="ui mini icon negative button" onclick="{delete_member.bind(this, user.id, user.user.name)}">
                    <i class="x icon"></i>
                </button></td>
                <td if="{user['group'] === 'OWNER'}"></td>
            </tr>
            </tbody>
        </table>
        <div class="ui mini modal" ref="confirm_delete">
            <div class="header">Please Confirm</div>
            <div class="content">
                Are you want to remove <strong>{pending_member_name}</strong> from <strong>{organization_name}</strong>?
            </div>
            <div class="actions">
                <div class="ui negative button">Remove Member</div>
                <div class="ui ok button">Cancel</div>
            </div>
        </div>
        <div class="ui modal" ref="invite_users">
            <div class="ui header">Invite Users</div>
            <div class="content">
                <select class="ui fluid search multiple selection dropdown" multiple id="user_search">
                    <i class="dropdown icon"></i>
                    <div class="default text">Select Collaborator</div>
                    <div class="menu">
                    </div>
                </select>
            </div>
            <div class="actions">
                <div class="ui positive button">Invite Users</div>
                <div class="ui cancel button">Cancel</div>
            </div>
        </div>
    </div>

    <script>
        self_manage = this
        self_manage.members = organization.members
        self_manage.organization_name = organization.name
        self_manage.organization_id = organization.id
        self_manage.pending_member_name = ''

        self_manage.one("mount", function () {
            $('.ui.inline.dropdown').dropdown({
                onChange: function (value, text, choice) {
                    let loader = $(choice).parent().parent().parent().find('.loader')
                    loader.addClass('active')
                    let data = {
                        group: value,
                        membership: choice.data('member'),
                    }
                    CODALAB.api.update_user_group(data, self_manage.organization_id)
                        .done((data) => {
                            setTimeout(()=>{
                                loader.removeClass('active')
                            }, 750)
                        })
                        .fail((response) => {
                            toastr.error('Failed to edit user')
                        })
                }
            })

            $(self_manage.refs.confirm_delete).modal({
                onDeny: function () {
                    CODALAB.api.delete_organization_member(self_manage.organization_id, {membership: self_manage.pending_member_id})
                        .done((data) => {
                            self_manage.members = self_manage.members.filter(user => user.id !== self_manage.pending_member_id)
                            self_manage.update()
                            self_manage.pending_member_id = undefined
                            self_manage.pending_member_name = undefined
                            return true
                        })
                        .fail((response) => {
                            toastr.error('Failed to remove member.')
                            self_manage.pending_member_id = undefined
                            self_manage.pending_member_name = undefined
                            return true
                        })
                },
            })

            $('#user_search').dropdown({
                apiSettings: {
                    url: `${URLS.API}user_lookup/?q={query}`,
                },
                clearable: true,
                preserveHTML: false,
                fields: {
                    title: 'name',
                    value: 'id',
                },
                cache: false,
                maxResults: 5,
            })
            $(self_manage.refs.invite_users).modal({
                onApprove: function () {
                    let users = $('#user_search').dropdown('get value')
                    CODALAB.api.invite_user_to_organization(self_manage.organization_id, {users: users})
                        .done((data) => {
                            toastr.success('Invites Sent')
                            location.reload()
                        })
                        .fail((response) => {
                            toastr.error('An error has occurred')
                            return true
                        })
                }
            })
        })

        self_manage.capitalize = (str) => {
            return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
        }

        self_manage.delete_member = (id, username) => {
            self_manage.pending_member_id = id
            self_manage.pending_member_name = username
            self_manage.update()
            $(self_manage.refs.confirm_delete)
                .modal('show')
        }

        self_manage.invite_users = () => {
            $(self_manage.refs.invite_users)
                .modal('show')
        }
    </script>
    <style>
        #invite-user-button {
            position: absolute;
            top: 14px;
            right: 14px;
        }
    </style>
</organization-user-management>
