<competition-detail>
    <select class="ui dropdown" ref="phase" onchange="{ phase_selected }">
        <option each="{ phase in competition.phases }" value="{ phase.id }">Phase: { phase.name }</option>
    </select>

    <div class="ui top attached tabular menu">
        <a class="active item" data-tab="submissions">Submissions</a>
        <a class="item" data-tab="leaderboard">Leaderboards</a>
    </div>
    <div class="ui bottom attached active tab segment" data-tab="submissions">
        <submission-upload phases="{ competition.phases }"></submission-upload>
        <submission-manager></submission-manager>
    </div>
    <div class="ui bottom attached tab segment" data-tab="leaderboard">
        <leaderboards competition_pk="{ competition.id }" leaderboards="{ competition.leaderboards }"></leaderboards>
    </div>

    <script>
        var self = this

        // Stops page load errors... although we shouldn't be using/referencing empty `competitions` object?
        self.competition = {}

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
                    CODALAB.events.trigger('phase_selected', self.competition.phases[0])
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
        }

        self.phase_selected = function(event, data) {
            // Really gross way of getting phase from the <select>'s <option each={ phase in phases}> jazz
            CODALAB.events.trigger('phase_selected', self.refs.phase.options[self.refs.phase.selectedIndex]._tag.phase)
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
