<errors>
    <ul class="list">
        <li each="{ error_object, field in opts.errors }">
            <strong>{field}:</strong>

            <span each="{error in error_object}">
                <!-- Error is not an object, no need to go deeper -->
                <virtual if="{ error.constructor != Object }">
                    {error}
                </virtual>

                <!-- We have more errors to loop through recursively -->
                <virtual if="{ error.constructor == Object }">
                    <errors errors="{ error }"></errors>
                </virtual>
            </span>
        </li>
    </ul>
</errors>


<competition-form>
    <div class="ui middle aligned stackable grid container">
        <div class="row centered">
            <div class="twelve wide column">

                <div class="ui message error" show="{ Object.keys(errors).length > 0 }">
                    <div class="header">
                        Error(s) saving competition
                    </div>
                    <errors errors="{errors}"></errors>
                </div>

                <div class="ui top pointing six item secondary menu">
                    <a class="active item" data-tab="competition_details">
                        <i class="checkmark box icon green" show="{ sections.details.valid && !errors.details }"></i>
                        <i class="minus circle icon red" show="{ errors.details }"></i>
                        Details
                    </a>
                    <a class="item" data-tab="participation">
                        <i class="checkmark box icon green" show="{ sections.participation.valid && !errors.pages }"></i>
                        <i class="minus circle icon red" show="{ errors.participation }"></i>
                        Participation
                    </a>
                    <a class="item" data-tab="pages">
                        <i class="checkmark box icon green" show="{ sections.pages.valid && !errors.pages }"></i>
                        <i class="minus circle icon red" show="{ errors.pages }"></i>
                        Pages
                    </a>
                    <a class="item" data-tab="phases">
                        <i class="checkmark box icon green" show="{ sections.phases.valid && !errors.phases }"></i>
                        <i class="minus circle icon red" show="{ errors.phases }"></i>
                        Phases
                    </a>
                    <a class="item" data-tab="leaderboard">
                        <i class="checkmark box icon green" show="{ sections.leaderboards.valid && !errors.leaderboards }"></i>
                        <i class="minus circle icon red" show="{ errors.leaderboards }"></i>
                        Leaderboard
                    </a>
                    <a class="item" data-tab="collaborators">
                        <i class="checkmark box icon green" show="{ sections.collaborators.valid && !errors.collaborators }"></i>
                        <i class="minus circle icon red" show="{ errors.collaborators }"></i>
                        Collaborators
                    </a>
                </div>

                <div class="ui bottom active tab" data-tab="competition_details">
                    <competition-details errors="{ errors.details }"></competition-details>
                </div>
                <div class="ui bottom tab" data-tab="participation">
                    <h1>Participating in a comp</h1>
                </div>
                <div class="ui bottom tab" data-tab="pages">
                    <competition-pages errors="{ errors.pages }"></competition-pages>
                </div>
                <div class="ui bottom tab" data-tab="phases">
                    <competition-phases errors="{ errors.phases }"></competition-phases>
                </div>
                <div class="ui bottom tab" data-tab="leaderboard">
                    <competition-leaderboards-form errors="{ errors.details }"></competition-leaderboards-form>
                </div>
                <div class="ui bottom tab" data-tab="collaborators">
                    <competition-collaborators errors="{ errors.details }"></competition-collaborators>
                </div>
            </div>
        </div>

        <div class="row centered">
            <button class="ui primary button { disabled: !are_all_sections_valid() }" onclick="{ save_and_publish }">
                Save and Publish
            </button>
            <button class="ui grey button { disabled: !are_all_sections_valid() }" onclick="{ save_as_draft }">
                Save as Draft
            </button>
            <button class="ui basic red button discard" onclick="{ discard }">
                Discard Changes
            </button>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.competition = {}
        self.sections = {
            details: {valid: false},
            pages: {valid: false},
            participation: {valid: false},
            phases: {valid: false},
            leaderboards: {valid: false},
            collaborators: {valid: false}
        }
        self.errors = {}

        self.one("mount", function () {
            // tabs
            $('.menu .item', self.root).tab()

            if (!!self.opts.competition_id) {
                self.update_competition_data(self.opts.competition_id)
            }
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/

        self.update_competition_data = (id) => {
            CODALAB.api.get_competition(id)
                    .done(function (data) {
                        self.competition = data
                        CODALAB.events.trigger('competition_loaded', self.competition)
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not find competition");
                    });
            self.update()
        }

        self.are_all_sections_valid = function () {
            _.forEach(_.keys(self.sections), section => {
                if (section !== 'collaborators') {
                    // collaborators is optional
                    if (!self.sections[section].valid) {
                        return false
                    }
                }
            })
            return true
        }

        self.discard = function () {
            if (confirm('Are you sure you want to discard your changes?')) {
                window.location.href = window.URLS.COMPETITION_MANAGEMENT
            }
        }

        self._save = function (publish) {
            let previous_index, current_index, next_index;
            let now = new Date()

            let current_phase = _.first(_.filter(self.competition.phases, phase => {
                return new Date(phase.start) < now && now < new Date(phase.end)
            }))

            if (current_phase) {
                current_index = current_phase.index
                previous_index = current_index > 0 ? current_index - 1 : null
                next_index = current_index < self.competition.phases.length - 1 ? current_index + 1 : null
            } else {
                let next_phase = _.first(_.filter(self.competition.phases, phase => {
                    return now < new Date(phase.start) && now < new Date(phase.end)
                }))
                if (next_phase) {
                    next_index = next_phase.index
                    previous_index = next_index > 0 ? next_index - 1 : null
                }
            }

            // convert serializer task data to just keys if we didn't edit phases
            // also add phase statuses based on above calculated indexes
            self.competition.phases = _.map(self.competition.phases, phase => {
                if (phase.tasks && typeof(phase.tasks[0]) === "object") {
                    phase.tasks = _.map(phase.tasks, task => task.value)
                }
                switch (phase.index) {
                    case current_index:
                        phase.status = 'Current'
                        break
                    case previous_index:
                        phase.status = 'Previous'
                        break
                    case next_index:
                        phase.status = 'Next'
                        break
                    default:
                        phase.status = null
                }
                return phase
            })


            self.competition.collaborators = _.map(self.competition.collaborators, collab => collab.id ? collab.id : collab)

            var api_endpoint = self.opts.competition_id ? CODALAB.api.update_competition : CODALAB.api.create_competition

            // Send competition_id for either create or update, won't hurt anything but is
            // useless for creation
            api_endpoint(self.competition, self.opts.competition_id)
                .done(function (response) {
                    self.errors = {}
                    self.update()
                    if (publish) {
                        toastr.success("Competition published!")
                        window.location.href = window.URLS.COMPETITION_DETAIL(response.id)
                    } else {
                        toastr.success("Competition saved!")
                        self.update_competition_data(response.id)
                    }
                })
                .fail(function (response) {
                    if (response) {
                        var errors = JSON.parse(response.responseText);

                        // to make errors clearer, move errors for "detail" page into the errors "details" key
                        var details_section_fields = ['title', 'logo']
                        details_section_fields.forEach(function (field) {
                            if (errors[field]) {
                                // initialize section, if not already
                                errors.details = errors.details || []

                                // make temp dict containing key: value
                                var new_error_dict = {}
                                new_error_dict[field] = errors[field]

                                // push it and delete the original
                                errors.details.push(new_error_dict)
                                delete errors[field]
                            }
                        })

                        self.update({errors: errors})
                    }
                    toastr.error("Creation failed, error occurred")
                })

        }

        self.save_and_publish = () => {
            self.competition.published = true
            self._save(self.competition.published)
        }

        self.save_as_draft = () => {
            self.competition.published = false
            self._save(self.competition.published)
        }

        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_data_update', function (data) {
            Object.assign(self.competition, data)
            self.update()
        })
        CODALAB.events.on('competition_is_valid_update', function (name, is_valid) {
            self.sections[name].valid = is_valid
            self.update()
        })
    </script>
    <style type="text/stylus">
        .ui.basic.red.button.discard:hover
            background-color #db2828 !important
            color white !important
    </style>
</competition-form>
