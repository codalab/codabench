<organization-edit>
    <div class="ui raised segment">
    <h1 class="ui dividing header">Organization Edit:</h1>
    <form class="ui form" id="organization-form">
        <div class="field">
            <label>Profile Photo</label>
            <label show="{ original_org_photo }">
                Uploaded Photo: <a href="{ original_org_photo }" target="_blank">{ original_org_photo_name }</a>
            </label>
            <div class="ui left action file input">
                <button class="ui icon button" type="button" onclick="document.getElementById('profile_phtoto').click()">
                    <i class="attach icon"></i>
                </button>
                <input id="profile_phtoto" type="file" ref="photo" accept="image/*">

                <!-- Just showing the file after it is uploaded -->
                <input value="{ logo_file_name }" readonly onclick="document.getElementById('profile_phtoto').click()">
            </div>
        </div>
        <div class="two fields">
            <div class="required field" id="name">
                <label>Organization Name</label>
                <input type="text" name="name" placeholder="Name">
            </div>
            <div class="required field" id="email">
                <label>Organization Email</label>
                <input type="text" name="email" placeholder="email@organization.com">
            </div>
        </div>
        <div class="field" id="location">
            <label>Location</label>
            <input type="text" name="location" placeholder="Location">
        </div>
        <div class="field" id="description">
            <label>Description</label>
            <textarea name="description"></textarea>
        </div>
        <div class="two fields">
            <div class="field" id="website_url">
                <label>Organization URL</label>
                <input type="text" name="website_url" placeholder="https://organization.com">
            </div>
            <div class="field" id="linkedin_url">
                <label>LinkedIn URL</label>
                <input type="text" name="linkedin_url" placeholder="https://www.linkedin.com/company/organization">
            </div>
        </div>
        <div class="two fields">
            <div class="field" id="twitter_url">
                <label>Twitter URL</label>
                <input type="text" name="twitter_url" placeholder="https://twitter.com/organization">
            </div>
            <div class="field" id="github_url">
                <label>Github URL</label>
                <input type="text" name="github_url" placeholder="https://github.com/organization">
            </div>
        </div>
        <div class="ui error message"></div>
        <div class="ui primary button" onclick="{save.bind(this)}" id="submit_button">Submit</div>
        <a href="{self.organization.url}">
            <button type="button" class="ui button">Back to Organization Page</button>
        </a>
    </form>
    </div>
    <script>
        self = this
        self.organization = organization
        self.original_org_photo_name = typeof self.organization.photo !== 'undefined' ? null : self.organization.photo.replace(/\\/g, '/').replace(/.*\//, '')
        self.original_org_photo = self.organization.photo
        delete self.organization.photo


        self.one("mount", function () {
            self.submit_button = $('#submit_button')
            $.fn.form.settings.rules.test_http = function(param) {
                return /^(http|https):\/\/(.*)/.test(param)
            }

            $('#organization-form').form('set values', {
                name: self.organization.name,
                email: self.organization.email,
                location: self.organization.location,
                description: self.organization.description,
                website_url: self.organization.website_url,
                linkedin_url: self.organization.linkedin_url,
                twitter_url: self.organization.twitter_url,
                github_url: self.organization.github_url,
            })

            $('#organization-form').form({
                keyboardShortcuts: false,
                fields: {
                    name: {
                        identifier: 'name',
                        optional: false,
                        rules: [{
                            type: 'empty'
                        }]
                    },
                    email: {
                        identifier: 'email',
                        optional: false,
                        rules: [{
                            type: 'email',
                            prompt: 'Please enter a valid {name}'
                        }]
                    },
                    website_url: {
                        identifier: 'website_url',
                        optional: true,
                        rules: [
                            {
                                type: 'url',
                                prompt: 'Please enter a valid {name}. Example: https://organization.com'
                            },
                            {
                                type: 'test_http',
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
                                prompt: 'Please enter a valid {name}. Example: https://organization.com'
                            },
                            {
                                type: 'test_http',
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
                                prompt: 'Please enter a valid {name}. Example: https://www.linkedin.com/company/organization'
                            },
                            {
                                type: 'test_http',
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
                                prompt: 'Please enter a valid {name}. Example: https://github.com/organization'
                            },
                            {
                                type: 'test_http',
                                prompt: '{name} must start with "http://" or "https://"'
                            }
                        ]
                    },
                },
                onSuccess: function () {
                    data = $('#organization-form').form('get values')
                    data.photo = self.org_photo
                    CODALAB.api.update_organization(data, self.organization.id)
                        .done(data => {
                            toastr.success("Organization Saved")
                            self.submit_button.prop('disabled', false)
                        })
                        .fail(data => {
                            let errorsJSON = data.responseJSON
                            let errors = []
                            for(let key in errorsJSON){
                                errors.push(self.camel_case_to_regular(key) + ' - ' + errorsJSON[key])
                                $('#'+key).addClass('error')
                            }
                            $('#organization-form').form('add errors', errors)
                            self.submit_button.prop('disabled', false)
                        })
                    return false
                },
                onFailure: function () {
                    self.submit_button.prop('disabled', false)
                }
            })

            // Draw in logo filename as it's changed
            $(self.refs.photo).change(function () {
                self.logo_file_name = self.refs.photo.value.replace(/\\/g, '/').replace(/.*\//, '')
                self.update()
                getBase64(this.files[0]).then(function (data) {
                    self.org_photo = JSON.stringify({file_name: self.logo_file_name, data: data})
                })
            })
        })

        self.camel_case_to_regular = (str) => {
            str = str.replaceAll('_', ' ')
            return str.replace(/(?:^|\s|["'([{])+\S/g, match => match.toUpperCase())
        }

        self.save = () => {
            self.submit_button.prop('disabled', true)
            $('#organization-form').form('validate form')
        }
    </script>
</organization-edit>
