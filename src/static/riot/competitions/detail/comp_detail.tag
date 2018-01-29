<comp-detail>

    <!--<div class="ui container grid">-->

        <comp-detail-title></comp-detail-title>

        <comp-tabs></comp-tabs>

        <comp-run-info></comp-run-info>

        <comp-phase-info></comp-phase-info>

        <comp-stats></comp-stats>

        <comp-tags></comp-tags>

    <!--</div>-->

    <script>
        var self = this

        self.competition = {}

        Object.assign(self.competition, {
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
    </script>
</comp-detail>