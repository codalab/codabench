<submission-manager>
    <h1>Submission manager</h1>
    <div show="{ opts.admin }" style="padding-bottom: 20px;">
        <a class="ui green button" href="{csv_link}">
            <i class="icon download"></i>Download as CSV
        </a>
        <button class="ui blue button">
            <i class="icon redo"></i>Rerun all submissions per phase
        </button>
    </div>
    <div class="ui icon input">
        <input type="text" placeholder="Search..." ref="search" onkeyup="{ filter }">
        <i class="search icon"></i>
    </div>
    <select class="ui dropdown {hidden: !opts.admin}" ref="phase" onchange="{ filter }">
        <option value="">Phase</option>
        <option value=" ">-----</option>
        <option each="{ phase in opts.competition.phases }" value="{ phase.id }">{ phase.name }</option>
    </select>
    <select class="ui dropdown" ref="status" onchange="{ filter }">
        <option value="">Status</option>
        <option value=" ">-----</option>
        <option value="Cancelled">Cancelled</option>
        <option value="Failed">Failed</option>
        <option value="Finished">Finished</option>
        <option value="Preparing">Preparing</option>
        <option value="Running">Running</option>
        <option value="Scoring">Scoring</option>
        <option value="Submitted">Submitted</option>
        <option value="Submitting">Submitting</option>
    </select>
    <table class="ui celled selectable inverted table">
        <thead>
        <tr>
            <th>#</th>
            <th>File name</th>
            <th show="{ opts.admin }">Owner</th>
            <th show="{ opts.admin }">Phase</th>
            <th class="right aligned" width="50px">Status</th>
            <th class="center aligned" show="{ opts.admin }">Actions</th>
            <!-- TODO: Figure out security 'risk' of "show" since it is simply set to style="display: none;" -->
            <th class="right aligned" width="50px">Leaderboard?</th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ submission in submissions }" onclick="{ show_modal.bind(this, submission) }" class="clickable">
            <td>1</td> <!-- TODO how is this number supposed to increment? -->
            <td>{ submission.filename }</td>
            <td show="{ opts.admin }">{ submission.owner }</td>
            <td show="{ opts.admin }">{ submission.phase.name }</td>
            <td class="right aligned">{ submission.status }</td>
            <td show="{ opts.admin }" class="center aligned" style="width: 150px">
                <button class="mini ui button inverted basic blue icon"
                        onclick="{ rerun_submission.bind(this, submission) }">
                    <i class="icon redo"></i>
                    <!-- rerun submission -->
                </button>
                <button class="mini ui button inverted basic yellow icon"
                        onclick="{ cancel_submission.bind(this, submission) }">
                    <i class="x icon"></i>
                    <!-- cancel submission -->
                </button>
                <button class="mini ui button inverted basic red icon"
                        onclick="{ delete_submission.bind(this, submission) }">
                    <i class="icon trash alternate"></i>
                    <!-- delete submission -->
                </button>
            </td>
            <td class="center aligned">
                <i class="add_to_leaderboard check square large icon { disabled: !submission.leaderboard }" onclick="{ add_to_leaderboard }"></i>
            </td>
        </tr>
        </tbody>
    </table>

    <div class="ui small modal" ref="modal">
        <submission-modal></submission-modal>
    </div>
    <script>
        var self = this

        self.selected_phase = undefined


        self.on("mount", function () {
            $('.ui .dropdown').dropdown();
            // Get the actual data
            //self.update_submissions()
        })

        self.update_submissions = function (filters) {
            if (opts.admin) {
                filters = filters || {phase__competition: opts.competition.id }
            } else {
                filters = filters || {phase: self.selected_phase.id}
            }
            filters = filters || {phase: self.selected_phase.id}
            CODALAB.api.get_submissions(filters)
                .done(function (data) {
                    // TODO: should be able to do this with a serializer?
                    if (opts.admin) {
                        self.submissions = data.map((item) => {
                            item.phase = opts.competition.phases.filter((phase) => {
                                return phase.id === item.phase
                            })[0]
                            return item
                        })
                    } else {
                        self.submissions = data
                    }
                    self.update({csv_link: this.url.replace('/api/submissions/?', '/api/submissions/?format=csv&')})
                })
                .fail(function (response) {
                    toastr.error("Error retrieving submissions")
                })
        }

        self.add_to_leaderboard = function() {
            console.log(this.submission)
            CODALAB.api.add_submission_to_leaderboard(this.submission.id)
                .done(function (data) {
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
        }

        self.filter = function () {
            var filters = {}
            var search = self.refs.search.value
            if (search.length >= 3 || search === '') {
                filters['search'] = search
            }
            var status = self.refs.status.value
            if (status && status !== ' ') {
                filters['status'] = status
            }
            if (!opts.admin) {
                filters['phase'] = self.selected_phase.id
            } else {
                var phase = self.refs.phase.value
                if (phase && phase !== ' ') {
                    filters['phase'] = phase
                } else {
                    filters['phase__competition'] = opts.competition.id
                }
            }
            self.update_submissions(filters)
        }

        self.download_csv = function () {

        }

        self.rerun_submission = function (submission) {
            CODALAB.api.re_run_submission(submission.id)
                .done(function (respose) {
                    toastr.success('Submission queued')
                    self.update_submissions()
                })
        }

        self.cancel_submission = function (submission) {
            CODALAB.api.cancel_submission(submission.id)
                .done(function (response) {
                    toastr.success('Submission cancelled')
                    self.update_submissions()
                })
        }

        self.delete_submission = function (submission) {
            if (confirm(`Are you sure you want to delete submission: ${submission.filename}?`)) {
                CODALAB.api.delete_submission(submission.id)
                    .done(function (response) {
                        toastr.success('Submission deleted')
                        self.update_submissions()
                    })
            }
        }

        self.show_modal = function (submission) {
            CODALAB.events.trigger('submission_clicked', submission)
            $(self.refs.modal).modal('show');
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
        .hidden
            display: none !important

        .clickable
            &:hover
                cursor: pointer
    </style>
</submission-manager>
