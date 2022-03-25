<competition-detail>
    <comp-detail-header class="comp-detail-paragraph-text" competition="{ competition }"></comp-detail-header>
    <comp-detail-timeline class="comp-detail-phases" competition="{ competition }"></comp-detail-timeline>
    <comp-tabs class="comp-detail-paragraph-text" competition="{ competition }"></comp-tabs>
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
                    let phase = _.find(self.competition.phases, p => p.status === 'Current')
                    CODALAB.events.trigger('phase_selected', phase ? phase : self.competition.phases[0])
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
        }

    </script>
    <style type="text/stylus">
        .comp-detail-paragraph-text
            font-size 16px !important
            line-height 20px !important
        :scope
            display block
            width 100%
            height 100%

        .ui.inverted.table
            background #44586b

        .ui.modal
            margin 20px

        .ui.table
            color $blue !important

            thead > tr > th
                color $blue !important
                background-color $lightblue !important
    </style>
</competition-detail>
