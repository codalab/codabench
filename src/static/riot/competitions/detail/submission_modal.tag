<submission-modal>
    <div class="content">
        <div class="ui {three: submission.admin}{two: !submission.admin} item small green menu">
            <div class="active item" data-tab="downloads">Downloads</div>
            <div class="item" data-tab="logs">Logs</div>
            <div class="item" data-tab="admin" if="{submission.admin}">Admin</div>
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
        <div class="ui tab" data-tab="admin" if="{submission.admin}">
            <div class="ui centered grid">
                <div class="ui fourteen wide column">
                    <div each="{leaderboard in leaderboards}">
                        <h3>{leaderboard.title}</h3>
                        <form id="score_update_form">
                            <table class="ui table">
                                <thead>
                                <tr>
                                    <th each="{column in columns}">
                                        {column.title}
                                    </th>
                                </tr>
                                </thead>
                                <tbody>
                                <tr>
                                    <td each="{column in columns}">
                                        <input type="number" name="{ column.score_id }" disabled="{ !!column.computation }"
                                               value="{ column.score }" step="any">
                                    </td>
                                </tr>
                                </tbody>
                            </table>
                            <button class="ui blue button" style="margin-bottom: 15px" onclick="{ update_scores }">Submit
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this
        self.submission = {}
        self.logs = {}
        self.leaderboards = []
        self.columns = []

        self.update_scores = function (event) {
            event.preventDefault()
            let data = get_form_data($('#score_update_form', self.root))
            console.log(data)
            _.forEach(_.keys(data), (key) => {
                CODALAB.api.update_submission_score(key, {score: data[key]})
                    .done(function (data) {
                        toastr.success('Score updated')
                        CODALAB.events.trigger('score_updated')
                    })
            })
        }

        self.get_score_details = function (column) {
            try {
                let score = _.filter(self.submission.scores, (score) => {
                    return score.index === column.index
                })[0]
                return [score.score, score.id]
            } catch {
                return ['', '']
            }
        }

        CODALAB.events.on('submission_clicked', function (submission) {
            // reset logs and leaderboards for new submission to write to
            self.logs = {}
            self.leaderboards = []
            self.submission = submission
            self.columns = []
            console.log(submission)
            CODALAB.api.get_submission_files(submission.id)
                .done(function (data) {
                    self.submission.result = data.result
                    self.submission.data_file = data.data_file
                    data.logs.forEach(function (item) {
                        $.get(item.data_file)
                            .done(function (content) {
                                self.logs[item.name] = content
                                self.update()
                            })
                    })
                    _.forEach(data.leaderboards, function (leaderboard_pk) {
                        CODALAB.api.get_leaderboard_details(leaderboard_pk)
                            .done(function (data) {
                                self.leaderboards.push(data)
                                self.update()

                                _.forEach(data.columns, (column) => {
                                    let col = {
                                        title: column.title,
                                        computation: column.computation,
                                    }
                                    let [score, score_id] = self.get_score_details(column)
                                    col.score = score
                                    col.score_id = score_id
                                    self.columns.push(col)
                                })
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