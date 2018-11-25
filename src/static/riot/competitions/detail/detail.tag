<competition-detail>
    <div class="ui top attached tabular menu">
        <a class="active item" data-tab="submissions">Submissions</a>
        <a class="item" data-tab="leaderboard">Leaderboards</a>
    </div>
    <div class="ui bottom attached active tab segment" data-tab="submissions">
        <submission-upload phases="{ competition.phases }"></submission-upload>
    </div>
    <div class="ui bottom attached tab segment" data-tab="leaderboard">
        <leaderboards competition_pk="{ competition.id }" leaderboards="{ competition.leaderboards }"></leaderboards>
    </div>

    <script>
        var self = this

        self.one("mount", function () {
            // Setup tabs
            $('.menu .item', self.root).tab()

            // Get the actual data
            self.update_competition_data()
        })

        self.update_competition_data = function () {
            CODALAB.api.get_competition(self.opts.competition_pk)
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
        :scope
            display block
            width 100%
            height 100%

        .ui.inverted.table
            background #44586b
    </style>
</competition-detail>
