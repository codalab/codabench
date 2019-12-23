<leaderboards>
    <table class="ui celled selectable table ">
        <thead>
        <tr>
            <th colspan="100%" style="text-align: center;">
                { selected_leaderboard.title }
            </th>
        </tr>
        <tr>
            <th>#</th>
            <th each="{ column, index in selected_leaderboard.columns }" if="{!_.includes(hidden_column_indexes, index)}">{ column.title }</th>
        </tr>
        </thead>
        <tbody>
        <tr if="{_.isEmpty(selected_leaderboard.submissions)}" class="center aligned">
            <td colspan="100%">
                <em>No submissions have been added to this leaderboard yet!</em>
            </td>
        </tr>
        <tr each="{ submission, index in selected_leaderboard.submissions }">
            <td class="collapsing">
                {index + 1}
            </td>
            <td each="{ score_column, col_index in submission.scores }" if="{!_.includes(hidden_column_indexes, col_index)}">{ score_column.score }</td>
        </tr>
        </tbody>
    </table>
    <script>
        let self = this
        self.selected_leaderboard = {}
        self.hidden_column_indexes = []

        self.update_leaderboard = () => {
            if (_.isEmpty(self.selected_leaderboard)) {
                return
            }
            self.hidden_column_indexes = _.map(self.selected_leaderboard.columns, (col, index) => {
                if (col.hidden) {
                    return index
                }
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
    </style>
</leaderboards>