<competition-form>
    <div class="ui middle aligned stackable grid container">
        <div class="row centered">
            <div class="twelve wide column">
                <div class="ui top pointing secondary menu">
                    <a class="active item" data-tab="competition_details">
                        <i class="checkmark box icon green" show="{ sections.details.valid }"></i> Competition details
                    </a>
                    <a class="item" data-tab="pages">
                        <i class="checkmark box icon green" show="{ sections.pages.valid }"></i> Pages
                    </a>
                    <a class="item" data-tab="phases">
                        <i class="checkmark box icon green" show="{ sections.phases.valid }"></i> Phases
                    </a>
                    <a class="item" data-tab="leaderboard">
                        <i class="checkmark box icon green" show="{ sections.leaderboards.valid }"></i>  Leaderboard
                    </a>
                    <a class="item" data-tab="collaborators">
                        <i class="checkmark box icon green" show="{ sections.collaborators.valid }"></i> Collaborators
                    </a>
                </div>

                <div class="ui bottom active tab" data-tab="competition_details">
                    <competition-details></competition-details>
                </div>
                <div class="ui bottom tab" data-tab="pages">
                    <competition-pages></competition-pages>
                </div>
                <div class="ui bottom tab" data-tab="phases">
                    <competition-phases></competition-phases>
                </div>
                <div class="ui bottom tab" data-tab="leaderboard">
                    <competition-leaderboards-form></competition-leaderboards-form>
                </div>
                <div class="ui bottom tab" data-tab="collaborators">
                    <competition-collaborators></competition-collaborators>
                </div>
            </div>
        </div>

        <div class="row centered">


            <!--

            REMEMBER TO MAKE THIS DISABLED UNTIL VALID!

            <button class="ui primary button disabled" onclick="{ save }">
            -->

            <button class="ui primary button" onclick="{ save }">
                Save
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

        self.one("mount", function () {
            // tabs
            $('.menu .item').tab()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
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

            // DO THE BULK!
            CODALAB.api.create_competition(self.competition)
                .done(function () {
                    toastr.success("Competition successfully created!")
                })
                .fail(function (response) {
                    toastr.error("Creation failed, error occurred");
                });
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