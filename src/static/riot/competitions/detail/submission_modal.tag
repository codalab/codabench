<submission-modal>
    <div class="content">
        <div class="ui three item small green menu">
            <div class="active item" data-tab="downloads">Downloads</div>
            <div class="item" data-tab="logs">Logs</div>
            <div class="item" data-tab="admin">Admin</div>
        </div>
        <div class="ui tab active" data-tab="downloads">
            <div class="ui relaxed centered grid" style="padding-bottom: 20px">
                <div class="ui fourteen wide column">
                    <div class="ui list">
                        <div class="item">
                            <a href="{ submission.data_file }">My Submission</a>
                        </div>
                        <div class="item">
                            <a href="{ submission.result }">Output from prediction step</a>
                        </div>
                        <div class="item">
                            <a href="#">Output from scoring step</a>
                        </div>
                        <div class="item">
                            <a href="#">Private output from scoring step</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="ui tab" data-tab="logs" style="height: 500px;">
            <div class="ui two item small green secondary pointing menu">
                <div class="active item" data-tab="prediction">Prediction</div>
                <div class="item" data-tab="scoring">Scoring</div>
            </div>
            <div class="ui active tab" data-tab="prediction">
                <div class="ui two column grid">
                    <div class="four wide column" style="height: 100%;">
                        <div class="ui vertical fluid green tabular menu">
                            <div class="active item" data-tab="stdout">stdout</div>
                            <div class="item" data-tab="stderr">stderr</div>
                            <div class="item" data-tab="ingest_stdout">Ingestion stdout</div>
                            <div class="item" data-tab="ingest_stderr">Ingestion stderr</div>
                        </div>
                    </div>
                    <div class="fluid twelve wide stretched column">

                        <div class="ui active tab" data-tab="stdout">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.prediction_stdout }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="stderr">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.prediction_stderr }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="ingest_stdout">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.prediction_ingestion_stdout }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="ingest_stderr">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.prediction_ingestion_stderr }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
            <div class="ui tab" data-tab="scoring">
                <div class="ui two column grid">
                    <div class="four wide column" style="height: 100%;">
                        <div class="ui vertical fluid green tabular menu">
                            <div class="active item" data-tab="stdout">stdout</div>
                            <div class="item" data-tab="stderr">stderr</div>
                            <div class="item" data-tab="ingest_stdout">Ingestion stdout</div>
                            <div class="item" data-tab="ingest_stderr">Ingestion stderr</div>
                        </div>
                    </div>
                    <div class="fluid twelve wide stretched column">

                        <div class="ui active tab" data-tab="stdout">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.scoring_stdout }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="stderr">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.scoring_stderr }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="ingest_stdout">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.scoring_ingestion_stdout }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="ingest_stderr">
                            <div class="ui grid">
                                <div class="fifteen wide column">
                                    <div class="ui inverted segment log">
                                        <pre>{ logs.scoring_ingestion_stderr }</pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="ui tab" data-tab="admin">
            <h3>Score change voodoo magic</h3>
<!--
            For each leaderboard in phase.leaderboards:
                For each column in leaderboard:
                    Make an input box for this _column index_


            for each leaderboard:
                For each score in submission.scores on that leaderboard
                    Fill input box mapping to _column index_
-->



        </div>
    </div>
    <script>
        var self = this
        self.submission = {}
        self.logs = {}

        CODALAB.events.on('submission_clicked', function (submission) {
            self.submission = submission
            CODALAB.api.get_submission_files(submission.id)
                .done(function (data) {
                    self.submission.result = data.result
                    self.submission.data_file = data.data_file
                    data.logs.forEach(function (item) {
                        $.get(item.data_file)
                            .done(function(content) {
                                self.logs[item.name] = content
                                self.update()
                            })
                    })
                })
        })


    </script>

    <style>
        .log {
            height: 415px;
            max-height: 415px;
            overflow: auto;
        }
    </style>
</submission-modal>