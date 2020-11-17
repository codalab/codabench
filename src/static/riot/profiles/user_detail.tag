<user-detail>
    <h1>User Edit Screen</h1>
    <form class="ui form" id="user-form">
        <div class="fields">
            <div class="field">
                <label>First Name</label>
                <input type="text" name="first_name" placeholder="First Name">
            </div>
            <div class="field">
                <label>Last Name</label>
                <input type="text" name="last_name" placeholder="Last Name">
            </div>
        </div>
        <div class="field">
            <label>Display Name</label>
            <input type="text" name="display_name" placeholder="Display Name">
        </div>
        <div class="field">
            <label>Email</label>
            <input type="text" name="email" placeholder="Email">
        </div>
        <div class="fields">
            <div class="field">
                <label>Personal Website</label>
                <input type="text" name="personal_url" placeholder="Personal URL">
            </div>
            <div class="field">
                <label>Twitter</label>
                <input type="text" name="twitter_url" placeholder="Twitter URL">
            </div>
            <div class="field">
                <label>LinkedIn URL</label>
                <input type="text" name="linkedin_url" placeholder="Linkedin URL">
            </div>
        </div>
        <div class="field">
            <label>Bio</label>
            <textarea name="biography"></textarea>
        </div>

        <button type="button" class="ui button" onclick="{save.bind(this)}">Submit</button>
    </form>













    <pre>{self.rendered_user}</pre>
    <script>
        self = this
        self.selected_user = selected_user
        self.one("mount", function () {
            self.rendered_user = JSON.stringify(selected_user, null, 2)
            $('#user-form').form('set values', {
                first_name:     selected_user.first_name,
                last_name:      selected_user.last_name,
                email:          selected_user.email,
                display_name:   selected_user.display_name,
                personal_url:   selected_user.personal_url,
                twitter_url:    selected_user.twitter_url,
                linkedin_url:   selected_user.linkedin_url
                })
            self.update()
        })

        self.save = () => {
            _.extend(self.selected_user, $('#user-form').form('get values'))
            CODALAB.api.update_user_details(self.selected_user.id, self.selected_user)
                .done( data => {
                    toastr.success("Details Saved")
                })
                .fail(errors =>{
                    console.log("fail", errors)
                })
        }
    </script>
</user-detail>
