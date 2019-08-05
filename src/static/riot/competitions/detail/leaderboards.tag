<leaderboards>
    <table each="{ leaderboard in opts.leaderboards }" class="ui celled selectable table">
        <thead>
        <tr>
            <th colspan="100%" style="text-align: center;">
                { leaderboard.title }
            </th>
        </tr>
        <tr>
            <th>#</th>
            <th each="{ column in leaderboard.columns }">{ column.title }</th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ submission in leaderboard.submissions }">
            <td class="collapsing">
                #
            </td>
            <td each="{ score_column in submission.scores }">{ score_column.score }</td>
        </tr>
        </tbody>
    </table>
    <script>
        var self = this

        self.one("updated", function () {
            // Get the actual data
            self.update_leaderboards()
        })

        self.update_leaderboards = function () {
            self.opts.leaderboards.forEach(function(leaderboard){
                CODALAB.api.get_leaderboard(leaderboard.id)
                    .done(function (data) {
                        leaderboard.submissions = data.submissions
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not find competition")
                    })
            })
        }

    </script>
    <style type="text/stylus">
        :scope
            display: block
            width: 100%
            height: 100%
    </style>
</leaderboards>