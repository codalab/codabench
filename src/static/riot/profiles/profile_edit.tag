<profile-edit>
    <form class="ui form" id="user-form">
        <!-- Photo: shows the current photo, or the new one as soon as it is chosen -->
        <div class="profile-edit-photo">
            <div class="bc-logo profile-photo">
                <img if="{ photo }" src="{ photo }" alt="">
                <span if="{ !photo }">{ parent.photo_letter }</span>
            </div>
            <button type="button" class="settings-button settings-button-secondary" onclick="{ choose_photo }">Change photo</button>
            <input type="file" ref="photo" accept="image/*">
        </div>
        <div class="two fields">
            <div class="field" id="first_name">
                <label>First Name</label>
                <input type="text" name="first_name" placeholder="First Name">
            </div>
            <div class="field" id="last_name">
                <label>Last Name</label>
                <input type="text" name="last_name" placeholder="Last Name">
            </div>
        </div>
        <div class="two fields">
            <div class="field" id="display_name">
                <label>Display Name</label>
                <input type="text" name="display_name" placeholder="Display Name">
            </div>
            <div class="field" id="title">
                <label>Job Title</label>
                <input type="text" name="title" placeholder="Job Title"></div>
        </div>
        <div class="field" id="location">
            <label>Location</label>
            <input type="text" name="location" placeholder="Location"></div>
        <div class="field" id="email">
            <label>Email</label>
            <input disabled type="text" name="email" placeholder="Email">
        </div>
        <div class="two fields">
            <div class="field" id="personal_url">
                <label>Personal Website</label>
                <input type="text" name="personal_url" placeholder="Personal URL">
            </div>
            <div class="field" id="twitter_url">
                <label>X URL</label>
                <input type="text" name="twitter_url" placeholder="X URL">
            </div>
        </div>
        <div class="two fields">
            <div class="field" id="linkedin_url">
                <label>LinkedIn URL</label>
                <input type="text" name="linkedin_url" placeholder="LinkedIn URL">
            </div>
            <div class="field" id="github_url">
                <label>Github URL</label>
                <input type="text" name="github_url" placeholder="Github URL">
            </div>
        </div>
        <div class="field" id="biography">
            <label>Bio</label>
            <textarea name="biography"></textarea>
        </div>
        <div class="ui error message"></div>
        <div class="profile-form-buttons">
            <button type="button" class="settings-button settings-button-secondary" onclick="{cancel}">Cancel</button>
            <button type="button" class="settings-button" onclick="{save.bind(this)}" ref="submit_button">Save</button>
        </div>
    </form>

    <script>
        var self = this
        // Why a copy: the profile details use selected_user too, and the steps below remove fields from it
        self.selected_user = Object.assign({}, selected_user)
        self.photo = self.selected_user.photo
        delete self.selected_user.photo
        self.one("mount", function () {
            // Create http validation rule
            $.fn.form.settings.rules.test_http = function(param) {
                return /^(http|https):\/\/(.*)/.test(param)
            }
            // Prefill form with saved data
            $('#user-form').form('set values', {
                first_name:     selected_user.first_name,
                last_name:      selected_user.last_name,
                email:          selected_user.email,
                display_name:   selected_user.display_name,
                personal_url:   selected_user.personal_url,
                twitter_url:    selected_user.twitter_url,
                linkedin_url:   selected_user.linkedin_url,
                github_url:     selected_user.github_url,
                title:          selected_user.title,
                location:       selected_user.location,
                biography:      selected_user.biography,
                })
             $('#user-form').form({
                 keyboardShortcuts: false,
                 fields: {
                    email: {
                        identifier: 'email',
                        optional: true // Make the email field optional
                    },
                     personal_url: {
                         identifier: 'personal_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid url. Example: https://www.xyz.com'
                             },
                             {
                                 type: "test_http",
                                 prompt: '{name} must start with "http://" or "https://"'
                             }
                         ]
                     },
                     twitter_url: {
                         identifier: 'twitter_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid {name}. Example: https://x.com/BobRoss'
                             },
                             {
                                 type: "test_http",
                                 prompt: '{name} must start with "http://" or "https://"'
                             }
                         ]
                     },
                     linkedin_url: {
                         identifier: 'linkedin_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid {name}. Example: https://www.linkedin.com/in/john-doe'
                             },
                             {
                                 type: "test_http",
                                 prompt: '{name} must start with "http://" or "https://"'
                             }
                         ]
                     },
                     github_url: {
                         identifier: 'github_url',
                         optional: true,
                         rules: [
                             {
                                 type: 'url',
                                 prompt: 'Please enter a valid {name}. Example: https://github.com/john-doe'
                             },
                             {
                                 type: "test_http",
                                 prompt: '{name} must start with "http://" or "https://"'
                             }
                         ]
                     },
                 },
                 onSuccess: function () {
                     // get form values from user-form
                     const formValues = $('#user-form').form('get values')
                     
                     // delete email from form values
                     delete formValues.email;

                     _.extend(self.selected_user, formValues)
                     CODALAB.api.update_user_details(self.selected_user.id, self.selected_user)
                         .done(data => {
                             toastr.success("Details Saved")
                             window.location.href = data
                         })
                         .fail(data => {
                             let errorsJSON = data.responseJSON
                             let errors = []
                             for(let key in errorsJSON){
                                 errors.push(self.camel_case_to_regular(key) + ' - ' + errorsJSON[key])
                                 $('#'+key).addClass('error')
                             }
                             $('#user-form').form('add errors', errors)
                             self.refs.submit_button.disabled = false
                         })
                     return false
                 },
                 onFailure: function (){
                     self.refs.submit_button.disabled = false
                 }
             })

            // Show the chosen photo right away. It is only uploaded when the user clicks Save.
            $(self.refs.photo).change(function () {
                const file = this.files[0]
                if (!file) {
                    return
                }
                getBase64(file).then(function (data) {
                    self.selected_user['photo'] = JSON.stringify({file_name: file.name, data: data})
                    self.photo = data
                    self.update()
                })
            })
            self.update()
        })

        // Why: the file input is hidden, so the Change photo button opens it
        self.choose_photo = () => {
            self.refs.photo.click()
        }

        self.camel_case_to_regular = (str) => {
            str = str.replaceAll('_', ' ')
            return str.replace(/(?:^|\s|["'([{])+\S/g, match => match.toUpperCase())
        }

        // Goes back to the profile details on the same page
        self.cancel = () => {
            self.parent.stop_editing()
        }

        self.save = () => {
            self.refs.submit_button.disabled = true
            $('#user-form').form('validate form')
        }
    </script>
</profile-edit>
