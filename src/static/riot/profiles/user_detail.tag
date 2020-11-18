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
        <div class="two fields">
            <div class="field">
                <label>Personal Website</label>
                <input type="text" name="personal_url" placeholder="Personal URL">
            </div>
            <div class="field">
                <label>Twitter URL</label>
                <input type="text" name="twitter_url" placeholder="Twitter URL">
            </div>
        </div>
        <div class="two fields">
            <div class="field">
                <label>LinkedIn URL</label>
                <input type="text" name="linkedin_url" placeholder="LinkedIn URL">
            </div>
            <div class="field">
                <label>Github URL</label>
                <input type="text" name="github_url" placeholder="Github URL">
            </div>
        </div>
        <div class="field">
            <label>Bio</label>
            <textarea name="biography"></textarea>
        </div>
        <div class="ui error message"></div>
        <button type="button" class="ui primary button" onclick="{save.bind(this)}" ref="submit_button">Submit</button>
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
                github_url:     selected_user.linkedin_url,
                title:          selected_user.title,
                location:       selected_user.location,
                biography:      selected_user.biography,
                })
             $('#user-form').form({
                 fields: {
                     email: {
                         identifier: 'email',
                         optional: true,
                         rules: [
                             {
                                 type: 'email',
                                 prompt: 'Please enter a valid e-mail'
                             }
                         ]
                     },
                     personal_url: {
                         identifier: 'personal_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid url. Example: https://www.xyz.com'
                             }
                         ]
                     },
                     twitter_url: {
                         identifier: 'twitter_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid twitter url. Example: https://twitter.com/BobRoss'
                             }
                         ]
                     },
                     linkedin_url: {
                         identifier: 'linkedin_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid url. Example: https://www.linkedin.com/in/john-doe'
                             }
                         ]
                     },
                     github_url: {
                         identifier: 'github_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid url. Example: https://github.com/john-doe'
                             }
                         ]
                     },
                 },
                 onSuccess: function (){
                     _.extend(self.selected_user, $('#user-form').form('get values'))
                     CODALAB.api.update_user_details(self.selected_user.id, self.selected_user)
                         .done( data => {
                             toastr.success("Details Saved")
                             window.location.href = data
                         })
                         .fail(errors =>{
                             toastr.error(JSON.stringify(errors))
                             self.refs.submit_button.disabled = false
                         })
                     return false
                 }
             })
            self.photo_name = typeof self.photo == 'undefined' || self.photo === null ? null : self.photo.replace(/\\/g, '/').replace(/.*\//, '')
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
            self.refs.submit_button.disabled = true
            $('#user-form').form('validate form')
        }
    </script>
</user-detail>
