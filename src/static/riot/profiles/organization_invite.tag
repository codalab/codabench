<organization-invite>
    <div class="ui raised segment">
        <h1 class="ui dividing header">Organization Invite</h1>
        <div if="{state === 'loading'}" class="ui placeholder">
            <div class="paragraph">
                <div class="line"></div>
                <div class="line"></div>
                <div class="line"></div>
                <div class="line"></div>
                <div class="line"></div>
            </div>
        </div>
        <div if="{state === 'invite_valid'}">
            <div class="ui items">
                <div class="item">
                    <div class="content">
                        <div class="description">
                            Would you like to accept invite to <strong>{invite_data.organization_name}</strong>
                        </div>
                        <div class="extra">Invite Sent {invite_data.date_joined}</div>
                        <div class="extra">
                            <div onclick="{accept_invite}" class="ui left floated positive button">
                                Accept
                                <i class="right check icon"></i>
                            </div>
                            <div onclick="{reject_invite}" class="ui right floated negative button">
                                Reject
                                <i class="right x icon"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div if="{state === 'invite_not_found'}">
            <div class="ui items">
                <div class="item">
                    <div class="content">
                        <div class="description">
                            <h3 class="header">Invite Not Found</h3>
                        </div>
                        <div class="extra">
                            <a href="/"><button class="ui right floated button primary">Return Home</button></a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div if="{state === 'user_invite_mismatch'}">
            <div class="ui items">
                <div class="item">
                    <div class="content">
                        <div class="description">
                            <h3 class="header">This invite is not for the user logged in.</h3>
                            <div class="text">
                                Please make sure you are logged into the correct account, or have organization
                                administrator send you an invite.
                            </div>
                        </div>
                        <div class="extra">
                            <a href="/"><button class="ui right floated button primary">Return Home</button></a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div if="{state === 'already_accepted'}">
            <div class="ui center aligned items">
                <div class="item">
                    <div class="content">
                        <div class="description">
                            <h3 class="header">Invite has already been accepted</h3>
                            <div class="text">
                                Redirecting you to the competition in 3 seconds.
                            </div>
                            <div class="ui active centered inline loader"></div>
                        </div>
                        <div class="extra">
                            <a href="/"><button class="ui right floated button primary">Return Home</button></a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div if="{state === 'unknown_error'}">
            <div class="ui items">
                <div class="item">
                    <div class="content">
                        <div class="description">
                            <h3 class="header">Unknown Error.</h3>
                            <div class="text">
                                This invite could not be validated. If you think this is an error please contact the
                                administrator or create a issue on the
                                <a href="https://github.com/codalab/competitions-v2">CODALAB GITHUB</a>.
                            </div>
                        </div>
                        <div class="extra">
                            <a href="/"><button class="ui right floated button primary">Return Home</button></a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        self = this
        self.state = 'loading'
        self.queryString = window.location.search
        self.urlParams = new URLSearchParams(self.queryString)
        self.data = {token: self.urlParams.get('token')}

        self.one('mount', () => {
            CODALAB.api.validate_organization_invite(self.data)
                .done((data) => {
                    self.invite_data = data
                    self.state = 'invite_valid'
                    setTimeout(self.update, 250)
                })
                .fail((response) => {
                    if (response.status === 301){
                        self.state = 'already_accepted'
                        let org_url = response.responseJSON.redirect_url
                        if (org_url === undefined) {
                            org_url = '/'
                        }
                        setTimeout((redirect_url = org_url) => {
                            window.location.href = redirect_url
                        }, 3250)
                    }
                    else if (response.status === 400){
                        self.state = 'invite_not_found'
                    }
                    else if (response.status === 403){
                        self.state = 'user_invite_mismatch'
                    }
                    else {
                        self.state = 'unknown_error'
                    }
                    setTimeout(self.update, 250)
                })
        })

        self.accept_invite = () => {
            CODALAB.api.update_organization_invite(self.data, 'POST')
                .done((data) => {
                    if (data.redirect_url !== undefined) {
                        window.location.href = data.redirect_url
                    } else {
                        window.location.href = '/'
                    }

                })
                .fail((response) => {
                    toastr.error('Oops! An error has occurred. Try refreshing and then trying again.')
                })
        }
        self.reject_invite = () => {
            data = {}
            CODALAB.api.update_organization_invite(self.data, 'DELETE')
                .done((data) => {
                    window.location.href = '/'
                })
                .fail((response) => {
                    toastr.error('Oops! An error has occurred. Try refreshing and then trying again.')
                })
        }
    </script>
</organization-invite>
