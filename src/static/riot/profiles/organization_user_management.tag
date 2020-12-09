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
                <td>{user['group']}</td>
            </tr>
            </tbody>
        </table>
    </div>

    <script>
        self = this
        self.members = organization.members
        console.log(self.members)
    </script>
</organization-user-management>
