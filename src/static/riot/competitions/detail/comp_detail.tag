<comp-detail>
    <comp-detail-title class="comp-detail-paragraph-text" competition={competition}></comp-detail-title>
    <comp-tabs class="comp-detail-paragraph-text" competition={competition}></comp-tabs>
    <style type="text/stylus">
        .comp-detail-paragraph-text
            font-size 16px !important
            line-height 20px !important
    </style>
    <script>
        var self = this

        self.competition = {}

        Object.assign(self.competition, {
            "title": "Iris Data Challenge",
            "description": "An iris data challenge brought to you by Chalearn to accelerate the growth of machine learning",
            "pages": [
                {
                    "title": "Overview",
                    "content": "This competition aims to mimic real ones",
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
                    "title": "First Phase",
                    "number": 1,
                    "start": "2018-12-01T00:00:00Z",
                    "end": "2018-12-05T00:00:00Z",
                    "description": "description here",
                    "input_data": null,
                    "reference_data": null,
                    "scoring_program": null,
                    "ingestion_program": null,
                    "public_data": null,
                    "starting_kit": null
                },
                {
                    "title": "Second Phase",
                    "number": 2,
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
                    "title": "Final Phase",
                    "number": 3,
                    "start": "2018-12-06T00:00:00Z",
                    "end": "2018-12-08T00:00:00Z",
                    "description": "another description",
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

        console.log(self.competition)
    </script>
    <style type="text/stylus">
        :scope
            min-height 500px
            width inherit
    </style>
</comp-detail>
