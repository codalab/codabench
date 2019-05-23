<registration>
    <div if="{!status}" class="ui grid">
        <div class="row">
            <p>You have not yet registered for this competition.</p>
            <p>
                To participate in this competition, you must accept its specific terms and conditions. After you
                register, the competition organizer will review your application and notify you when your participation
                is
                approved.
            </p>
        </div>
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
    </div>

    <div if="{status}">
        Your current status is: {_.startCase(status)}
    </div>

    <script>
        let self = this
        self.on('mount', () => {
            self.accepted = false
        })

        CODALAB.events.on('competition_loaded', (competition) => {
            self.competition_id = competition.id
            self.status = competition.participant_status
            self.update()
        })

        self.accept_toggle = () => {
            self.accepted = !self.accepted
        }

        self.submit_registration = () => {
            CODALAB.api.submit_competition_registration(self.competition_id)
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
                    toastr.error('Something went wrong.')
                })
        }
    </script>
</registration>