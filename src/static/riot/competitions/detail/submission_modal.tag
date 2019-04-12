<submission-modal>
    <div class="ui large green pointing menu">
        <div class="active item" data-tab="downloads">DOWNLOADS</div>
        <div class="item" data-tab="logs">LOGS</div>
        <div class="item" data-tab="admin" if="{submission.admin}">ADMIN</div>
    </div>
    <div class="ui tab active modal-tab" data-tab="downloads">
        <div class="ui relaxed centered grid">
            <div class="ui fifteen wide column">
                <div class="ui horizontal divider"></div>
                <table class="ui very basic table" id="downloads">
                    <thead>
                    <tr>
                        <th><i class="download icon"></i> Files</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td class="selectable file-download"><a href="{ submission.data_file }"><i class="file archive outline icon"></i> Submission File</a></td>
                    </tr>
                    <tr>
                        <td class="selectable file-download"><a href="{ submission.result }"><i class="file outline icon"></i>Output from prediction step</a></td>
                    </tr>
                    <tr>
                        <td class="selectable file-download"><a href="#"><i class="file outline icon"></i>Output from scoring step</a></td>
                    </tr>
                    <tr>
                        <td class="selectable file-download"><a href="#"><i class="file outline icon"></i>Private output from scoring step</a></td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <div class="ui tab modal-tab" data-tab="logs">
        <div class="ui grid">
            <div class="three wide column">
                <div class="ui fluid vertical secondary menu">
                    <div class="active item" data-tab="prediction">Prediction Logs</div>
                    <div class="item" data-tab="scoring">Scoring Logs</div>
                </div>
            </div>
            <div class="thirteen wide column">
                <div class="ui active tab" data-tab="prediction">
                    <div class="ui top attached inverted pointing menu">
                        <div class="active item" data-tab="p_stdout">stdout</div>
                        <div class="item" data-tab="p_stderr">stderr</div>
                        <div class="item" data-tab="p_ingest_stdout">Ingestion stdout</div>
                        <div class="item" data-tab="p_ingest_stderr">Ingestion stderr</div>
                    </div>

                    <div class="ui active bottom attached inverted segment tab log" data-tab="p_stdout">
                        <pre>{ logs.prediction_stdout }</pre>
                    </div>

                    <div class="ui bottom attached inverted segment tab log" data-tab="p_stderr">
                        <pre>{ logs.prediction_stderr }</pre>
                    </div>

                    <div class="ui bottom attached inverted segment tab log" data-tab="p_ingest_stdout">
                        <pre>{ logs.prediction_ingestion_stdout }</pre>
                    </div>

                    <div class="ui bottom attached inverted segment tab log" data-tab="p_ingest_stderr">
                        <pre>{ logs.prediction_ingestion_stderr }</pre>
                    </div>
                </div>
                <div class="ui tab" data-tab="scoring">
                    <div class="ui top attached inverted pointing menu">
                        <div class="active item" data-tab="s_stdout">stdout</div>
                        <div class="item" data-tab="s_stderr">stderr</div>
                        <div class="item" data-tab="s_ingest_stdout">Ingestion stdout</div>
                        <div class="item" data-tab="s_ingest_stderr">Ingestion stderr</div>
                    </div>

                    <div class="ui active bottom attached inverted segment tab log" data-tab="s_stdout">
                        <pre>{ logs.scoring_stdout }</pre>
                    </div>

                    <div class="ui bottom attached inverted segment tab log" data-tab="s_stderr">
                        <pre>{ logs.scoring_stderr }</pre>
                    </div>

                    <div class="ui bottom attached inverted segment tab log" data-tab="s_ingest_stdout">
                        <pre>{ logs.scoring_ingestion_stdout }</pre>
                    </div>

                    <div class="ui bottom attached inverted segment tab log" data-tab="s_ingest_stderr">
                        <pre>{ logs.scoring_ingestion_stderr }</pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="ui tab leaderboard-tab" data-tab="admin" if="{submission.admin}">
        <form class="ui form" id="score_update_form">
            <div each="{leaderboard in leaderboards}" class="leaderboard">
                <h3>{leaderboard.title}</h3>

                <table class="ui collapsing table">
                    <thead>
                    <tr>
                        <th each="{column in leaderboard.columns}">
                            {column.title}
                        </th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td each="{column in leaderboard.columns}">
                            <input type="number" name="{ column.score_id }"
                                   disabled="{ !!column.computation }"
                                   value="{ column.score }" step="any">
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
            <button class="ui blue button" onclick="{ update_scores }">
                Submit
            </button>
        </form>
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
                    return score.column_key === column.key
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
            // self.columns = []
            self.update()
            var tabs = $('.menu .item', self.root)
            tabs.tab()
            tabs.tab('change tab', 'downloads')
            CODALAB.api.get_submission_details(submission.id)
                .done(function (data) {
                    self.leaderboards = data.leaderboards
                    self.submission.result = data.result
                    self.submission.data_file = data.data_file
                    _.forEach(data.logs, (item) => {
                        $.get(item.data_file)
                            .done(function (content) {
                                self.logs[item.name] = content
                                self.update()
                            })
                    })
                    if (self.submission.admin) {
                        _.forEach(data.leaderboards, (leaderboard) => {
                            _.map(leaderboard.columns, (column) => {
                                let [score, score_id] = self.get_score_details(column)
                                column.score = score
                                column.score_id = score_id
                                return column
                            })
                        })
                    }
                    self.update()
                })
        })
    </script>

    <style type="text/stylus">
        .log
            height 465px
            max-height 465px
            overflow auto
        .leaderboard-tab
            height 515px
            overflow auto
        .leaderboard
            padding-bottom 10px
        .modal-tab
            height 530px
        .file-download
            margin-top 25px !important
            margin-botton 25px !important
        #downloads thead tr th, #downloads tbody tr td
            font-size 16px !important
    </style>
</submission-modal>
