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
                <!--
                            <virtual if="{ error_object.constructor == Array }">
                                asdfasdfasdf
                                <span each="{error in error_object}">{error}</span>
                            </virtual>

                            <virtual if="{ error_object.constructor == Object }">
                                AYESSSS
                                <span each="{inline_error, i in error_object}">{inline_error} - {i}</span>
                            </virtual>
                            -->


                <div class="ui top pointing secondary menu">
                    <a class="active item" data-tab="competition_details">
                        <i class="checkmark box icon green" show="{ sections.details.valid && !errors.details }"></i>
                        <i class="minus circle icon red" show="{ errors.details }"></i>
                        Competition details
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
            <button class="ui primary button { disabled: !are_all_sections_valid() }" onclick="{ save }">
                Save
            </button>
            <button class="ui primary button" onclick="{ save }">
                TEST Save
            </button>
            <button class="ui button">
                Discard
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
            'details': {valid: false},
            'pages': {valid: false},
            'phases': {valid: false},
            'leaderboards': {valid: false},
            'collaborators': {valid: false}
        }
        self.errors = {}

        self.one("mount", function () {
            // tabs
            $('.menu .item').tab()

            if (!!self.opts.competition_id) {
                CODALAB.api.get_competition(self.opts.competition_id)
                    .done(function (data) {
                        self.competition = data
                        CODALAB.events.trigger('competition_loaded', self.competition)
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not find competition");
                    });
            }
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.are_all_sections_valid = function () {
            for (var section in self.sections) {
                if (section === 'collaborators') {
                    // collaborators is optional
                    continue;
                }

                if (!self.sections[section].valid) {
                    return false
                }
            }
            return true
        }

        self.save = function () {




            /*Object.assign(self.competition, {
                "title": "asdf",
                "pages": [
                    {
                        "title": "test",
                        "content": "test",
                        "index": 1
                    }
                ],
                "phases": [
                    {
                        "number": 1,
                        "start": "2018-12-01T00:00:00Z",
                        "end": "2018-12-05T00:00:00Z",
                        "description": "test",
                        "input_data": null,
                        "reference_data": null,
                        "scoring_program": null,
                        "ingestion_program": null,
                        "public_data": null,
                        "starting_kit": null
                    }
                ],
                "leaderboards": [
                    {
                        "primary_index": 0,
                        "title": "test",
                        "key": "RESULTS",
                        "columns": [
                            {
                                "computation": null,
                                "computation_indexes": null,
                                "title": "test",
                                "key": "SCORE_1",
                                "sorting": "desc",
                                "index": 0
                            }, {
                                "computation": "avg",
                                "computation_indexes": ["0"],
                                "title": "test",
                                "key": "SCORE_2",
                                "sorting": "desc",
                                "index": 1
                            }
                        ]
                    },{
                        "primary_index": 0,
                        "title": "test",
                        "key": "RESULTS",
                        "columns": [
                            {
                                "computation": null,
                                "computation_indexes": null,
                                "title": "test",
                                "key": "SCORE_1",
                                "sorting": "desc",
                                "index": 0
                            }, {
                                "computation": "avg",
                                "computation_indexes": ["0"],
                                "title": "test",
                                "key": "SCORE_2",
                                "sorting": "desc",
                                "index": 1
                            }
                        ]
                    }
                ],
                "collaborators": []
            })*/


            console.log("MAIN FORM SAVING")

            console.log("competition data:")
            console.log(self.competition)

            var api_endpoint = undefined

            if (!self.opts.competition_id) {
                // CREATE competition
                api_endpoint = CODALAB.api.create_competition
            } else {
                // UPDATE competition
                api_endpoint = CODALAB.api.update_competition
            }

            // Send competition_id for either create or update, won't hurt anything but is
            // useless for creation
            api_endpoint(self.competition, self.opts.competition_id)
                .done(function () {
                    toastr.success("Competition successfully created!")
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

        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_data_update', function (data) {
            Object.assign(self.competition, data)
            self.update()

            console.log("new data:")
            console.log(data)
            console.log("updated competition data")
            console.log(self.competition)
        })
        CODALAB.events.on('competition_is_valid_update', function (name, is_valid) {
            console.log(name + " is_valid -> " + is_valid)
            self.sections[name].valid = is_valid
            self.update()
        })
    </script>
</competition-form>