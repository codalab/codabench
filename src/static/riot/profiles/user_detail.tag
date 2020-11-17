<user-detail>
    <h1>User Edit Screen</h1>
    <form class="ui form" id="user-form">
        <div class="field">
            <label>Profile Photo</label>
            <label show="{ photo }">
                Uploaded Photo: <a href="{ photo }" target="_blank">{ photo_name }</a>
            </label>
            <div class="ui left action file input">
                <button class="ui icon button" onclick="document.getElementById('profile_phtoto').click()">
                    <i class="attach icon"></i>
                </button>
                <input id="profile_phtoto" type="file" ref="photo" accept="image/*">

                <!-- Just showing the file after it is uploaded -->
                <input value="{ logo_file_name }" readonly onclick="document.getElementById('profile_phtoto').click()">
            </div>
        </div>
        <div class="two fields">
            <div class="field">
                <label>First Name</label>
                <input type="text" name="first_name" placeholder="First Name">
            </div>
            <div class="field">
                <label>Last Name</label>
                <input type="text" name="last_name" placeholder="Last Name">
            </div>
        </div>
        <div class="two fields">
            <div class="field">
                <label>Display Name</label>
                <input type="text" name="display_name" placeholder="Display Name">
            </div>
            <div class="field">
                <label>Job Title</label>
                <input type="text" name="title" placeholder="Job Title"></div>
        </div>
        <div class="field">
            <label>Location</label>
            <input type="text" name="location" placeholder="Location"></div>
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

    <script>
        self = this
        self.selected_user = selected_user
        self.photo = self.selected_user.photo
        delete self.selected_user.photo
        self.one("mount", function () {
            // Prefill form with saved data
            $('#user-form').form('set values', {
                first_name:     selected_user.first_name,
                last_name:      selected_user.last_name,
                email:          selected_user.email,
                display_name:   selected_user.display_name,
                personal_url:   selected_user.personal_url,
                twitter_url:    selected_user.twitter_url,
                linkedin_url:   selected_user.linkedin_url,
                title:          selected_user.title,
                location:       selected_user.location
                })
            self.photo_name = typeof self.photo == 'undefined' ? null : self.photo.replace(/\\/g, '/').replace(/.*\//, '')
            // Draw in logo filename as it's changed
            $(self.refs.photo).change(function () {
                self.logo_file_name = self.refs.photo.value.replace(/\\/g, '/').replace(/.*\//, '')
                self.update()
                getBase64(this.files[0]).then(function (data) {
                    self.selected_user['photo'] = JSON.stringify({file_name: self.logo_file_name, data: data})
                })
            })
            self.update()
        })

        self.save = () => {
            // delete form_data['photo']
            _.extend(self.selected_user, $('#user-form').form('get values'))
            CODALAB.api.update_user_details(self.selected_user.id, self.selected_user)
                .done( data => {
                    toastr.success("Details Saved")
                })
                .fail(errors =>{
                    toastr.error(JSON.stringify(errors))
                })
        }
    </script>
</user-detail>
