<submission-manager>
    <h1>Submission manager</h1>
    <div if="{ opts.admin }" class="admin-buttons">
        <a class="ui green button" href="{csv_link}">
            <i class="icon download"></i>Download as CSV
        </a>
        <div class="ui dropdown blue button" ref="rerun_button">
            <i class="icon redo"></i>
            <div class="text">Rerun all submissions per phase</div>
            <div class="menu">
                <div class="header">Select a phase</div>
                <div class="item" each="{phase in opts.competition.phases}" onclick="{rerun_phase.bind(this, phase)}">{ phase.name }</div>
            </div>
        </div>
    </div>
    <div class="ui icon input">
        <input type="text" placeholder="Search..." ref="search" onkeyup="{ filter }">
        <i class="search icon"></i>
    </div>
    <select if="{opts.admin}" class="ui dropdown" ref="phase" onchange="{ filter }">
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
    <table class="ui celled selectable table">
        <thead>
        <tr>
            <th class="index-column">#</th>
            <th>File name</th>
            <th if="{ opts.admin }">Owner</th>
            <th if="{ opts.admin }">Phase</th>
            <th class="right aligned status-column">Status</th>
            <th class="center aligned {admin-action-column: opts.admin, action-column: !opts.admin}">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ submission, index in submissions }" onclick="{ show_modal.bind(this, submission) }" class="submission_row">
            <td>{ index + 1 }</td>
            <td>{ submission.filename }</td>
            <td if="{ opts.admin }">{ submission.owner }</td>
            <td if="{ opts.admin }">{ submission.phase.name }</td>
            <td class="right aligned">{ submission.status }</td>
            <td class="center aligned">
                <virtual if="{ opts.admin }">
                    <button class="mini ui button basic blue icon"
                            data-tooltip="Rerun Submission"
                            data-inverted=""
                            onclick="{ rerun_submission.bind(this, submission) }">
                        <i class="icon redo"></i>
                        <!-- rerun submission -->
                    </button>
                    <button class="mini ui button basic yellow icon"
                            data-tooltip="Cancel Submission"
                            data-inverted=""
                            onclick="{ cancel_submission.bind(this, submission) }">
                        <i class="x icon"></i>
                        <!-- cancel submission -->
                    </button>
                    <button class="mini ui button basic red icon"
                            data-tooltip="Delete Submission"
                            data-inverted=""
                            onclick="{ delete_submission.bind(this, submission) }">
                        <i class="icon trash alternate"></i>
                        <!-- delete submission -->
                    </button>
                </virtual>
                <button if="{!submission.leaderboard}"
                        class="mini ui button basic green icon"
                        data-tooltip="Add to Leaderboard"
                        data-inverted=""
                        onclick="{ add_to_leaderboard.bind(this, submission) }">
                    <i class="icon share"></i>
                    <!-- send submission to leaderboard-->
                </button>
                <div if="{!!submission.leaderboard}"
                     class="mini ui green button icon on-leaderboard"
                     data-tooltip="On the Leaderboard"
                     data-inverted=""
                     onclick="{do_nothing}">
                    <i class="icon check"></i>
                </div>
            </td>
        </tr>
        </tbody>
    </table>

    <div class="ui large modal" ref="modal">
        <div class="content">
            <submission-modal></submission-modal>
        </div>
    </div>
    <script>
        var self = this

        self.selected_phase = undefined


        self.on("mount", function () {
            $(self.refs.search).dropdown();
            $(self.refs.status).dropdown();
            $(self.refs.phase).dropdown();
            $(self.refs.rerun_button).dropdown();
        })

        self.do_nothing = event => {
            event.stopPropagation()
        }

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
                    self.update({csv_link: CODALAB.api.get_submission_csv_URL(filters)})
                })
                .fail(function (response) {
                    toastr.error("Error retrieving submissions")
                })
        }

        self.add_to_leaderboard = function(submission) {
            CODALAB.api.add_submission_to_leaderboard(submission.id)
                .done(function (data) {
                    self.update_submissions()
                })
                .fail(function (response) {
                    toastr.error("Could not find competition")
                })
            event.stopPropagation()
        }
        self.rerun_phase = function (phase) {
            CODALAB.api.re_run_phase_submissions(phase.id)
                .done(function (response) {
                    toastr.success(`Rerunning ${response.count} submissions`)
                    self.update_submissions()
                })
        }
        self.filter = function () {
            delay(() => {
                var filters = {}
                var search = self.refs.search.value
                if (search) {
                    filters['search'] = search
                }
                var status = self.refs.status.value
                if (status !== ' ') {
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
            }, 100)
        }

        self.rerun_submission = function (submission) {
            CODALAB.api.re_run_submission(submission.id)
                .done(function (response) {
                    toastr.success('Submission queued')
                    self.update_submissions()
                })
            event.stopPropagation()
        }

        self.cancel_submission = function (submission) {
            CODALAB.api.cancel_submission(submission.id)
                .done(function (response) {
                    if (response.canceled === true) {
                        toastr.success('Submission cancelled')
                        self.update_submissions()
                    } else {
                        toastr.error('Could not cancel submission')
                    }
                })
            event.stopPropagation()
        }

        self.delete_submission = function (submission) {
            if (confirm(`Are you sure you want to delete submission: ${submission.filename}?`)) {
                CODALAB.api.delete_submission(submission.id)
                    .done(function (response) {
                        toastr.success('Submission deleted')
                        self.update_submissions()
                    })
            }
            event.stopPropagation()
        }

        self.show_modal = function (submission) {
            if (opts.admin) {
                submission.admin = true
            }
            CODALAB.events.trigger('submission_clicked', submission)
            $(self.refs.modal).modal('show');
        }

        CODALAB.events.on('phase_selected', function(selected_phase) {
            self.selected_phase = selected_phase
            self.update_submissions()
        })

        CODALAB.events.on('new_submission_created', function(new_submission_data) {
            self.submissions.unshift(new_submission_data)
            self.update()
        })

        CODALAB.events.on('score_updated', () => {
            $(self.refs.modal).modal('hide')
            self.update_submissions()
        })
    </script>

    <style type="text/stylus">
        //:scope
        //    height 100%
        .admin-buttons
            padding-bottom: 20px;

        .on-leaderboard
            &:hover
                cursor auto
                background-color #21ba45 !important

        .admin-action-column
            width 200px

        .action-column
            width 100px

        .status-column
            width 50px

        .index-column
            width: 40px

        .submission_row
            &:hover
                cursor: pointer
            height: 52px
    </style>
</submission-manager>
