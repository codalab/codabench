<submission-manager>
    <h1>Submission manager</h1>
    <table class="ui celled selectable inverted table">
        <thead>
        <tr>
            <th>#</th>
            <th>File name</th>
            <th class="right aligned">Status</th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ submission in submissions }">
            <td>1</td>
            <td>{ submission.filename }</td>
            <td class="right aligned">{ submission.status }</td>
        </tr>
        </tbody>
    </table>

    <script>
        var self = this

        self.one("mount", function () {
            // Get the actual data
            self.update_submissions()
        })

        self.update_submissions = function () {
            CODALAB.api.get_submissions(self.opts.competition_pk)
                .done(function (data) {
                    self.submissions = data
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
        }
    </script>

    <style type="text/stylus">
        //:scope
        //    display block
        //    width 100%
        //    height 100%

        .ui.inverted.table
            background #44586b
    </style>
</submission-manager>
