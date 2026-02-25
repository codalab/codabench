<submission-modal>
    <div class="ui large green pointing menu">
        <div class="active submission-modal item" data-tab="{admin_: submission.admin}downloads">DOWNLOADS</div>
        <div class="submission-modal item" data-tab="{admin_: submission.admin}logs" show="{!opts.hide_output}">LOGS</div>
        <div class="submission-modal item" data-tab="{admin_: submission.admin}graph" show="{!opts.hide_output && opts.show_visualization}">VISUALIZATION</div>
        <div class="submission-modal item" data-tab="admin" if="{submission.admin}">ADMIN</div>
        <div class="submission-modal item" data-tab="{admin_: submission.admin}fact_sheet">FACT SHEET ANSWERS</div>
    </div>
    <!-- Downloads -->
    <div class="ui tab active modal-tab" data-tab="{admin_: submission.admin}downloads">
        <div class="ui relaxed centered grid">
            <div class="ui fifteen wide column">
                <table class="ui table" id="downloads">
                    <thead>
                        <tr>
                            <th><i class="download icon"></i> Files</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="selectable file-download">
                                <a href="{ data_file }"><i class="file archive outline icon"></i> Submission File</a>
                            </td>
                        </tr>
                        <tr>
                            <td class="selectable file-download {disabled: !prediction_result}" show="{!opts.hide_prediction_output}">
                                <a href="{ prediction_result }"><i class="file outline icon"></i>Output from prediction step</a>
                            </td>
                        </tr>
                        <tr>
                            <td class="selectable file-download {disabled: !scoring_result}" show="{!opts.hide_score_output}">
                                <a href="{ scoring_result }"><i class="file outline icon"></i>Output from scoring step</a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <!-- Logs -->
    <div class="ui tab modal-tab" data-tab="{admin_: submission.admin}logs" hide="{opts.hide_output}">
        <div class="ui top attached inverted pointing menu" if="{logTabs.length > 0}">
            <div each="{tab in logTabs}"
                class="submission-modal item {active: tab.fullTabId === activeLogTabId}"
                data-tab="{tab.fullTabId}"
                onclick="{() => { activeLogTabId = tab.fullTabId }}">
                {tab.label}
            </div>
        </div>
        <!-- If no logs -->
        <div class="ui bottom attached inverted segment tab log active" if="{logTabs.length === 0}">
            <pre class="empty">No logs available for this submission.</pre>
        </div>
        <!-- Dynamic tabs -->
        <div each="{tab in logTabs}"
            class="ui bottom attached inverted segment tab log {active: tab.fullTabId === activeLogTabId}"
            data-tab="{tab.fullTabId}">
            <pre class="{empty: isEmpty(tab.content)}">{ showLog(tab.content) }</pre>
        </div>
    </div>
    <!-- Fact sheet -->
    <div class="ui tab modal-tab" data-tab="{admin_: submission.admin}fact_sheet">
        <div class="ui inverted segment log">
            <textarea name="fact-sheet" id="fact_sheet" ref="fact_sheet_text_area">{ JSON.stringify(fact_sheet_answers, null, 2) }</textarea>
        </div>
        <div class="ui button green" onclick="{update_fact_sheet.bind(this)}">Save</div>
    </div>
    <!-- Visualization -->
    <div class="ui tab modal-tab" data-tab="{admin_: submission.admin}graph" show="{opts.show_visualization && (!opts.hide_output || submission.admin)}">
        <iframe src="{detailed_result}" class="graph-frame" show="{detailed_result}"></iframe>
    </div>
    <!-- Admin -->
    <div class="ui tab leaderboard-tab" data-tab="admin" if="{submission.admin}">
        <submission-scores leaderboards="{leaderboards}"></submission-scores>
    </div>

    <script>
        var self = this
        self.submission = {}
        self.logs = {}
        self.leaderboards = []
        self.columns = []

        // Logs helpers
        self.nonEmpty = (v) => !self.isEmpty(v)
        self.showLog = (v) => self.nonEmpty(v) ? self.normalizeLog(v) : "No logs for this tab."
        self.normalizeLog = (v) => {
            if (v == null) return v
            if (Array.isArray(v)) return v.join('\n')
            if (typeof v === "object") {
                try { return JSON.stringify(v, null, 2) } catch { return String(v) }
            }
            return String(v)
        }
        self.isEmpty = (v) => {
            v = self.normalizeLog(v)
            return v == null || (typeof v === "string" && v.trim().length === 0)
        }

        // Dynamic tabs state
        self.logTabs = []
        self.activeLogTabId = null

        self.rebuildLogTabs = () => {
            const prefix = self.submission && self.submission.admin ? 'admin_' : ''
            const candidates = [
            { key:'p_stdout', label:'Prediction output', content: self.logs.prediction_stdout },
            { key:'p_stderr', label:'Prediction errors', content: self.logs.prediction_stderr },
            { key:'p_ing_out', label:'Ingestion output', content: self.logs.prediction_ingestion_stdout },
            { key:'p_ing_err', label:'Ingestion errors', content: self.logs.prediction_ingestion_stderr },
            { key:'s_stdout', label:'Scoring output', content: self.logs.scoring_stdout },
            { key:'s_stderr', label:'Scoring errors', content: self.logs.scoring_stderr },
            { key:'s_ing_out', label:'Scoring ingestion output', content: self.logs.scoring_ingestion_stdout },
            { key:'s_ing_err', label:'Scoring ingestion errors', content: self.logs.scoring_ingestion_stderr },
            ]

            // Keep only non empty tabs
            self.logTabs = candidates
                .filter(t => !self.isEmpty(t.content))
                .map(t => ({
                    ...t,
                    fullTabId: `${prefix}${t.key}`
                }))
            // Select a valid tab as active
            const stillValid = self.logTabs.find(t => t.fullTabId === self.activeLogTabId)
            if (!stillValid) {
                self.activeLogTabId = self.logTabs.length ? self.logTabs[0].fullTabId : null
            }
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
        self.update_submission_details = () => {
            self.logs = {}
            self.rebuildLogTabs()
            self.update()
            CODALAB.api.get_submission_details(self.submission.id)
                .done(function (data) {
                    self.leaderboards = data.leaderboards
                    self.prediction_result = data.prediction_result
                    self.scoring_result = data.scoring_result
                    self.data_file = data.data_file
                    self.detailed_result = data.detailed_result
                    self.fact_sheet_answers = data.fact_sheet_answers

                    _.forEach(data.logs, (item) => {
                        $.get(item.data_file)
                            .done(function (content) {
                                self.logs[item.name] = content
                                self.rebuildLogTabs()
                                self.update()
                                setTimeout(() => {
                                    $(self.root).find('.ui.top.attached.menu .item').tab()
                                }, 0)
                            })
                    })
                    self.rebuildLogTabs()
                    self.update()
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

        self.update_fact_sheet = () => {
            let fact_sheet = self.refs.fact_sheet_text_area.value
            try {
                fact_sheet = JSON.parse(fact_sheet)
            }
            catch (err) {
                toastr.error("Invalid JSON")
                return false
            }
            self.fact_sheet_answers = fact_sheet
            CODALAB.api.update_submission_fact_sheet(self.submission.id, self.fact_sheet_answers)
                .done((data) => {
                    toastr.success('Fact Sheet Answers updated')
                    setTimeout(function () {
                        location.reload()
                    }, 1000)
                })
                .fail((response) => {
                    toastr.error(response.responseText)
                })
        }

        CODALAB.events.on('submission_clicked', () => {
            self.submission = opts.submission
            self.update()
            self.update_submission_details()
            let path = self.submission.admin ? 'admin_downloads' : 'downloads'
            $('.ui.large.green.pointing.menu .submission-modal.item').tab('change tab', path)
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
            margin-bottom 25px !important

        .graph-frame
            height 100%
            width 100%
            overflow scroll
            border none

        #downloads thead tr th, #downloads tbody tr td
            font-size 16px !important

        pre.empty 
            opacity 0.7 

        .log
            color white
            background #1b1c1d

        .log textarea
            width 100%
            height 98%

    </style>
</submission-modal>
