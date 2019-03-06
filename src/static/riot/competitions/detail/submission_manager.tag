<submission-manager>
    <h1>Submission manager</h1>
    <table class="ui celled selectable inverted table">
        <thead>
        <tr>
            <th>#</th>
            <th>File name</th>
            <th class="right aligned" width="50px">Status</th>
            <th class="right aligned" width="50px">Leaderboard?</th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ submission in submissions }">
            <td>1</td>
            <td>{ submission.filename }</td>
            <td class="right aligned">{ submission.status }</td>
            <td class="center aligned">
                <i class="add_to_leaderboard check square large icon { disabled: !submission.leaderboard }" onclick="{ add_to_leaderboard }"></i>
            </td>
        </tr>
        </tbody>
    </table>

    <script>
        var self = this

        self.selected_phase = undefined

        /*self.one("mount", function () {
            // Get the actual data
            self.update_submissions()
        })*/

        self.update_submissions = function () {
            CODALAB.api.get_submissions(self.selected_phase.id)
                .done(function (data) {
                    self.submissions = data
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
        }

        self.add_to_leaderboard = function() {
            console.log(this.submission)
            CODALAB.api.add_submission_to_leaderboard(this.submission.id)
                .done(function (data) {
                    self.update_submissions()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
        }

        CODALAB.events.on('phase_selected', function(selected_phase) {
            console.log("phase_selected")
            console.log(selected_phase)
            self.selected_phase = selected_phase
            self.update_submissions()
        })
        CODALAB.events.on('new_submission_created', function(new_submission_data) {
            self.submissions.unshift(new_submission_data)
            self.update()
        })
    </script>

    <style type="text/stylus">
        //:scope
        //    height 100%

        .add_to_leaderboard
            cursor pointer
            &:hover
                opacity 1 !important
            &.selected
                opacity 1 !important
                color #40f940
    </style>
</submission-manager>
