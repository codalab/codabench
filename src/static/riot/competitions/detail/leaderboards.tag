<leaderboards>
    <table id="leadboardTable" class="ui celled selectable table">
        <thead>
        <tr>
            <th colspan="100%" class="center aligned">
                <p class="leaderboard-title">{ selected_leaderboard.title }</p>
                <div style="visibility: {show_download};" class="float-right">
                    <div class="ui compact menu">
                        <div class="ui simple dropdown item" style="padding: 0px 5px">
                            <i class="download icon" style="font-size: 1.5em; margin: 0;"></i>
                            <div style="padding-top: 8px; right: 0; left: auto;" class="menu">
                                <a href="{URLS.COMPETITION_GET_CSV(competition_id, selected_leaderboard.id)}" target="new" class="item">This CSV</a>
                                <a href="{URLS.COMPETITION_GET_JSON_BY_ID(competition_id, selected_leaderboard.id)}" target="new" class="item">This JSON</a>
                            </div>
                        </div>
                    </div>
                </div>
            </th>
        </tr>
        <tr class="task-row">
            <th>Task:</th>
            <th></th>
            <th each="{ task in selected_leaderboard.tasks }" class="center aligned" colspan="{ task.colWidth }">{ task.name }</th>
        </tr>
        <tr>
            <th class="center aligned">#</th>
            <th>Username</th>
            <th class="center aligned" each="{ column in columns }" colspan="1">{column.title}</th>
        </tr>
        </thead>
        <tbody>
        <tr if="{_.isEmpty(selected_leaderboard.submissions)}" class="center aligned">
            <td colspan="100%">
                <em>No submissions have been added to this leaderboard yet!</em>
            </td>
        </tr>
        <tr each="{ submission, index in selected_leaderboard.submissions}">
            <td class="collapsing index-column center aligned">
                <gold-medal if="{index + 1 === 1}"></gold-medal>
                <silver-medal if="{index + 1 === 2}"></silver-medal>
                <bronze-medal if="{index + 1 === 3}"></bronze-medal>
                <fourth-place-medal if="{index + 1 === 4}"></fourth-place-medal>
                <fifth-place-medal if="{index + 1 === 5}"></fifth-place-medal>
                <virtual if="{index + 1 > 5}">{index + 1}</virtual>
            </td>
            <td>{ submission.owner }</td>
            <td each="{ column in columns }">{ get_score(column, submission.scores) } </td>
        </tr>
        </tbody>
    </table>

    <script>
        let self = this
        self.selected_leaderboard = {}
        // self.hidden_column_keys = []
        self.columns = []
        // self.organized_submissions = []
        self.phase_id = null
        self.competition_id = null

        self.get_score = function(column, scores) {
            let score = _.get(_.find(scores, {'task_id': column.task_id, 'column_key': column.key}), 'score')
            if (score) {
                return score
            }
            return 'n/a'
        }

        self.update_leaderboard = () => {
            CODALAB.api.get_leaderboard_for_render(self.phase_id)
                .done(responseData => {
                    self.selected_leaderboard = responseData
                    console.log(self.selected_leaderboard)
                    self.columns = []
                    for(taskNum = 0; taskNum < Object.keys(self.selected_leaderboard.tasks).length; taskNum++){
                        for(colNum = 0; colNum < Object.keys(self.selected_leaderboard.tasks[taskNum].columns).length; colNum++){
                            col = self.selected_leaderboard.tasks[taskNum].columns[colNum]
                            col.task_id = self.selected_leaderboard.tasks[taskNum].id
                            self.columns.push(col)
                        }
                    }
                    self.update()
                })
            // if (_.isEmpty(self.selected_leaderboard)) {
            //     return
            // }
            // self.hidden_column_keys = _.map(self.selected_leaderboard.columns, col => {
            //     if (col.hidden) {
            //         return col.key
            //     }
            // })
            //
            // // Columns are assumed to be the same for each task. Each column on the leaderboard is duplicated once for
            // // each task and assigned a unique column key.
            // self.generated_columns = []
            // _.forEach(self.selected_leaderboard_phase.tasks, task => {
            //     _.forEach(self.selected_leaderboard.columns, col => {
            //         col = Object.assign({}, col)
            //         col['task'] =  task
            //         col['key'] += `_${task['id']}`
            //         self.generated_columns.push(col)
            //     })
            // })
            //
            // // organized_submissions is used to organize submissions by owner so many scores by the same owner are
            // // rendered on the same row of the leaderboard table.
            // let organized_submissions = {}
            // _.forEach(self.selected_leaderboard_phase.submissions, submission => {
            //     submission = JSON.parse(JSON.stringify(submission))
            //     _.forEach(submission['scores'], score => {
            //         score['column_key'] += `_${submission['task']}`
            //     })
            //
            //     if (!organized_submissions[submission['owner']]) {
            //         organized_submissions[submission['owner']] = [submission]
            //     } else {
            //         organized_submissions[submission['owner']].push(submission)
            //     }
            // })
            //
            // self.organized_submissions = []
            // _.forEach(organized_submissions, submission_list => {
            //     let scores = []
            //     _.forEach(submission_list, submission => {
            //         _.forEach(submission.scores, score => {
            //             scores.push(score)
            //         })
            //     })
            //
            //     let submission = {
            //         owner: submission_list[0].owner,
            //         scores: scores,
            //     }
            //     self.organized_submissions.push(submission)
            // })
            //
        }


        CODALAB.events.on('leaderboard_phase_selected', id => {
            self.phase_id = id
            self.update_leaderboard()
        })

        CODALAB.events.on('competition_loaded', (competition) => {
            self.competition_id = competition.id
            self.opts.is_admin ? self.show_download = "visible": self.show_download = "hidden"
        })

        CODALAB.events.on('submission_added_to_leaderboard', self.update_leaderboard)

    </script>
    <style type="text/stylus">
        :scope
            display: block
            width: 100%
            height: 100%

        .celled.table.selectable
            margin 1em 0

        table tbody .center.aligned td
            color #8c8c8c
        .index-column
            min-width 55px
        .leaderboard-title
            position absolute
            left 50%
            transform translate(-50%, 50%)
        .ui.table > thead > tr.task-row > th
            background-color: #e8f6ff !important
    </style>
</leaderboards>
