<leaderboards>
    <table id="leadboardTable" class="ui celled selectable table">
        <thead>
        <tr>
            <th colspan="100%" class="center aligned">
                { selected_leaderboard.title }
            </th>
        </tr>
        <tr>
            <th class="center aligned">#</th>
            <th>Username</th>
            <th each="{ column in generated_columns }" if="{!_.includes(hidden_column_keys, column.key)}">{ column.title }</th>
        </tr>
        </thead>
        <tbody>
        <tr if="{_.isEmpty(selected_leaderboard.submissions)}" class="center aligned">
            <td colspan="100%">
                <em>No submissions have been added to this leaderboard yet!</em>
            </td>
        </tr>
        <tr each="{ submission, index in organized_submissions }">
            <td class="collapsing index-column center aligned">
                <gold-medal if="{index + 1 === 1}"></gold-medal>
                <silver-medal if="{index + 1 === 2}"></silver-medal>
                <bronze-medal if="{index + 1 === 3}"></bronze-medal>
                <fourth-place-medal if="{index + 1 === 4}"></fourth-place-medal>
                <fifth-place-medal if="{index + 1 === 5}"></fifth-place-medal>
                <virtual if="{index + 1 > 5}">{index + 1}</virtual>
            </td>
            <td>{ submission[0].owner }</td>
            <td each="{ column in generated_columns }" if="{!_.includes(hidden_column_keys, column.key)}">{ get_score(column, submission ) } </td>
        </tr>
        </tbody>
    </table>
    <script>
        let self = this
        self.selected_leaderboard = {}
        self.hidden_column_keys = []


        self.get_score = function(column, submission) {
            for (i in submission) {
                let score = _.get(_.find(submission[i].scores, {column_key: column.key}), 'score')
                if (score) {
                    return score
                }
            }
            return 'n/a'
        }

        self.update_leaderboard = () => {
            if (_.isEmpty(self.selected_leaderboard)) {
                return
            }
            self.hidden_column_keys = _.map(self.selected_leaderboard.columns, col => {
                if (col.hidden) {
                    return col.key
                }
            })
            self.generated_columns = []
            _.forEach(self.opts.tasks, task => {
                _.forEach(self.selected_leaderboard.columns, col => {
                    col = Object.assign({}, col)
                    col['task'] =  task['id']
                    col['title'] += ` ${task['id']}`
                    col['key'] += `_${task['id']}`
                    self.generated_columns.push(col)
                })
            })

            let organized_submissions = {}
            _.forEach(self.selected_leaderboard.submissions, submission => {
                _.forEach(submission['scores'], score => {
                    score['column_key'] += `_${submission['task']}`
                })

                if (!organized_submissions[submission['owner']]) {
                    organized_submissions[submission['owner']] = [submission]
                } else {
                    organized_submissions[submission['owner']].push(submission)
                }
            })

            self.organized_submissions = []
            _.forEach(organized_submissions, submission_list => {
                self.organized_submissions.push(submission_list)
            })

            self.update()
        }

        self.update_leaderboards = function () {
            if (!self.opts.leaderboards) {
                return
            }
            _.forEach(self.opts.leaderboards, leaderboard => {
                CODALAB.api.get_leaderboard(leaderboard.id)
                    .done(function (data) {
                        leaderboard.submissions = data.submissions
                        self.update_leaderboard()
                    })
                    .fail(function (response) {
                        toastr.error("Could not find leaderboard submissions")
                    })
            })
        }

        CODALAB.events.on('competition_loaded', () => {
            self.selected_leaderboard = self.opts.leaderboards[0]
            self.update_leaderboards()
        })

        CODALAB.events.on('leaderboard_selected', leaderboard => {
            self.selected_leaderboard = leaderboard
            self.update_leaderboard()
        })

        CODALAB.events.on('submission_added_to_leaderboard', self.update_leaderboards)

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
    </style>
</leaderboards>
