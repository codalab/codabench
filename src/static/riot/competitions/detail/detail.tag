<competition-detail>
        <submission-upload phases="{ competition.phases }"></submission-upload>

    <script>
        var self = this

        self.one("mount", function () {
            self.update_competition_data()
        })

        self.update_competition_data = function() {
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
    </style>
</competition-detail>