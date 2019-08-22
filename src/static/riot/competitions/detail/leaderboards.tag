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
            <th each="{ column in selected_leaderboard.columns }">{ column.title }</th>
        </tr>
        </thead>
        <tbody>
        <tr if="{_.get(selected_leaderboard.submissions, 'length', 0) === 0}" class="center aligned"><td colspan="3"><em>No submissions have been added to this leaderboard yet!</em></td></tr>
        <tr each="{ submission in selected_leaderboard.submissions }">
            <td class="collapsing">
                #
            </td>
            <td each="{ score_column in submission.scores }">{ score_column.score }</td>
        </tr>
        </tbody>
    </table>
    <script>
        var self = this
        self.selected_leaderboard = {}
        self.selected_leaderboard_index = {}

        self.one("updated", function () {
            // Get the actual data
            self.update_leaderboards()
        })

        self.update_leaderboards = function () {
            if (!self.opts.leaderboards) {
                return
            }

            self.opts.leaderboards.forEach(function (leaderboard) {
                CODALAB.api.get_leaderboard(leaderboard.id)
                    .done(function (data) {
                        leaderboard.submissions = data.submissions
                        self.selected_leaderboard = self.opts.leaderboards[0]
                        self.selected_leaderboard_index = self.selected_leaderboard.id
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not find competition")
                    })
            })
        }

        CODALAB.events.on('leaderboard_selected', function (selected_leaderboard) {
            self.selected_leaderboard = selected_leaderboard
        })

        CODALAB.events.on('submission_added_to_leaderboard', () => self.update_leaderboards())

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