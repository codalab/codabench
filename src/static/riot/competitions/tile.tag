<competition-list>
    <div class="ui vertical stripe segment">
        <div class="ui middle aligned stackable grid container centered">
            <div class="row">
                <div class="fourteen wide column">
                    <div class="ui divided items" if="{opts.competitions}">
                        <competition-tile each="{competition in competitions}"></competition-tile>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this

        self.one("mount", function () {
            if (!self.opts.competitions) {
                // If no competitions specified, get ALL competitions
                CODALAB.api.get_competitions()
                    .done(function (data) {
                        self.opts.competitions = data
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not load competition list....")
                    })
            }
        })

        self.competition = {}
        self.competition_two = {}
        self.competition_three = {}

        Object.assign(self.competition, {
            "title": "Iris Data Challenge",
            "description": "An iris data challenge brought to you by Chalearn to accelearate the growth of machine learning",
            "pages": [
                {
                    "title": "Overview",
                    "content": "This competition aims to mimick real ones",
                    "index": 1
                },
                {
                    "title": "FAQ",
                    "content": "Will I lose all my points?",
                    "index": 2
                }
            ],
            "phases": [
                {
                    "title": "Initial Testing",
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
                },
                {
                    "title": "Initial Feedback",
                    "number": 2,
                    "start": "2018-12-06T00:00:00Z",
                    "end": "2018-12-08T00:00:00Z",
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
                }, {
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
        })

        Object.assign(self.competition_two, {
            "title": "Iris Data Challenge",
            "description": "An iris data challenge brought to you by Chalearn to accelearate the growth of machine learning",
            "pages": [
                {
                    "title": "Overview",
                    "content": "This competition aims to mimick real ones",
                    "index": 1
                },
                {
                    "title": "FAQ",
                    "content": "Will I lose all my points?",
                    "index": 2
                }
            ],
            "phases": [
                {
                    "title": "Initial Testing",
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
                },
                {
                    "title": "Initial Feedback",
                    "number": 2,
                    "start": "2018-12-06T00:00:00Z",
                    "end": "2018-12-08T00:00:00Z",
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
                }, {
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
        })

        Object.assign(self.competition_three, {
            "title": "Iris Data Challenge",
            "description": "An iris data challenge brought to you by Chalearn to accelearate the growth of machine learning",
            "pages": [
                {
                    "title": "Overview",
                    "content": "This competition aims to mimick real ones",
                    "index": 1
                },
                {
                    "title": "FAQ",
                    "content": "Will I lose all my points?",
                    "index": 2
                }
            ],
            "phases": [
                {
                    "title": "Initial Testing",
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
                },
                {
                    "title": "Initial Feedback",
                    "number": 2,
                    "start": "2018-12-06T00:00:00Z",
                    "end": "2018-12-08T00:00:00Z",
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
                }, {
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
        })

        self.competitions = [self.competition, self.competition_two, self.competition_three]

    </script>
</competition-list>
