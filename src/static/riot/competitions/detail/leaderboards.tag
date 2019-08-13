<leaderboards>
    <table class="ui celled selectable table">
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

        CODALAB.events.on('leaderboard_selected', function (selected_leaderboard) {
            self.selected_leaderboard = selected_leaderboard
            console.log('--------------')
            console.log(selected_leaderboard)
            console.log('--------------')
        })

    </script>
    <style type="text/stylus">
        :scope
            display: block
            width: 100%
            height: 100%
    </style>
</leaderboards>