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
                        Error(s) saving benchmark
                    </div>
                    <errors errors="{errors}"></errors>
                </div>

                <div class="ui six item secondary pointing menu">
                    <a class="active item" data-tab="competition_details">
                        <i class="checkmark box icon green" show="{ valid_sections.details && !errors.details }"></i>
                        <i class="minus circle icon red" show="{ errors.details }"></i>
                        Details
                    </a>
                    <a class="item" data-tab="participation">
                        <i class="checkmark box icon green" show="{ valid_sections.participation && !errors.participation }"></i>
                        <i class="minus circle icon red" show="{ errors.participation }"></i>
                        Participation
                    </a>
                    <a class="item" data-tab="pages">
                        <i class="checkmark box icon green" show="{ valid_sections.pages && !errors.pages }"></i>
                        <i class="minus circle icon red" show="{ errors.pages }"></i>
                        Pages
                    </a>
                    <a class="item" data-tab="phases">
                        <i class="checkmark box icon green" show="{ valid_sections.phases && !errors.phases }"></i>
                        <i class="minus circle icon red" show="{ errors.phases }"></i>
                        Phases
                    </a>
                    <a class="item" data-tab="leaderboard">
                        <i class="checkmark box icon green" show="{ valid_sections.leaderboards && !errors.leaderboards }"></i>
                        <i class="minus circle icon red" show="{ errors.leaderboards }"></i>
                        Leaderboard
                    </a>
                    <a class="item" data-tab="collaborators">
                        <i class="checkmark box icon green" show="{ valid_sections.collaborators && !errors.collaborators }"></i>
                        <i class="minus circle icon red" show="{ errors.collaborators }"></i>
                        Administrators
                    </a>
                </div>
                <div class="ui active tab" data-tab="competition_details">
                    <competition-details errors="{ errors.details }"></competition-details>
                </div>
                <div class="ui tab" data-tab="participation">
                    <competition-participation errors="{ errors.participation}"></competition-participation>
                </div>
                <div class="ui tab" data-tab="pages">
                    <competition-pages errors="{ errors.pages }"></competition-pages>
                </div>
                <div class="ui tab" data-tab="phases">
                    <competition-phases errors="{ errors.phases }"></competition-phases>
                </div>
                <div class="ui tab" data-tab="leaderboard">
                    <competition-leaderboards errors="{ errors.details }"></competition-leaderboards>
                </div>
                <div class="ui tab" data-tab="collaborators">
                    <competition-collaborators errors="{ errors.details }"></competition-collaborators>
                </div>
            </div>
        </div>

        <div class="center aligned row">
            <div class="column">
                <div class="ui checkbox publish-checkbox">
                    <input type="checkbox" ref="publish">
                    <label>Publish</label>
                </div>
                <button selenium="save4" class="ui primary button { disabled: !are_all_sections_valid() }" onclick="{ save }">
                    Save
                </button>
                <button class="ui basic red button discard" onclick="{ discard }">
                    Discard Changes
                </button>
                <!--  Show back button when updating only  -->
                <a if="{opts.competition_id}" class="ui secondary basic button" href="{URLS.COMPETITION_DETAIL(opts.competition_id)}">Back To Competition</a>
                <!--  Show help when creating only  -->
                <help_button if="{!opts.competition_id}" href="https://github.com/codalab/competitions-v2/wiki/Competition-Creation:-Form"></help_button>
            </div>
        </div>
    </div>

    <script>
        var self = this
        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.competition = {}
        self.valid_sections = {
            details: false,
            pages: false,
            participation: false,
            phases: false,
            leaderboards: false,
            collaborators: false
        }
        self.optional_sections = [
            'collaborators',
        ]

        self.required_sections = _.filter(_.keys(self.valid_sections), section => !self.optional_sections.includes(section))

        self.errors = {}

        self.one("mount", function () {
            // tabs
            $('.menu .item', self.root).tab({
                history: true,
                historyType: 'hash',
                onVisible: (tab_name) => {
                    if (_.includes(['participation', 'competition_details'], tab_name)) {
                        CODALAB.events.trigger('update_codemirror')
                    }
                }
            })
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
                    for(phase of self.competition.phases){
                        phase.task_instances = []
                        for(task of phase.tasks){
                            phase.task_instances.push({
                                task: task.value,
                                phase: phase.id,
                                order_index: phase.task_instances.length,
                            })
                        }
                    }
                    self.refs.publish.checked = self.competition.published
                    CODALAB.events.trigger('competition_loaded', self.competition)
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition");
                });
            self.update()
        }

        self.are_all_sections_valid = function () {
            return _.every(_.map(self.required_sections, section => self.valid_sections[section]))
        }

        self.discard = function () {
            if (confirm('Are you sure you want to discard your changes?')) {
                window.location.href = window.URLS.COMPETITION_MANAGEMENT
            }
        }

        self.save = function () {
            self.competition["queue"] = parseInt(self.competition["queue"])
            if (typeof(self.competition["queue"]) === "NaN" ) {
                self.competition["queue"] = null
            }
            self.competition.published = self.refs.publish.checked
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
                if (phase.task_instances && _.some(phase.task_instances, Object)) {
                    phase.task_instances.task = _.map(phase.task_instances.task, task => task.key || task.value)
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
            self.competition_return = JSON.parse(JSON.stringify(self.competition))
            for(phase of self.competition_return.phases){
                for(taskord of phase.task_instances){
                    taskord.phase = phase.id
                }
                phase.tasks = phase.task_instances
                delete phase.task_instances
            }

            // Send competition_id for either create or update, won't hurt anything but is
            // useless for creation
            api_endpoint(self.competition_return, self.opts.competition_id)
                .done(function (response) {
                    self.errors = {}
                    self.update()
                    toastr.success("Competition saved!")
                    window.location.href = window.URLS.COMPETITION_DETAIL(response.id)
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
                    if(self.opts.competition_id){
                        toastr.error("Creation failed, error occurred")
                    }else{
                        toastr.error("Updation failed, error occurred")
                    }
                })

        }
        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_data_update', function (data) {
            Object.assign(self.competition, data)
            self.update()
        })
        CODALAB.events.on('competition_is_valid_update', function (name, is_valid) {
            self.valid_sections[name] = is_valid
            self.update()
        })
    </script>
    <style type="text/stylus">
        .publish-checkbox
            margin-right 10px
        .ui.basic.red.button.discard:hover
            background-color #db2828 !important
            color white !important
        .ui.basic.secondary.button:hover
            background-color #1b1c1d !important
            color white !important
    </style>
</competition-form>
