<submission-manager class="submission-manager">
    <div if="{ opts.admin }" class="admin-buttons">
        <a class="ui green button" href="{csv_link}">
            <i class="icon download"></i>Download as CSV
        </a>
        <div class="ui dropdown blue button" ref="rerun_button">
            <i class="icon redo"></i>
            <div class="text">Rerun all submissions per phase</div>
            <div class="menu">
                <div class="header">Select a phase</div>
                <div class="parent-modal item" each="{phase in opts.competition.phases}"
                     onclick="{rerun_phase.bind(this, phase)}">{ phase.name }
                </div>
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
            <th class="collapsing">ID #</th>
            <th>File name</th>
            <th if="{ opts.admin }">Owner</th>
            <th if="{ opts.admin }">Phase</th>
            <th class="right aligned status-column">Status</th>
            <th class="center aligned {admin-action-column: opts.admin, action-column: !opts.admin}">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr if="{ _.isEmpty(submissions) && !loading }" class="center aligned">
            <td colspan="100%"><em>No submissions found! Please make a submission</em></td>
        </tr>
        <tr if="{loading}" class="center aligned">
            <td colspan="100%">
                <em>Loading Submissions...</em>
            </td>
        </tr>
        <tr show="{!loading}" each="{ submission, index in filter_children(submissions) }"
            onclick="{ submission_clicked.bind(this, submission) }" class="submission_row">
            <td>{ submission.id }</td>
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
                    <button class="mini ui button basic red icon"
                            data-tooltip="Delete Submission"
                            data-inverted=""
                            onclick="{ delete_submission.bind(this, submission) }">
                        <i class="icon trash alternate"></i>
                        <!-- delete submission -->
                    </button>
                </virtual>
                <span if="{!_.includes(['Finished', 'Cancelled', 'Unknown', 'Failed'], submission.status)}"
                        data-tooltip="Cancel Submission"
                        data-inverted=""
                        onclick="{ cancel_submission.bind(this, submission) }">
                    <i class="grey minus circle icon"></i>
                    <!-- cancel submission -->
                </span>
                <span if="{!submission.leaderboard && submission.status === 'Finished'}"
                        data-tooltip="Add to Leaderboard"
                        data-inverted=""
                        onclick="{ add_to_leaderboard.bind(this, submission) }">
                    <i class="icon green columns"></i>
                    <!-- send submission to leaderboard-->
                </span>
                <span if="{!!submission.leaderboard}"
                     data-tooltip="On the Leaderboard"
                     data-inverted=""
                     onclick="{do_nothing}">
                    <i class="icon green check"></i>
                </span>
                <span if="{!submission.is_public && submission.status === 'Finished'}"
                      data-tooltip="Make Public"
                      data-inverted=""
                      onclick="{toggle_submission_is_public.bind(this, submission)}">
                    <i class="icon share teal alternate"></i>
                </span>
                <span if="{!!submission.is_public && submission.status === 'Finished'}"
                      data-tooltip="Make Private"
                      data-inverted=""
                      onclick="{toggle_submission_is_public.bind(this, submission)}">
                    <i class="icon share grey alternate"></i>
                </span>
            </td>
        </tr>
        </tbody>
    </table>

    <div class="ui large modal" ref="modal">
        <div class="content">
            <div if="{!!selected_submission && !_.get(selected_submission, 'has_children', false)}">
                <submission-modal hide_output="{selected_phase.hide_output}" submission="{selected_submission}"></submission-modal>
            </div>
            <div if="{!!selected_submission && _.get(selected_submission, 'has_children', false)}">
                <div class="ui large green pointing menu">
                    <div each="{child, i in _.get(selected_submission, 'children')}"
                         class="parent-modal item"
                         data-tab="{admin_: is_admin()}child_{i}">
                        Task {i + 1}
                    </div>
                    <div if="{is_admin()}" data-tab="admin" class="parent-modal item">Admin</div>
                </div>
                <div each="{child, i in _.get(selected_submission, 'children')}"
                     class="ui tab"
                     data-tab="{admin_: is_admin()}child_{i}">
                    <submission-modal hide_output="{selected_phase.hide_output}" submission="{child}"></submission-modal>
                </div>
                <div class="ui tab" style="height: 565px; overflow: auto;" data-tab="admin" if="{is_admin()}">
                    <submission-scores leaderboards="{leaderboards}"></submission-scores>
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this

        self.selected_phase = undefined
        self.selected_submission = undefined
        self.hide_output = false
        self.leaderboards = {}
        self.loading = true

        self.on("mount", function () {
            $(self.refs.search).dropdown();
            $(self.refs.status).dropdown();
            $(self.refs.phase).dropdown();
            $(self.refs.rerun_button).dropdown();
        })

        self.is_admin = () => {
            return _.get(self.selected_submission, 'admin', false)
        }

        self.do_nothing = event => {
            event.stopPropagation()
        }

        self.is_admin = () => {
            return _.get(self.selected_submission, 'admin', false)
        }

        self.filter_children = submissions => {
            return _.filter(submissions, sub => !sub.parent)
        }

        self.update_submissions = function (filters) {
            self.loading = true
            self.update()
            if (opts.admin) {
                filters = filters || {phase__competition: opts.competition.id}
            } else {
                filters = filters || {phase: self.selected_phase.id}
            }
            filters = filters || {phase: self.selected_phase.id}
            CODALAB.api.get_submissions(filters)
                .done(function (submissions) {
                    // TODO: should be able to do this with a serializer?
                    if (opts.admin) {
                        self.submissions = submissions.map((item) => {
                            item.phase = opts.competition.phases.filter((phase) => {
                                return phase.id === item.phase
                            })[0]
                            return item
                        })
                    } else {
                        self.submissions = _.filter(submissions, sub => sub.owner === CODALAB.state.user.username)
                    }
                    if (!opts.admin) {
                        CODALAB.events.trigger('submissions_loaded', self.submissions)
                    }
                    self.csv_link = CODALAB.api.get_submission_csv_URL(filters)
                    self.update()

                    // Timeout here so loader doesn't flicker
                    _.delay(() => {
                        self.loading = false
                        self.update()
                    }, 300)
                })
                .fail(function (response) {
                    toastr.error("Error retrieving submissions")
                })
        }

        self.add_to_leaderboard = function (submission) {
            CODALAB.api.add_submission_to_leaderboard(submission.id)
                .done(function (data) {
                    self.update_submissions()
                    CODALAB.events.trigger('submission_added_to_leaderboard')
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

        self.get_score_details = function (submission, column) {
            try {
                let score = _.filter(submission.scores, (score) => {
                    return score.column_key === column.key
                })[0]
                return [score.score, score.id]
            } catch {
                return ['', '']
            }
        }

        self.toggle_submission_is_public = function (submission) {
            event.stopPropagation()
            let message = submission.is_public
                ? 'Are you sure you want to make this submission private? It will no longer be visible to other users.'
                : 'Are you sure you want to make this submission public? It will become visible to everyone'
            if (confirm(message)) {
                CODALAB.api.toggle_submission_is_public(submission.id)
                    .done(data => {
                        toastr.success('Submission updated')
                        self.update_submissions()
                    })
                    .fail(resp => {
                        toastr.error('Error updating submission')
                    })
            }
        }


        self.submission_clicked = function (submission) {
            // stupid workaround to not modify the original submission object
            submission = _.defaultsDeep({}, submission)
            if (submission.has_children) {
                submission.children = _.map(submission.children, child => {
                    return {id: child}
                })
                CODALAB.api.get_submission_details(submission.id)
                    .done(function (data) {
                        self.leaderboards = data.leaderboards
                        _.forEach(self.leaderboards, (leaderboard) => {
                            _.map(leaderboard.columns, column => {
                                let [score, score_id] = self.get_score_details(submission, column)
                                column.score = score
                                column.score_id = score_id
                                return column
                            })
                        })
                        self.update()
                    })
            }
            if (opts.admin) {
                submission.admin = true
            }
            self.selected_submission = submission
            self.update()
            $(self.refs.modal)
                .modal({
                    onShow: () => {
                        if (_.get(self.selected_submission, 'has_children', false)) {
                            // only try and tabulate the parent modal if children exist
                            let path = self.is_admin() ? 'admin_child_0' : 'child_0'
                            $('.menu .parent-modal.item')
                                .tab('change tab', path)
                        }
                    }
                })
                .modal('show')
            CODALAB.events.trigger('submission_clicked')
        }

        CODALAB.events.on('phase_selected', function (selected_phase) {
            self.selected_phase = selected_phase
            self.selected_phase.hide_output = selected_phase.hide_output && !CODALAB.state.user.has_competition_admin_privileges(self.opts.competition)
            self.update_submissions()
        })

        CODALAB.events.on('new_submission_created', function (new_submission_data) {
            self.submissions.unshift(new_submission_data)
            self.update()
        })

        CODALAB.events.on('score_updated', () => {
            $(self.refs.modal).modal('hide')
            self.update_submissions()
        })

        CODALAB.events.on('submission_status_update', data => {
            let sub = _.find(self.submissions, submission => submission.id === data.submission_id)
            if (sub) {
                sub.status = data.status
            }
            self.update()
        })
    </script>

    <style type="text/stylus">
        :scope
            margin 2em 0

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

        .submission_row
            &:hover
                cursor: pointer
            height: 52px

        table tbody .center.aligned td
            color #8c8c8c
    </style>
</submission-manager>
