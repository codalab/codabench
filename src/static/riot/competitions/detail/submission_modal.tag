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
                        <td class="selectable file-download"><a href="{ data_file }"><i class="file archive outline icon"></i> Submission File</a></td>
                    </tr>
                    <tr>
                        <td class="selectable file-download"><a href="{ result }"><i class="file outline icon"></i>Output from prediction step</a></td>
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
        <submission-scores leaderboards="{leaderboards}"></submission-scores>
    </div>
    <script>
        var self = this
        self.submission = {}
        self.logs = {}
        self.leaderboards = []
        self.columns = []


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
        self.update_submission_details = () => {
            CODALAB.api.get_submission_details(self.submission.id)
                .done(function (data) {
                    self.leaderboards = data.leaderboards
                    self.result = data.result
                    self.data_file = data.data_file
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
        }
        self.on('update', () => {
            if (!self.submission || self.submission !== opts.submission) {
                self.submission = opts.submission
                self.update_submission_details()
                $('.menu .item', self.root).tab()
            }
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
        .modal-tab
            height 530px
        .file-download
            margin-top 25px !important
            margin-botton 25px !important
        #downloads thead tr th, #downloads tbody tr td
            font-size 16px !important
    </style>
</submission-modal>
