<leaderboards>
    <table each="{ leaderboard in opts.leaderboards }" class="ui celled selectable inverted table">
        <thead>
        <tr>
            <th colspan="100%" style="text-align: center;">
                { leaderboard.title }
            </th>
        </tr>
        <tr>
            <th>#</th>
            <th each="{ column in leaderboard.columns }">{ column.title }</th>
            <th class="right aligned">Status</th>
        </tr>
        </thead>
        <tbody>
        <tr>
            <td class="collapsing">
                1
            </td>
            <td>1.0</td>
            <td class="right aligned collapsing">Submitting</td>
        </tr>
        </tbody>
    </table>
    <script>
        var self = this

        self.one("mount", function () {
            // Get the actual data
            self.update_leaderboards()
        })

        self.update_leaderboards = function () {
            CODALAB.api.get_leaderboards(self.opts.competition_pk)
                .done(function (data) {
                    self.competition = data
                    CODALAB.events.trigger('competition_loaded', self.competition)
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
        }
    </script>
    <style type="text/stylus">
        .ui.inverted.table
            background #44586b
    </style>
</leaderboards>