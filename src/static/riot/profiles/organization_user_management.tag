<organization-user-management>
    <div class="ui raised segment">
        <h1 class="ui dividing header">User Management:</h1>
        <table class="ui striped table">
            <thead>
            <tr>
                <th>Name</th>
                <th>E-mail</th>
                <th>Date Joined</th>
                <th>Group</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{user in members}">
                <td><a href="/profiles/user/{user.user.slug}/">{user.user.name}</a></td>
                <td><a href="mailto:{user.user.email}">{user.user.email}</a></td>
                <td>{user.date_joined}</td>
                <td if="{user['group'] !== 'OWNER'}">
                    <div class="ui inline dropdown">
                        <span class="text">{capitalize(user['group'])}</span>
                        <i class="dropdown icon"></i>
                        <div class="menu">
                            <div class="header">Adjust Member Permissions</div>
                            <div class="item" data-member="{user.id}" data-value="MANAGER"    >Manager</div>
                            <div class="item" data-member="{user.id}" data-value="PARTICIPANT">Participant</div>
                            <div class="item" data-member="{user.id}" data-value="MEMBER"     >Member</div>
                        </div>
                    </div>
                    <div class="ui tiny inline loader"></div>
                </td>
                <td if="{user['group'] === 'OWNER'}">
                    <span class="text">{capitalize(user['group'])}</span>
                </td>
            </tr>
            </tbody>
        </table>
    </div>

    <script>
        self = this
        self.members = organization.members
        self.organization_id = organization.id

        self.one("mount", function () {
            $('.ui.inline.dropdown').dropdown({
                onChange: function (value, text, choice) {
                    let loader = $(choice).parent().parent().parent().find('.loader')
                    loader.addClass('active')
                    let data = {
                        group: value,
                        membership: choice.data('member'),
                    }
                    CODALAB.api.update_user_group(data, self.organization_id)
                        .done((data) => {
                            setTimeout(()=>{
                                loader.removeClass('active')
                            }, 750)
                        })
                        .fail((response) => {
                            toastrr.error('Failed to edit user')
                        })
                }
            })
        })

        self.capitalize = (str) => {
            return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
        }
    </script>
</organization-user-management>
