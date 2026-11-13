<submission-manager class="submission-manager">
    <div if="{ opts.admin }" class="admin-buttons" style="display: flex; align-items: center; gap: 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="ui dropdown button" ref="rerun_button">
            <i class="icon history"></i>
            <div class="text">Rerun all submissions per phase</div>
            <div class="menu">
                <div class="header">Select a phase</div>
                <div class="parent-modal item" each="{phase in opts.competition.phases}" onclick="{rerun_phase.bind(this, phase)}">
                { phase.name }
                </div>
            </div>
            </div>

            <a class="ui button" href="{csv_link}">
            <i class="icon download"></i>Download as CSV
            </a>

            <select class="ui dropdown" ref="submission_handling_operation" onchange="{ on_operation_changed }">
                <option value="download_submissions">Download selected submissions</option>
                <option value="download_prediction_results">Download prediction results of selected submissions</option>
                <option value="download_scoring_results">Download scoring results of selected submissions</option>
                <option value="delete">Delete selected submissions</option>
                <option value="rerun">Rerun selected submissions</option>
                <option value="resubmit">Resubmit selected submissions on current tasks</option>
                    <option value="migrate">Migrate selected submissions</option>
                </select>

                <select if="{ selected_operation === 'migrate' }" class="ui dropdown" ref="migrate_target_phase">
                    <option value="">Destination phase…</option>
                    <option each="{ phase in opts.competition.phases }" value="{ phase.id }">{ phase.name }</option>
            </select>

            <button type="button" class="ui button" disabled="{checked_submissions.length === 0}" onclick="{submission_handling.bind(this)}">
            Apply
            </button>
        </div>
        <div id="downloadStatus" style="display:none; display: flex; flex-direction: column; align-items: flex-start;">
            <progress id="downloadProgress" value="0" max="100"  style="display:none; width: 150px;"></progress>
            <div id="progressText" style="margin-top: 4px;"></div>
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

    <button type="button" class="ui icon button" data-tooltip="Refresh" data-inverted="" onclick="{ refresh_now }">
        <i class="sync icon"></i>
    </button>

    <div class="ui input" if="{opts.admin}">
        <input 
        type="checkbox" 
        checked="{show_is_soft_deleted}"
        onclick="{toggleShowSoftDeleted}">
        <label class="checkbox-label">Show soft-deleted submissions</label>
    </div>
    <table class="ui celled selectable table" ref="submission_table">
        <thead>
            <tr>
                <th if="{opts.admin}">
                    <div class="ui checkbox" onclick="{select_all_pressed.bind(this)}">
                        <input type="checkbox" name="select_all">
                        <label>All</label>
                    </div>
                </th>
                <th class="collapsing" style="cursor:pointer;" onclick="{ sort_by.bind(this, 'id') }">
                    ID # <i if="{ sort_column === 'id' }" class="icon { sort_direction === 'asc' ? 'caret up' : 'caret down' }"></i>
                </th>
                <th style="cursor:pointer;" onclick="{ sort_by.bind(this, 'filename') }">
                    File name <i if="{ sort_column === 'filename' }" class="icon { sort_direction === 'asc' ? 'caret up' : 'caret down' }"></i>
                </th>
                <th if="{ opts.admin }" style="cursor:pointer;" onclick="{ sort_by.bind(this, 'owner') }">
                    Owner <i if="{ sort_column === 'owner' }" class="icon { sort_direction === 'asc' ? 'caret up' : 'caret down' }"></i>
                </th>
                <th if="{ opts.admin }" style="cursor:pointer;" onclick="{ sort_by.bind(this, 'phase') }">
                    Phase <i if="{ sort_column === 'phase' }" class="icon { sort_direction === 'asc' ? 'caret up' : 'caret down' }"></i>
                </th>
                <th style="cursor:pointer;" onclick="{ sort_by.bind(this, 'created_when') }">
                    Date <i if="{ sort_column === 'created_when' }" class="icon { sort_direction === 'asc' ? 'caret up' : 'caret down' }"></i>
                </th>
                <th style="cursor:pointer;" onclick="{ sort_by.bind(this, 'status') }">
                    Status <i if="{ sort_column === 'status' }" class="icon { sort_direction === 'asc' ? 'caret up' : 'caret down' }"></i>
                </th>
                <th style="cursor:pointer;" onclick="{ sort_by.bind(this, 'score') }">
                    Score <i if="{ sort_column === 'score' }" class="icon { sort_direction === 'asc' ? 'caret up' : 'caret down' }"></i>
                </th>
                <th if="{ has_hidden_scores() }" data-tooltip="Hidden leaderboard columns, only competition admins see them" data-inverted="">
                    Hidden scores <i class="eye slash outline icon"></i>
                </th>
                <th if="{ opts.competition.enable_detailed_results && opts.competition.show_detailed_results_in_submission_panel}">
                    Detailed Results
                </th>
                <th class="center aligned">Actions</th>
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
        </tbody>

        <tbody each="{ submission, index in sorted_parents(submissions) }">
            <tr show="{!loading}"
                onclick="{ submission_clicked.bind(this, submission) }" class="submission_row {submission.is_soft_deleted ? 'soft-deleted' : ''}">
                <td if="{ opts.admin }">
                    <div if="{ !submission.is_soft_deleted }" class="ui checkbox" onclick="{on_submission_checked.bind(this)}">
                        <input type="checkbox" name="{submission.id}">
                        <label></label>
                    </div>
                </td>
                
                <td>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="display:inline-flex; width:16px; justify-content:center; flex-shrink:0;">
                            <span if="{ submission.has_children }"
                                data-tooltip="{ expanded_submissions[submission.id] ? 'Hide child submissions' : 'Show child submissions' }"
                                data-inverted=""
                                onclick="{ toggle_expand.bind(this, submission) }"
                                style="cursor:pointer;">
                                <i class="icon { expanded_submissions[submission.id] ? 'caret down' : 'caret right' }" style="margin:0;"></i>
                            </span>
                        </span>
                        <span>{ submission.id }</span>
                    </div>
                </td>

                <td>{ submission.filename }</td>
                <td if="{ opts.admin }">{ submission.owner }</td>
                <td if="{ opts.admin }">{ submission.phase.name }</td>
                <td>{ pretty_date(submission.created_when) }</td>
                <td class="right aligned collapsing">
                    { display_status(submission) }
                    <sup if="{ status_mismatch(submission) }" data-tooltip="{ mismatch_message(submission) }" data-inverted="">
                        <i class="orange exclamation triangle icon"></i>
                    </sup>
                    <sup data-tooltip="{submission.status_details}">
                        <i if="{submission.status === 'Failed' && !is_hitl_failure(submission)}" class="failed question circle icon"></i>
                        <i if="{submission.status === 'Failed' && is_hitl_failure(submission)}" class="orange lock icon"></i>
                    </sup>
                    <sup if="{ pending_info(submission) }" data-tooltip="{ pending_info(submission).message }" data-inverted="">
                        <i class="question circle icon" style="color: { pending_info(submission).color };"></i>
                    </sup>
                </td>
                <td>{get_score(submission)}</td>
                <td if="{ has_hidden_scores() }">
                    <div each="{ score in get_hidden_scores(submission) }">{ score.column_key }: { format_score(score) }</div>
                </td>
                <td
                    if="{ opts.competition.enable_detailed_results && opts.competition.show_detailed_results_in_submission_panel }">
                    <a if="{submission.status === 'Finished'}" href="detailed_results/{submission.id}" target="_blank"
                        class="eye-icon-link">
                        <i class="icon grey eye eye-icon"></i>
                    </a>
                </td>
                <!--  Show Action buttons when submission is not soft deleted  -->
                <!--  For soft-deleted submissions, organizers can still hard-delete  -->
                <td if="{ submission.is_soft_deleted }">
                    <virtual if="{ opts.admin }">
                        <span data-tooltip="Delete Submission" data-inverted=""
                            onclick="{ delete_submission.bind(this, submission) }">
                            <i class="icon red trash alternate"></i>
                        </span>
                    </virtual>
                </td>
                <td class="center aligned" if="{ !submission.is_soft_deleted }">
                    <virtual if="{ opts.admin}">
                        <!-- run/rerun submission IDEMPOTENT -->
                        <!--  run: status = submitting auto_run = false  -->
                        <!--  rerun: else   -->
                        <span if="{ is_manual_run(submission) }"
                            data-tooltip="{ submission.has_children ? 'Run all remaining children' : 'Run Submission' }"
                            data-inverted=""
                            onclick="{ run_submission.bind(this, submission) }">
                            <i class="icon green play"></i>
                        </span>
                        <span if="{ _.includes(['Finished', 'Failed', 'Cancelled'], submission.status) }"
                            data-tooltip="Rerun Submission (does not create a new one)" data-inverted=""
                            onclick="{ rerun_submission.bind(this, submission) }">
                            <i class="icon purple history"></i>
                        </span>
                        <!-- resubmit on current tasks (re-run keeps the original task) -->
                        <span if="{ _.includes(['Finished', 'Failed', 'Cancelled'], submission.status) }"
                            data-tooltip="Resubmit (new submission on current tasks)" data-inverted=""
                            onclick="{ resubmit_submission.bind(this, submission) }">
                            <i class="icon blue redo { disabled: resubmitting }"></i>
                        </span>
                        <!-- delete submission -->
                        <span data-tooltip="Delete Submission" data-inverted=""
                            onclick="{ delete_submission.bind(this, submission) }">
                            <i class="icon red trash alternate"></i>
                        </span>
                    </virtual>
                    <!-- cancel submission -->
                    <span if="{!_.includes(['Finished', 'Cancelled', 'Unknown', 'Failed'], submission.status)}"
                        data-tooltip="Cancel Submission" data-inverted=""
                        onclick="{ cancel_submission.bind(this, submission) }">
                        <i class="grey minus circle icon"></i>
                    </span>
                    <!-- send submission to leaderboard-->
                    <span if="{!submission.on_leaderboard && submission.status === 'Finished'}"
                        data-tooltip="Add to Leaderboard" data-inverted=""
                        onclick="{ add_to_leaderboard.bind(this, submission) }">
                        <i class="icon green columns"></i>
                    </span>
                    <!--  On leaderboard  -->
                    <span if="{ submission.on_leaderboard }" data-tooltip="On the Leaderboard" data-inverted=""
                        onclick="{ remove_from_leaderboard.bind(this, submission) }">
                        <i class="icon green check"></i>
                    </span>
                    <!--  Make Public  -->
                    <span
                        if="{!submission.is_public && submission.status === 'Finished' && submission.can_make_submissions_public}"
                        data-tooltip="Make Public" data-inverted=""
                        onclick="{toggle_submission_is_public.bind(this, submission)}">
                        <i class="icon share teal alternate"></i>
                    </span>
                    <!--  Make Private  -->
                    <span
                        if="{!!submission.is_public && submission.status === 'Finished' && submission.can_make_submissions_public}"
                        data-tooltip="Make Private" data-inverted=""
                        onclick="{toggle_submission_is_public.bind(this, submission)}">
                        <i class="icon share grey alternate"></i>
                    </span>
                    <!-- Delete Submission -->
                    <!--  Show only if submission is Finished/Failed/Cancelled and not admin interface  -->
                    <!--  This condition && !opts.admin is there to not show soft delete button in the admin interface  -->
                    <span if="{ ((submission.status === 'Finished' && !submission.on_leaderboard) || submission.status === 'Failed' || submission.status === 'Cancelled')  && !opts.admin}"
                        data-tooltip="Delete Submission" data-inverted=""
                        onclick="{ soft_delete_submission.bind(this, submission) }">
                        <i class="icon red trash"></i>
                    </span>
                    <!-- Atomic Migration -->
                    <span if="{ can_migrate(submission) }" class="migrate-wrapper" onclick="{ do_nothing }">
                        <span data-tooltip="Migrate to another phase" data-inverted=""
                            style="cursor:pointer;"
                            onclick="{ toggle_migrate_menu.bind(this, submission) }">
                            <i class="icon blue copy outline"></i>
                        </span>
                        <div if="{ migrate_menu_open === submission.id }" class="migrate-menu">
                            <div class="migrate-header">
                                Migrate submission #{ submission.id } to…
                            </div>
                            <div each="{ phase in get_future_phases(submission) }"
                                class="migrate-item { disabled: migrating }"
                                onclick="{ migrate_submission.bind(this, submission, phase) }">
                                <div class="migrate-item-title">
                                    <span>{ phase.name }</span>
                                    <i class="angle right icon"></i>
                                </div>
                                <small class="migrate-item-meta">
                                    { phase.status || 'Upcoming' } · starts { pretty_date(phase.start) }
                                </small>
                            </div>
                        </div>
                    </span>
                </td>
            </tr>

            <tr if="{ submission.has_children && expanded_submissions[submission.id] }" class="child-submissions-row">
                <td colspan="100%" style="padding: 0 0 0 40px; background:#fafafa;">
                    <table class="ui very compact celled table">
                        <thead>
                            <tr>
                                <th>ID #</th>
                                <th if="{ opts.admin }">Owner</th>
                                <th if="{ opts.admin }">Phase</th>
                                <th if="{ has_multiple_tasks(submission) }">Task</th>
                                <th>Group</th>
                                <th>Date</th>
                                <th>Status</th>
                                <th>Score</th>
                                <th if="{ has_hidden_scores() }">Hidden scores</th>
                                <th class="center aligned">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ child in get_children(submission) }" onclick="{ submission_clicked.bind(this, child) }" class="submission_row">
                                <td>{ child.id }</td>
                                <td if="{ opts.admin }">{ child.owner }</td>
                                <td if="{ opts.admin }">{ child.phase ? child.phase.name : '' }</td>
                                <td if="{ has_multiple_tasks(submission) }">{ child.task ? child.task.name : '' }</td>
                                <td>{ child.participant_group_name || '-' }</td>
                                <td>{ pretty_date(child.created_when) }</td>
                                <td class="right aligned collapsing">
                                    { child.status }
                                    <sup if="{ pending_info(child) }" data-tooltip="{ pending_info(child).message }" data-inverted="">
                                        <i class="question circle icon" style="color: { pending_info(child).color };"></i>
                                    </sup>
                                </td>
                                <td>{ get_score(child) }</td>
                                <td if="{ has_hidden_scores() }">
                                    <div each="{ score in get_hidden_scores(child) }">{ score.column_key }: { format_score(score) }</div>
                                </td>

                                <td if="{ child.is_soft_deleted }">
                                    <virtual if="{ opts.admin }">
                                        <span data-tooltip="Delete Submission" data-inverted=""
                                            onclick="{ delete_submission.bind(this, child) }">
                                            <i class="icon red trash alternate"></i>
                                        </span>
                                    </virtual>
                                </td>
                                <td class="center aligned" if="{ !child.is_soft_deleted }">
                                    <virtual if="{ opts.admin}">
                                        <span if="{ child.status === 'Submitting' && !child.auto_run }"
                                            data-tooltip="Run this task" data-inverted=""
                                            onclick="{ run_submission.bind(this, child) }">
                                            <i class="icon green play"></i>
                                        </span>
                                        <span if="{ _.includes(['Finished', 'Failed', 'Cancelled'], child.status) }"
                                            data-tooltip="Rerun Submission (does not create a new one)" data-inverted=""
                                            onclick="{ rerun_submission.bind(this, child) }">
                                            <i class="icon purple history"></i>
                                        </span>
                                        <span data-tooltip="Delete Submission" data-inverted=""
                                            onclick="{ delete_submission.bind(this, child) }">
                                            <i class="icon red trash alternate"></i>
                                        </span>
                                    </virtual>
                                    <span if="{!_.includes(['Finished', 'Cancelled', 'Unknown', 'Failed'], child.status)}"
                                        data-tooltip="Cancel Submission" data-inverted=""
                                        onclick="{ cancel_submission.bind(this, child) }">
                                        <i class="grey minus circle icon"></i>
                                    </span>
                                    <span if="{!child.on_leaderboard && child.status === 'Finished'}"
                                        data-tooltip="Add to Leaderboard" data-inverted=""
                                        onclick="{ add_to_leaderboard.bind(this, child) }">
                                        <i class="icon green columns"></i>
                                    </span>
                                    <span if="{ child.on_leaderboard }" data-tooltip="On the Leaderboard" data-inverted=""
                                        onclick="{ remove_from_leaderboard.bind(this, child) }">
                                        <i class="icon green check"></i>
                                    </span>
                                    <span
                                        if="{!child.is_public && child.status === 'Finished' && child.can_make_submissions_public}"
                                        data-tooltip="Make Public" data-inverted=""
                                        onclick="{toggle_submission_is_public.bind(this, child)}">
                                        <i class="icon share teal alternate"></i>
                                    </span>
                                    <span
                                        if="{!!child.is_public && child.status === 'Finished' && child.can_make_submissions_public}"
                                        data-tooltip="Make Private" data-inverted=""
                                        onclick="{toggle_submission_is_public.bind(this, child)}">
                                        <i class="icon share grey alternate"></i>
                                    </span>
                                    <span if="{ ((child.status === 'Finished' && !child.on_leaderboard) || child.status === 'Failed' || child.status === 'Cancelled')  && !opts.admin}"
                                        data-tooltip="Delete Submission" data-inverted=""
                                        onclick="{ soft_delete_submission.bind(this, child) }">
                                        <i class="icon red trash"></i>
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>

    <div class="ui pagination menu" style="display:flex; align-items:center; justify-content:space-between; margin-top: 12px;">
        <div style="display:flex; align-items:center; gap:8px;">
            <button class="ui button" onclick="{ go_to_page.bind(this, page - 1) }" disabled="{ page <= 1 }">
                <i class="icon chevron left"></i> Previous
            </button>

            <div style="display:flex; align-items:center; gap:6px;">
                <span>Page</span>
                <input type="number" min="1" value="{ page }" onkeydown="{ handle_page_enter }" style="width:70px; text-align:center;" />
                <span> / { total_pages || 1 }</span>
            </div>

            <button class="ui button" onclick="{ go_to_page.bind(this, page + 1) }" disabled="{ !next }">
                Next <i class="icon chevron right"></i>
            </button>
        </div>

        <div style="display:flex; align-items:center; gap:8px;">
            <label>Per page</label>
            <select class="ui dropdown" value="{ page_size }" onchange="{ change_page_size.bind(this) }">
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="500">500</option>
                <option value="all">1000</option>
            </select>

            <div style="margin-right: 10px; color: #8c8c8c;">
                <small>{ total_count || 0 } total</small>
            </div>
        </div>
    </div>

    <div class="ui large modal" ref="modal">
        <div class="content">
            <div if="{!!selected_submission && !_.get(selected_submission, 'has_children', false)}">
                <submission-modal hide_output="{selected_phase.hide_output}"
                    show_visualization="{opts.competition.enable_detailed_results}"
                    submission="{selected_submission}"></submission-modal>
            </div>
            <div if="{!!selected_submission && _.get(selected_submission, 'has_children', false)}">
                <div class="ui large green pointing menu">
                    <div each="{child, i in _.get(selected_submission, 'children')}" class="parent-modal item"
                        data-tab="{admin_: is_admin()}child_{i}">
                        Task {i + 1}
                    </div>


                    <div class="item" if="{_.get(selected_submission, 'children').length === 0}">
                        <i style="padding: 5px;">ERROR: Submission is a parent, but has no children. There was an error
                            during creation.</i>
                    </div>
                </div>

                <div each="{child, i in _.get(selected_submission, 'children')}" class="ui tab"
                    data-tab="{admin_: is_admin()}child_{i}">
                    <submission-modal hide_output="{selected_phase.hide_output}"
                        show_visualization="{opts.competition.enable_detailed_results}"
                        submission="{child}"></submission-modal>
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
        self.checked_submissions = []
        self.show_is_soft_deleted = false

        self.page = 1
        self.page_size = 50
        self.total_count = 0
        self.total_pages = 1
        self.next = null
        self.previous = null

        self.expanded_submissions = {}
        self.request_id = 0
        self.fetching = false
        self.pending_refresh = null
        self.destroyed = false
        self.burst = 0

        self.TERMINAL = ['Finished', 'Failed', 'Cancelled', 'None', 'Unknown']

        // ---- Status helpers -------------------------------------------------
        self.is_waiting_manual = s => s.status === 'Submitting' && !s.auto_run

        self.display_status = function (submission) {
            if (!submission.has_children) return submission.status
            let kids = _.filter(self.get_children(submission), c => !c.is_soft_deleted)
            if (kids.length === 0) return submission.status
            // Children on another page: we cannot be sure, keep the stored status
            let missing = _.difference(submission.children || [], _.map(kids, 'id'))
            if (missing.length > 0 && self.total_pages > 1) return submission.status

            let statuses = _.map(kids, 'status')
            let done = ['Finished', 'Failed', 'Cancelled']
            if (_.every(statuses, s => _.includes(done, s))) {
                if (_.includes(statuses, 'Finished')) return 'Finished'
                if (_.includes(statuses, 'Failed')) return 'Failed'
                return 'Cancelled'
            }
            if (_.every(statuses, s => s === 'Submitting')) return 'Submitting'
            let active = _.find(['Scoring', 'Running', 'Preparing', 'Submitted'], s => _.includes(statuses, s))
            return active || 'Running'
        }

        self.status_mismatch = function (submission) {
            return !!submission.has_children && self.display_status(submission) !== submission.status
        }

        self.mismatch_message = function (submission) {
            return `Stored status is "${submission.status}" but its child submissions give "${self.display_status(submission)}". ` +
                'The displayed status is recomputed from the children.'
        }

        self.get_submission_phase = function (submission) {
            if (!submission || !submission.phase) return null
            if (_.isObject(submission.phase)) return submission.phase
            return _.find(opts.competition.phases, p => p.id === submission.phase) || null
        }

        self.is_waiting_for_phase = function (submission) {
            if (!submission || submission.status !== 'Submitting') return false
            let phase = self.get_submission_phase(submission)
            if (!phase || !phase.start) return false
            return Date.parse(phase.start) > Date.now()
        }

        self.waiting_message = function (submission) {
            let phase = self.get_submission_phase(submission)
            if (!phase) return ''
            return 'Waiting for phase "' + phase.name + '" to start (' + self.pretty_date(phase.start) +
                '). This submission will run automatically once the phase begins.'
        }

        self.pending_info = function (submission) {
            if (!submission || submission.status !== 'Submitting') return null
            if (self.is_waiting_for_phase(submission)) {
                return { color: 'blue', message: self.waiting_message(submission) }
            }
            if (!submission.auto_run) {
                return { color: 'black', message: 'An organizer will run your submission soon' }
            }
            return null
        }

        // ---- Refresh machinery ----------------------------------------------
        self.needs_polling = function () {
            return _.some(self.submissions, s =>
                !_.includes(self.TERMINAL, s.status) && !self.is_waiting_manual(s))
        }

        self.refresh_soon = function (ticks) {
            if (self.destroyed) return

            self.burst = Math.max(self.burst, ticks || 6)
            self.update_submissions(undefined, true)
        }

        self.refresh_soon_debounced = _.debounce(function () {
            if (!self.destroyed) self.refresh_soon(3)
        }, 800)

        self.refresh_now = function (event) {
            if (event) event.stopPropagation()
            self.refresh_soon()
        }

        self.on_visibility = function () {
            if (self.destroyed || document.hidden) return
            self.update_submissions(undefined, true)
        }

        self.build_filters = function () {
            let filters = {}
            let search = self.refs.search && self.refs.search.value
            if (search) filters.search = search
            let status = self.refs.status && self.refs.status.value
            if (status && status !== ' ') filters.status = status
            if (opts.admin) {
                let phase = self.refs.phase && self.refs.phase.value
                if (phase && phase !== ' ') {
                    filters.phase = phase
                } else {
                    filters.phase__competition = opts.competition.id
                }
                filters.show_is_soft_deleted = self.show_is_soft_deleted
            } else {
                filters.phase = self.selected_phase ? self.selected_phase.id : undefined
            }
            return filters
        }

        self.close_migrate_menu = function () {
            if (self.migrate_menu_open !== null) {
                self.migrate_menu_open = null
                self.update()
            }
        }

        self.on_migrate_keydown = function (e) {
            if (e.key === 'Escape') self.close_migrate_menu()
        }

        self.on("mount", function () {
            $(self.refs.search).dropdown()
            $(self.refs.status).dropdown()
            $(self.refs.phase).dropdown()
            $(self.refs.rerun_button).dropdown()
            $(self.refs.submission_handling_operation).dropdown()
            $(document).on('click.migrate_menu', self.close_migrate_menu)
            $(document).on('keydown.migrate_menu', self.on_migrate_keydown)

            self.poll = setInterval(function () {
                if (document.hidden || self.fetching) return
                if (self.burst > 0 || self.needs_polling()) {
                    if (self.burst > 0) self.burst--
                    self.update_submissions(undefined, true)
                }
            }, 4000)
            document.addEventListener('visibilitychange', self.on_visibility)
        })

        self.on("unmount", function () {
            self.destroyed = true
            self.request_id++
            self.pending_refresh = null

            if (self.refresh_soon_debounced &&
                typeof self.refresh_soon_debounced.cancel === 'function') {
                self.refresh_soon_debounced.cancel()
            }

            $(document).off('click.migrate_menu', self.close_migrate_menu)
            $(document).off('keydown.migrate_menu', self.on_migrate_keydown)

            clearInterval(self.poll)
            document.removeEventListener('visibilitychange', self.on_visibility)

            self.remove_codalab_listeners()
        })

        self.pretty_date = function (date_string) {
            if (!!date_string) {
                return luxon.DateTime.fromISO(date_string).toFormat('yyyy-MM-dd HH:mm')
            } else {
                return ''
            }
        }

        self.is_admin = () => {
            return _.get(self.selected_submission, 'admin', false)
        }

        self.do_nothing = event => {
            event.stopPropagation()
        }

        self.get_children = function (submission) {
            return _.filter(self.submissions, sub => sub.parent === submission.id && (self.show_is_soft_deleted || !sub.is_soft_deleted))
        }

        self.has_multiple_tasks = function (submission) {
            let children = self.get_children(submission)
            let task_ids = _.uniq(_.map(children, child => _.get(child, 'task.id')).filter(id => id != null))
            return task_ids.length > 1
        }

        self.toggle_expand = function (submission, event) {
            event.stopPropagation()
            self.expanded_submissions[submission.id] = !self.expanded_submissions[submission.id]
            self.update()
        }

        self.sort_column = 'created_when'
        self.sort_direction = 'desc'  // or 'asc'

        self.filter_children = submissions => {
            return _.filter(submissions, sub => !sub.parent)
        }

        self.sort_by = function (column, event) {
            if (event) event.stopPropagation()
            if (self.sort_column === column) {
                self.sort_direction = self.sort_direction === 'asc' ? 'desc' : 'asc'
            } else {
                self.sort_column = column
                self.sort_direction = 'asc'
            }
            self.update()
        }

        self.get_sort_value = function (submission, column) {
            switch (column) {
                case 'id': return submission.id
                case 'filename': return (submission.filename || '').toLowerCase()
                case 'owner': return (submission.owner || '').toLowerCase()
                case 'phase': return _.get(submission, 'phase.name', '').toLowerCase()
                case 'created_when': return submission.created_when || ''
                case 'status': return (self.display_status(submission) || '').toLowerCase()
                case 'score':
                    let s = self.get_score(submission)
                    return s === '' ? -Infinity : parseFloat(s)
                default: return ''
            }
        }

        self.sorted_parents = function (submissions) {
            let parents = self.filter_children(submissions)
            let sorted = _.orderBy(
                parents,
                [sub => self.get_sort_value(sub, self.sort_column)],
                [self.sort_direction]
            )
            return sorted
        }

        self.toggleShowSoftDeleted = function () {
            self.show_is_soft_deleted = !self.show_is_soft_deleted
            self.update_submissions()
            self.update()
        }

        self.is_hitl_failure = function (submission) {
            return !!(submission.status_details && submission.status_details.indexOf('Human in the Loop') !== -1)
        }

        self.migrate_menu_open = null

        self.is_organizer = function () {
            return !!opts.admin
                || !!_.get(opts, 'competition.admin')
                || !!_.get(opts, 'competition.is_admin')
        }

        self.can_migrate = function (submission) {
            return self.is_organizer()
                && !submission.parent
                && !submission.is_soft_deleted
                && submission.status === 'Finished'
                && self.get_future_phases(submission).length > 0
        }

        self.toggle_migrate_menu = function (submission, event) {
            if (event) event.stopPropagation()
            self.migrate_menu_open = (self.migrate_menu_open === submission.id) ? null : submission.id
            self.update()
        }

        self.error_message = function (response, fallback) {
            let json = response && response.responseJSON
            if (Array.isArray(json)) return json.join(' ')
            if (json && json.detail) return json.detail
            if (json && json.error_msg) return json.error_msg
            if (json && json.error) return json.error
            return fallback
        }

        self.migrate_submission = function (submission, phase, event) {
            if (event) event.stopPropagation()
            if (self.migrating) return
            if (!confirm(`Migrate submission #${submission.id} to phase "${phase.name}"?`)) {
                return
            }
            self.migrating = true
            self.update()
            CODALAB.api.migrate_submission(submission.id, phase.id)
                .done(function () {
                    toastr.success(`Submission #${submission.id} migrated to "${phase.name}"`)
                    self.migrate_menu_open = null
                    self.refresh_soon()
                })
                .fail(function (response) {
                    toastr.error(self.error_message(response, 'Error migrating submission'))
                })
                .always(function () {
                    if (self.destroyed) return

                    self.migrating = false
                    self.update()
                })
        }


        self.selected_operation = 'download_submissions'

        self.on_operation_changed = function (event) {
            self.selected_operation = event.target.value
            self.update()
        }

        self.migrate_selected_submissions = function () {
            let phase_id = self.refs.migrate_target_phase && self.refs.migrate_target_phase.value
            if (!phase_id) {
                toastr.error('Select a destination phase first')
                return
            }
            let phase = _.find(opts.competition.phases, p => String(p.id) === String(phase_id))
            let count = self.checked_submissions.length
            if (!confirm(`Migrate ${count} selected submission(s) to phase "${phase.name}"?`)) return

            CODALAB.api.migrate_many_submissions(self.checked_submissions, phase.id)
                .done(function (response) {
                    let skipped = response.skipped || []
                    toastr.success(`${response.migrated.length} submission(s) migrated`)
                    if (skipped.length > 0) {
                        toastr.warning(skipped.map(s => `#${s.id}: ${s.reason}`).join('<br>'))
                    }
                    self.refresh_soon()
                })
                .fail(function (response) {
                    toastr.error(self.error_message(response, 'Error migrating submissions'))
                })
        }

        self.get_future_phases = function (submission) {
            if (!submission || !submission.phase) return []

            const phase = _.isObject(submission.phase)
                ? submission.phase
                : _.find(opts.competition.phases, p => p.id === submission.phase)

            if (!phase) return []

            const now = new Date()
            // Any other phase of the competition that has not ended can receive the submission
            return _.filter(opts.competition.phases, p => {
                if (p.id === phase.id) return false
                if (p.end && new Date(p.end) < now) return false
                return true
            })
        }

        self.pending_children = function (submission) {
            return _.filter(self.submissions, sub => sub.parent === submission.id && sub.status === 'Submitting')
        }

        self.has_pending_children = function (submission) {
            return self.pending_children(submission).length > 0
        }

        self.is_manual_run = function (submission) {
            if (submission.auto_run) return false
            return submission.status === 'Submitting' || self.has_pending_children(submission)
        }

        self.update_submissions = function (filters, silent) {
            if (self.destroyed) return

            filters = _.clone(filters || self.build_filters())

            if (self.fetching) {
                const previous = self.pending_refresh
                self.pending_refresh = {
                    filters: filters,
                    silent: previous ? (previous.silent && !!silent) : !!silent
                }
                return
            }

            const request_id = ++self.request_id
            self.fetching = true
            if (!silent) {
                self.loading = true
                self.update()
            }

            filters.page = self.page
            filters.page_size = (String(self.page_size).toLowerCase() === 'all') ? 'all' : self.page_size

            CODALAB.api.get_submissions(filters)
                .done(function (response) {
                    if (self.destroyed || request_id !== self.request_id) return

                    let results = response
                    if (response && typeof response === 'object' && response.hasOwnProperty('results')) {
                        results = response.results || []
                        self.next = response.next || null
                        self.previous = response.previous || null
                        self.total_count = response.count || 0

                        var effectivePageSize = 1
                        var serverPageSize = undefined
                        var totalCount = (typeof response.count === 'number') ? response.count : self.total_count
                        var isLastPage = (response.next === null)

                        if (response && typeof response.page_size !== 'undefined') {
                            serverPageSize = response.page_size
                        }

                        if (typeof serverPageSize !== 'undefined') {
                            if (String(serverPageSize).toLowerCase() === 'all') {
                                self.page_size = 'all'
                            } else {
                                var parsedServerPS = Number(serverPageSize)
                                if (!isNaN(parsedServerPS) && parsedServerPS > 0) {
                                    self.page_size = parsedServerPS
                                }
                            }
                        }

                        if (String(self.page_size).toLowerCase() === 'all') {
                            if (typeof response.page_size_numeric === 'number' && response.page_size_numeric > 0) {
                                effectivePageSize = response.page_size_numeric
                            } else if (typeof response.effective_page_size === 'number' && response.effective_page_size > 0) {
                                effectivePageSize = response.effective_page_size
                            } else {
                                if (!isLastPage && Array.isArray(results) && results.length > 0) {
                                    effectivePageSize = results.length
                                } else if (isLastPage && self.page > 1 && typeof totalCount === 'number' && totalCount > 0) {
                                    var itemsOnLastPage = Array.isArray(results) ? results.length : 0
                                    var pagesBefore = self.page - 1
                                    var calc = Math.floor((totalCount - itemsOnLastPage) / pagesBefore)
                                    effectivePageSize = calc > 0 ? calc : 50
                                } else if (Array.isArray(results) && results.length > 0) {
                                    effectivePageSize = results.length
                                } else {
                                    effectivePageSize = 50
                                }
                            }
                        } else if (typeof self.page_size === 'number' && self.page_size > 0) {
                            effectivePageSize = self.page_size
                        } else {
                            effectivePageSize = 50
                        }

                        if (typeof totalCount !== 'number' || totalCount < 0) {
                            self.total_pages = 1
                        } else {
                            self.total_pages = Math.max(1, Math.ceil(totalCount / effectivePageSize))
                        }
                    } else {
                        results = response || []
                        self.next = null
                        self.previous = null
                        self.total_count = results.length
                        self.total_pages = Math.max(1, Math.ceil(self.total_count / self.page_size))
                    }

                    if (opts.admin) {
                        self.submissions = results.map((item) => {
                            item.phase = opts.competition.phases.filter((phase) => {
                                return phase.id === item.phase
                            })[0]
                            return item
                        })
                    } else {
                        self.submissions = _.filter(results, sub => sub.owner === CODALAB.state.user.username)
                    }

                    // Open the child table of parents that have children waiting for a manual run
                    self.auto_expanded = self.auto_expanded || {}
                    _.forEach(self.filter_children(self.submissions), parent => {
                        if (!parent.auto_run && parent.has_children && !self.auto_expanded[parent.id]
                            && self.has_pending_children(parent)) {
                            self.expanded_submissions[parent.id] = true
                            self.auto_expanded[parent.id] = true
                        }
                    })

                    if (!opts.admin) {
                        CODALAB.events.trigger('submissions_loaded', self.submissions)
                    }

                    self.csv_link = CODALAB.api.get_submission_csv_URL(filters)

                    self.update()
                    // Silent refreshes must not re-read the checkboxes (selection could be lost)
                    if (!silent) self.submission_checked()

                    if (silent) {
                        self.loading = false
                    } else {
                        _.delay(() => {
                            if (self.destroyed) return
                            self.loading = false
                            self.update()
                        }, 300)
                    }
                })
                .fail(function () {
                    if (self.destroyed || request_id !== self.request_id) return
                    self.loading = false
                    self.update()
                    if (!silent) toastr.error("Error retrieving submissions")
                })
                .always(function () {
                    if (request_id !== self.request_id) return

                    self.fetching = false

                    if (self.pending_refresh && !self.destroyed) {
                        const pending = self.pending_refresh
                        self.pending_refresh = null

                        self.update_submissions(pending.filters, pending.silent)
                    }
                })
        }

        self.go_to_page = function (p) {
            let newPage = parseInt(p, 10)
            if (isNaN(newPage) || newPage < 1) newPage = 1
            if (self.total_pages && newPage > self.total_pages) newPage = self.total_pages
            if (newPage === self.page) return
            self.page = newPage
            self.update_submissions()
        }

        self.change_page_size = function (e) {
            const raw = (e && e.target && typeof e.target.value !== 'undefined') ? String(e.target.value).toLowerCase() : String(self.page_size).toLowerCase()

            if (raw === 'all') {
                self.page_size = 'all'
            } else {
                const val = parseInt(raw, 10)
                if (isNaN(val) || val <= 0) return
                if (![50, 100, 500].includes(val)) return
                self.page_size = val
            }

            self.page = 1  // reset to first page when page size changes
            self.update_submissions()
        }

        self.handle_page_enter = function (ev) {
            if (ev.key === 'Enter') {
                let v = ev.target.value
                let requested = parseInt(v, 10)
                if (isNaN(requested)) return
                self.go_to_page(requested)
            }
        }

        self.add_to_leaderboard = function (submission) {
            CODALAB.api.add_submission_to_leaderboard(submission.id)
                .done(function (data) {
                    self.refresh_soon()
                    CODALAB.events.trigger('submission_changed_on_leaderboard')
                })
                .fail(function (response) {
                    toastr.error(response.responseJSON.detail)
                })
            event.stopPropagation()
        }
        self.remove_from_leaderboard = function (submission) {
            CODALAB.api.remove_submission_from_leaderboard(submission.id)
                .done(function (data) {
                    self.refresh_soon()
                    CODALAB.events.trigger('submission_changed_on_leaderboard')
                })
                .fail(function (response) {
                    toastr.error(response.responseJSON.detail)
                })
            event.stopPropagation()
        }
        self.rerun_phase = function (phase) {
            if (confirm("Are you sure? This could take hours .. you are re-running all of the submissions in a phase.")) {
                CODALAB.api.re_run_phase_submissions(phase.id)
                    .done(function (response) {
                        toastr.success(`Rerunning ${response.count} submissions`)
                        self.refresh_soon()
                    })
                    .fail(function (response) {
                        toastr.error(response.responseJSON.detail)
                    })
            }
        }

        self.filter = function () {
            delay(() => {
                self.page = 1
                self.update_submissions()
            }, 100)
        }

        self.run_submission = function (submission, event) {
            if (event) event.stopPropagation()
            CODALAB.api.run_submission(submission.id)
                .done(function (response) {
                    toastr.success('Submission queued')
                    self.refresh_soon()
                })
                .fail(function (response) {
                    if (response.responseJSON && response.responseJSON.detail) {
                        toastr.error(response.responseJSON.detail)
                    } else {
                        toastr.error(response.responseText)
                    }
                })
        }

        self.rerun_submission = function (submission, event) {
            if (event) event.stopPropagation()
            CODALAB.api.re_run_submission(submission.id)
                .done(function () {
                    toastr.success('Submission queued')
                    self.refresh_soon()
                    CODALAB.events.trigger('submission_changed_on_leaderboard')
                })
                .fail(function (response) {
                    toastr.error(self.error_message(response, response.responseText))
                })
        }

        // Ignore clicks while a resubmit request is in progress, each request creates new submissions
        self.resubmitting = false
        self.resubmit_error = function (response) {
            toastr.error(_.get(response, 'responseJSON.detail') || _.get(response, 'responseJSON[0]') || response.responseText)
        }
        self.resubmit_done = function () {
            self.resubmitting = false
            self.update()
        }

        self.resubmit_submission = function (submission) {
            event.stopPropagation()
            if (self.resubmitting || !confirm(`Resubmit submission ${submission.id} as a new submission on the current tasks of the phase?`)) {
                return
            }
            self.resubmitting = true
            CODALAB.api.resubmit_submission(submission.id)
                .done(function (response) {
                    toastr.success(`Created submission ${response.id} on current tasks. The leaderboard is not updated automatically.`)
                    self.refresh_soon()
                })
                .fail(self.resubmit_error)
                .always(self.resubmit_done)
        }

        self.resubmit_selected_submissions = function () {
            if (self.resubmitting || !confirm(`Resubmit the ${self.checked_submissions.length} selected submissions as new submissions on the current tasks of the phase?`)) {
                return
            }
            self.resubmitting = true
            CODALAB.api.resubmit_many_submissions(self.checked_submissions)
                .done(function (response) {
                    toastr.success(`Created ${response.count} submissions on current tasks. The leaderboard is not updated automatically.`)
                    self.refresh_soon()
                })
                .fail(self.resubmit_error)
                .always(self.resubmit_done)
        }

        self.rerun_selected_submissions = function () {
            CODALAB.api.re_run_many_submissions(self.checked_submissions)
                .done(function (response) {
                    toastr.success('Submissions queued')
                    self.refresh_soon()
                })
        }

        self.cancel_submission = function (submission) {
            CODALAB.api.cancel_submission(submission.id)
                .done(function (response) {
                    if (response.canceled === true) {
                        toastr.success('Submission cancelled')
                        self.refresh_soon()
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
                        self.refresh_soon()
                    })
            }
            event.stopPropagation()
        }

        self.soft_delete_submission = function (submission) {
            if (confirm(`Are you sure you want to delete your submission: ${submission.filename}?`)) {
                CODALAB.api.soft_delete_submission(submission.id)
                    .done(function (response) {
                        toastr.success(response.message || 'Submission deleted successfully');
                        self.refresh_soon()
                    })
                    .fail(function (response) {
                        let errorMsg = 'An error occurred while deleting the submission.';
                        if (response.responseJSON && response.responseJSON.error) {
                            errorMsg = response.responseJSON.error;
                        }
                        toastr.error(errorMsg)
                    })
            }
            event.stopPropagation()
        }

        self.delete_selected_submissions = function () {
            if (confirm(`Are you sure you want to delete the selected submissions?`)) {
                CODALAB.api.delete_many_submissions(self.checked_submissions)
                    .done(function (response) {
                        toastr.success('Submissions deleted')
                        self.refresh_soon()
                    })
                    .fail(function (response) {
                        toastr.error('Something went wrong')
                    })
            }
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

        self.get_score = function (submission) {
            try {
                // Look for a primary score, fallback to the first visible score if not found
                let score_obj = _.find(submission.scores, s => s.is_primary) || _.find(submission.scores, s => !s.hidden)
                if (score_obj) {
                    return self.format_score(score_obj)
                }
                return ""
            } catch {
                return ""
            }
        }

        self.format_score = function (score_obj) {
            return parseFloat(score_obj.score).toFixed(score_obj.precision || 0)
        }

        // The API only sends hidden-column scores to competition admins
        self.get_hidden_scores = function (submission) {
            return _.filter(submission.scores, 'hidden')
        }

        self.has_hidden_scores = function () {
            return _.some(self.submissions, submission => !_.isEmpty(self.get_hidden_scores(submission)))
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
                        self.refresh_soon()
                    })
                    .fail(resp => {
                        toastr.error(resp.responseJSON.detail)
                    })
            }
        }

        self.on_submission_checked = function (event) {
            event.stopPropagation()
            self.submission_checked()
        }

        self.submission_checked = function () {
            let inputs = $(self.refs.submission_table).find('input')
            let checked_boxes = inputs.not(':first').filter('input:checked')
            let unchecked_boxes = inputs.not(':first').filter('input:not(:checked)')
            inputs.first().prop('checked', unchecked_boxes.length === 0)
            self.checked_submissions = checked_boxes.serializeArray().map((x) => { return x.name })
        }

        self.select_all_pressed = function () {
            let check_boxes = $(self.refs.submission_table).find('input')
            // Set checkboxes to be equal to Select_All checkbox
            check_boxes.prop('checked', check_boxes.first().is(':checked'))

            let inputs = $(self.refs.submission_table).find('input')
            let checked_boxes = inputs.not(':first').filter('input:checked')
            self.checked_submissions = checked_boxes.serializeArray().map((x) => { return x.name })
        }

        self.submission_clicked = function (submission) {
            // stupid workaround to not modify the original submission object
            submission = _.defaultsDeep({}, submission)
            if (submission.has_children) {
                submission.children = _.map(_.sortBy(submission.children), child => {
                    return { id: child }
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

        // file_type is one of "submissions", "predictions" or "results"
        self.bulk_download = function (file_type) {
            const download_options = {
                submissions: {api: CODALAB.api.download_many_submissions, zip_name: "bulk_submissions.zip"},
                prediction_results: {api: CODALAB.api.download_many_prediction_results, zip_name: "bulk_prediction_results.zip"},
                scoring_results: {api: CODALAB.api.download_many_scoring_results, zip_name: "bulk_scoring_results.zip"},
            }
            const {api, zip_name} = download_options[file_type]

            const statusBox = document.getElementById('downloadStatus');
            const progressEl = document.getElementById('downloadProgress');
            const textEl = document.getElementById('progressText');

            statusBox.style.display = "flex";
            progressEl.style.display = "flex";
            progressEl.value = 0;
            textEl.textContent = "Preparing download...";

            // Kick the API request
            const req = api(self.checked_submissions);

            // Common error handler
            const handleError = (err) => {
                console.error("Error downloading submissions:", err);
                textEl.textContent = "Error downloading!";
                setTimeout(() => { statusBox.style.display = "none"; }, 5000);
            };

            // Success handler (async because we await inside)
            const handleSuccess = async (resp) => {

                // If wrapper returns a fetch Response object
                if (resp && typeof resp.json === "function" && typeof resp.text === "function") {
                    try { resp = await resp.json(); } catch (e) { /* fallthrough */ }
                }

                // If JSON came back as a string, parse it
                if (typeof resp === "string") {
                    try {
                    resp = JSON.parse(resp);
                    } catch (e) {
                    console.warn("download_many_submissions returned non-JSON string:", resp);
                    resp = [];
                    }
                }

                // Normalize response -> files array
                let files = resp;
                if (resp && typeof resp === 'object' && !Array.isArray(resp)) {
                // common shapes: { files: [...] } or { data: [...] } or direct array
                if (Array.isArray(resp.files)) files = resp.files;
                else if (Array.isArray(resp.data)) files = resp.data;
                else if (Array.isArray(resp.results)) files = resp.results;
                else if (Array.isArray(resp)) files = resp;
                else {
                    // if jQuery passes multiple args (data, textStatus, jqXHR), pick the first arg
                    if (arguments && arguments[0] && Array.isArray(arguments[0])) files = arguments[0];
                    else {
                    console.warn("Unexpected response shape from download_many_submissions:", resp);
                    files = [];
                    }
                }
                }

                if (!Array.isArray(files) || files.length === 0) {
                textEl.textContent = "No files to download";
                setTimeout(() => { statusBox.style.display = "none"; }, 3000);
                return;
                }

                console.log("Files returned by server:", files);

                const zip = new JSZip();
                const total = files.length;
                let completed = 0;
                const failed = [];

                const limit = 5;
                const queue = files.slice(); // clone
                const running = [];

                // worker to fetch one file
                async function worker(file) {
                try {
                    const response = await fetch(file.url);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const blob = await response.blob();
                    zip.file(file.name.replace(/[:/\\]/g, "_"), blob);
                } catch (err) {
                    console.error(`Failed to fetch ${file.name}:`, err);
                    failed.push(`${file.name} (${err.message || 'fetch error'})`);
                } finally {
                    completed++;
                    const percent = Math.floor((completed / total) * 100);
                    progressEl.value = percent;
                    textEl.textContent = `${completed} / ${total} files (${percent}%)`;
                }
                }

                // run queue with limited concurrency
                while (queue.length > 0) {
                    while (running.length < limit && queue.length > 0) {
                        const file = queue.shift();
                        const p = worker(file).then(() => {
                        // remove finished promise from running
                        const idx = running.indexOf(p);
                        if (idx !== -1) running.splice(idx, 1);
                        });
                        running.push(p);
                    }
                    // Wait for at least one running promise to finish
                    if (running.length > 0) {
                        await Promise.race(running);
                    }
                }
                await Promise.all(running);

                // Add failed.txt if necessary
                if (failed.length > 0) {
                const failedContent = `The following submissions failed to download:\n\n${failed.join("\n")}`;
                zip.file("failed.txt", failedContent);
                }

                textEl.textContent = "Generating bundle";
                progressEl.style.display = "none";

                const blob = await zip.generateAsync({ type: "blob" });
                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = zip_name;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                if (failed.length > 0) {
                textEl.textContent = `Download complete, but ${failed.length} failed (see failed.txt in the zip)`;
                } else {
                textEl.textContent = "Download ready!";
                }

                setTimeout(() => { statusBox.style.display = "none"; }, 5000);
            };

            // Support both jQuery jqXHR (.done/.fail) and native Promise (.then/.catch)
            if (req && typeof req.done === "function") {
                // jQuery-style
                req.done(function() { 
                // jQuery passes (data, textStatus, jqXHR)
                // forward only the first argument to our handler
                const args = Array.from(arguments);
                handleSuccess(args[0]);
                }).fail(handleError);
            } else if (req && typeof req.then === "function") {
                // native Promise
                req.then(handleSuccess).catch(handleError);
            } else {
                console.error("download_many_submissions returned non-promise/non-jqXHR:", req);
                handleError(new Error("Invalid request return type"));
            }
        };

        self.submission_handling = function () {
            if (self.checked_submissions.length === 0) {
                console.log("no submission is selected");
            } else {
                var submission_operation = self.refs.submission_handling_operation.value
                switch (submission_operation) {
                    case "delete":
                        self.delete_selected_submissions()
                        break;
                    case "download_submissions":
                        self.bulk_download("submissions")
                        break;
                    case "download_scoring_results":
                        self.bulk_download("scoring_results")
                        break;
                    case "download_prediction_results":
                        self.bulk_download("prediction_results")
                        break;
                    case "rerun":
                        self.rerun_selected_submissions()
                        break
                    case "resubmit":
                        self.resubmit_selected_submissions()
                        break
                    case "migrate":
                        self.migrate_selected_submissions()
                        break
                    default:
                        console.log("should never be in this state of default..")
                }
            }
        }

        // ---- Global event listeners -----------------------------------------
        self.on_phase_selected = function (selected_phase) {
            if (self.destroyed) return

            self.selected_phase = selected_phase
            self.selected_phase.hide_output =
                selected_phase.hide_output &&
                !CODALAB.state.user.has_competition_admin_privileges(self.opts.competition)

            self.update_submissions()
        }

        self.on_new_submission_created = function (new_submission_data) {
            if (self.destroyed) return

            self.submissions = self.submissions || []
            self.submissions.unshift(new_submission_data)
            self.update()
            self.refresh_soon(8)
        }

        self.on_score_updated = function () {
            if (self.destroyed) return
            $(self.refs.modal).modal('hide')
            self.refresh_soon()
        }

        self.on_submission_status_update = function (data) {
            if (self.destroyed) return
            let sub = _.find(
                self.submissions,
                submission => submission.id === data.submission_id
            )
            if (sub) {
                sub.status = data.status
                self.update()
            }
            self.refresh_soon_debounced()
        }

        CODALAB.events.on('phase_selected', self.on_phase_selected)
        CODALAB.events.on('new_submission_created', self.on_new_submission_created)
        CODALAB.events.on('score_updated', self.on_score_updated)
        CODALAB.events.on('submission_status_update', self.on_submission_status_update)

        self.remove_codalab_listeners = function () {
            CODALAB.events.off('phase_selected', self.on_phase_selected)
            CODALAB.events.off('new_submission_created', self.on_new_submission_created)
            CODALAB.events.off('score_updated', self.on_score_updated)
            CODALAB.events.off('submission_status_update', self.on_submission_status_update)
        }
    </script>

    <style type="text/stylus">
        :scope
            display block
            margin 2em 0
            min-height 90vh

        .admin-buttons
            padding-bottom 20px

        .on-leaderboard
            &:hover
                cursor auto
                background-color #21ba45 !important

        .submission_row
            &:hover
                cursor pointer
            height 42px

        table tbody .center.aligned td
            color #8c8c8c

        .failed.question.circle.icon
            color #2c3f4c

        .checkbox-label
            margin-left 5px

        .soft-deleted
            background-color #ffdede !important

        .child-submissions-row
            td
                padding-top 0
                padding-bottom 0
                height 42px

            table tbody tr:hover
                cursor pointer
                background-color rgba(0,0,0,0.03)
        .migrate-wrapper
            position relative
            display inline-block

        .migrate-menu
            position absolute
            z-index 1000
            right 0
            top 26px
            min-width 240px
            background white
            border 1px solid #ddd
            border-radius 4px
            box-shadow 0 4px 12px rgba(0, 0, 0, 0.15)
            text-align left

        .migrate-header
            padding 8px 12px
            font-weight bold
            font-size 0.9em
            color #555
            background #f7f7f7
            border-bottom 1px solid #eee
            border-radius 4px 4px 0 0

        .migrate-item
            padding 8px 12px
            cursor pointer
            border-bottom 1px solid #f0f0f0
            &:hover
                background #eef6ff
            &.disabled
                opacity 0.5
                pointer-events none

        .migrate-item-title
            display flex
            justify-content space-between
            align-items center
            font-weight 600

        .migrate-item-meta
            color #8c8c8c

        .migrate-footer
            padding 6px 12px
            font-size 0.8em
            color #8c8c8c
            background #fafafa
            border-radius 0 0 4px 4px
        .child-submissions-row
            td
                padding-top 0
                padding-bottom 0
        .migrate-wrapper
            position relative
            display inline-block

        .migrate-menu
            position absolute
            z-index 1000
            right 0
            top 26px
            min-width 240px
            background white
            border 1px solid #ddd
            border-radius 4px
            box-shadow 0 4px 12px rgba(0, 0, 0, 0.15)
            text-align left

        .migrate-header
            padding 8px 12px
            font-weight bold
            font-size 0.9em
            color #555
            background #f7f7f7
            border-bottom 1px solid #eee
            border-radius 4px 4px 0 0

        .migrate-item
            padding 8px 12px
            cursor pointer
            border-bottom 1px solid #f0f0f0
            &:hover
                background #eef6ff
            &.disabled
                opacity 0.5
                pointer-events none

        .migrate-item-title
            display flex
            justify-content space-between
            align-items center
            font-weight 600

        .migrate-item-meta
            color #8c8c8c

        .migrate-footer
            padding 6px 12px
            font-size 0.8em
            color #8c8c8c
            background #fafafa
            border-radius 0 0 4px 4px
    </style>
</submission-manager>
