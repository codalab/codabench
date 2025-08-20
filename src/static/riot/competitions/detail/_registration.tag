<registration>
    <div if="{!status}">
        <div class="ui yellow message">
            <div class="row">
                <div class="column">
                        <h3>You have not yet registered for this competition.</h3>
                        <p>
                            To participate in this competition, you must accept its specific
                            <a href="" onclick="{show_modal}">terms and conditions</a>.
                            <span if="{registration_auto_approve}">This competition <strong>does not</strong>
                            require approval, once you register, you will immediately be able to participate.</span>
                        </p>

                        <p if="{!registration_auto_approve}">
                            This competition <strong>requires approval</strong> from the competition organizers. After
                            submitting your registration request, an email
                            will be sent to the competition organizers notifying them of your request. Your application will
                            remain pending until they
                            approve or deny it.
                        </p>
                </div>
            </div>
            <virtual if="{CODALAB.state.user.logged_in}">
                <div class="row">
                    <div class="ui checkbox">
                        <input type="checkbox" id="accept-terms" onclick="{accept_toggle}">
                        <label for="accept-terms">I accept the terms and conditions of the competition.</label>
                    </div>
                </div>
                <div class="row">
                    <button class="ui primary button {disabled: !accepted}" onclick="{submit_registration}">
                        Register
                    </button>
                </div>
            </virtual>
            <div class="row" if="{!CODALAB.state.user.logged_in}">
                <div class="column">
                    <a href="{URLS.LOGIN}?next={location.pathname}">Log In</a> or
                    <a href="{URLS.SIGNUP}" target="_blank">Sign Up</a> to register for this competition.
                </div>
            </div>
        </div>
    </div>

    <div if="{status}">
        <div if="{status === 'pending'}" class="ui yellow message">
            <h3>Registration Status: {_.startCase(status)}</h3>
            Your request to participate in this competition is waiting for an approval from the competition organizer.
        </div>
        <div if="{status === 'denied'}" class="ui red message">
            <h3>Registration Status: {_.startCase(status)}</h3>
            Your request to participate in this competition is denied. Please contact the competition organizer for more details.
        </div>
    </div>

    <div ref="terms_modal" class="ui modal">
        <div class="header">
            Terms and Conditions
        </div>
        <div ref="terms_content" class="content">

        </div>
        <div class="actions">
            <div class="ui cancel button">
                Close
            </div>
        </div>
    </div>

    <script>
        let self = this
        self.on('mount', () => {
            self.accepted = false
        })

        CODALAB.events.on('competition_loaded', (competition) => {
            self.competition_id = competition.id
            if (self.refs.terms_content) {
                const rendered_content = renderMarkdownWithLatex(competition.terms)
                self.refs.terms_content.innerHTML = ""
                rendered_content.forEach(node => {
                    self.refs.terms_content.appendChild(node.cloneNode(true)); // Append each node
                });
            }
            self.registration_auto_approve = competition.registration_auto_approve
            self.status = competition.participant_status
            self.update()
        })

        self.accept_toggle = () => {
            self.accepted = !self.accepted
        }

        self.show_modal = (e) => {
            if (e) {
                e.preventDefault()
            }
            $(self.refs.terms_modal).modal('show')
        }

        self.submit_registration = () => {

            // Get the value of the 'secret_key' parameter from the URL
            const url = new URL(window.location.href)
            const searchParams = new URLSearchParams(url.search)
            const secretKey = searchParams.get('secret_key')

            CODALAB.api.submit_competition_registration(self.competition_id, secretKey)
                .done(response => {
                    self.status = response.participant_status
                    if (self.status === 'approved') {
                        toastr.success('You have been registered!')
                        CODALAB.api.get_competition(self.competition_id)
                            .done(competition => {
                                CODALAB.events.trigger('competition_loaded', competition)
                            })
                    } else {
                        toastr.success('Your registration application is being processed!')
                    }
                    self.update()
                })
                .fail(response => {
                    toastr.error('Error submitting your registration application.')
                })
        }
    </script>
</registration>