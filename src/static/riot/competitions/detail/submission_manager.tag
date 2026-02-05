<submission-manager class="submission-manager">
    <div if="{ opts.admin }" class="admin-buttons" style="display: flex; align-items: center; gap: 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="ui dropdown button" ref="rerun_button">
            <i class="icon redo"></i>
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

            <select class="ui dropdown" ref="submission_handling_operation">
            <option value="download">Download selected submissions</option>
            <option value="delete">Delete selected submissions</option>
            <option value="rerun">Rerun selected submissions</option>
            </select>

            <button type="button" class="ui button" disabled="{checked_submissions.length === 0}" onclick="{submission_handling.bind(this)}">
            Apply
            </button>
        </div>
        <div id="downloadStatus" style="display:none; display: flex; flex-direction: column; align-items: flex-start;">
            <progress id="downloadProgress" value="0" max="100"  style="display:none; width: 150px;"></progress>
            <div id="progressText" style="margin-top: 4px;"></div>
            <!-- -->
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
    <div class="ui input" if="{opts.admin}">
        <input 
        type="checkbox" 
        checked="{show_is_soft_deleted}"
        onclick="{toggleShowSoftDeleted}">
        <label class="checkbox-label">Show soft-deleted submissions</label>
    </div>
    <table class="ui celled selectable sortable table" ref="submission_table">
        <thead>
            <tr>
                <th if="{opts.admin}">
                    <div class="ui checkbox" onclick="{select_all_pressed.bind(this)}">
                        <input type="checkbox" name="select_all">
                        <label>All</label>
                    </div>
                </th>
                <th class="sorted descending collapsing">ID #</th>
                <th>File name</th>
                <th if="{ opts.admin }">Owner</th>
                <th if="{ opts.admin }">Phase</th>
                <th>Date</th>
                <th>Status</th>
                <th>Score</th>
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
            <tr show="{!loading}" each="{ submission, index in filter_children(submissions) }"
                onclick="{ submission_clicked.bind(this, submission) }" class="submission_row {submission.is_soft_deleted ? 'soft-deleted' : ''}">
                <td if="{ opts.admin }">
                    <div if="{ !submission.is_soft_deleted }" class="ui checkbox" onclick="{on_submission_checked.bind(this)}">
                        <input type="checkbox" name="{submission.id}">
                        <label></label>
                    </div>
                </td>
                <td>{ submission.id }</td>
                <td>{ submission.filename }</td>
                <td if="{ opts.admin }">{ submission.owner }</td>
                <td if="{ opts.admin }">{ submission.phase.name }</td>
                <td>{ pretty_date(submission.created_when) }</td>
                <td class="right aligned collapsing">
                    { submission.status }
                    <sup data-tooltip="{submission.status_details}">
                        <i if="{submission.status === 'Failed'}" class="failed question circle icon"></i>
                    </sup>
                    <sup data-tooltip="An organizer will run your submission soon">
                        <i if="{submission.status === 'Submitting' && !submission.auto_run}"
                            class="question circle icon"></i>
                    </sup>
                </td>
                <td>{get_score(submission)}</td>
                <td
                    if="{ opts.competition.enable_detailed_results && opts.competition.show_detailed_results_in_submission_panel }">
                    <a if="{submission.status === 'Finished'}" href="detailed_results/{submission.id}" target="_blank"
                        class="eye-icon-link">
                        <i class="icon grey eye eye-icon"></i>
                    </a>
                </td>
                <!--  Show Action buttons when submission is not soft deleted  -->
                <!--  Otherwise show empty <td>  -->
                <td if="{ submission.is_soft_deleted }"></td>
                <td class="center aligned" if="{ !submission.is_soft_deleted }">
                    <virtual if="{ opts.admin}">
                        <!-- run/rerun submission -->
                        <!--  run: status = submitting auto_run = false  -->
                        <!--  rerun: else   -->
                        <span
                            data-tooltip="{ submission.status === 'Submitting' && !submission.auto_run ? 'Run Submission' : 'Rerun Submission' }"
                            data-inverted=""
                            onclick="{ submission.status === 'Submitting' && !submission.auto_run ? run_submission.bind(this, submission) : rerun_submission.bind(this, submission) }">
                            <i
                                class="icon { submission.status === 'Submitting' && !submission.auto_run ? 'green play' : 'blue redo' }"></i>
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
                </td>
            </tr>
        </tbody>
    </table>

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

                    <div if="{is_admin()}" data-tab="admin" class="parent-modal item">Admin</div>

                    <!-- Sometimes submissions end up in a bad state with no children..  -->
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
        self.checked_submissions = []
        self.show_is_soft_deleted = false

        self.on("mount", function () {
            $(self.refs.search).dropdown()
            $(self.refs.status).dropdown()
            $(self.refs.phase).dropdown()
            $(self.refs.rerun_button).dropdown()
            $(self.refs.submission_handling_operation).dropdown()
            $(self.refs.submission_table).tablesort()
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

        self.filter_children = submissions => {
            return _.filter(submissions, sub => !sub.parent)
        }

        self.toggleShowSoftDeleted = function () {
            self.show_is_soft_deleted = !self.show_is_soft_deleted
            self.update_submissions()
            self.update()
        }

        self.update_submissions = function (filters) {
            self.loading = true
            self.update()
            if (opts.admin) {
                filters = filters || { phase__competition: opts.competition.id }
                filters.show_is_soft_deleted = self.show_is_soft_deleted
            } else {
                filters = filters || { phase: self.selected_phase.id }
            }
            filters = filters || { phase: self.selected_phase.id }
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
                    self.submission_checked()

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
                    self.update_submissions()
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
                        self.update_submissions()
                    })
                    .fail(function (response) {
                        toastr.error(response.responseJSON.detail)
                    })
            }
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

        self.run_submission = function (submission) {
            CODALAB.api.run_submission(submission.id)
                .done(function (response) {
                    toastr.success('Submission queued')
                    self.update_submissions()
                })
                .fail(function (response) {
                    if (response.responseJSON.detail) {
                        toastr.error(response.responseJSON.detail)
                    } else {
                        toastr.error(response.responseText)
                    }
                })
            event.stopPropagation()

        }

        self.rerun_submission = function (submission) {
            CODALAB.api.re_run_submission(submission.id)
                .done(function (response) {
                    toastr.success('Submission queued')
                    self.update_submissions()
                })
                .fail(function (response) {
                    if (response.responseJSON.detail) {
                        toastr.error(response.responseJSON.detail)
                    }
                    else if (response.responseJSON.error_msg) {
                        toastr.error(response.responseJSON.error_msg)
                    }
                    else {
                        toastr.error(response.responseText)
                    }
                })
            event.stopPropagation()
        }

        self.rerun_selected_submissions = function () {
            CODALAB.api.re_run_many_submissions(self.checked_submissions)
                .done(function (response) {
                    toastr.success('Submissions queued')
                    self.update_submissions()
                })
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

        self.soft_delete_submission = function (submission) {
            if (confirm(`Are you sure you want to delete your submission: ${submission.filename}?`)) {
                CODALAB.api.soft_delete_submission(submission.id)
                    .done(function (response) {
                        toastr.success(response.message || 'Submission deleted successfully');
                        self.update_submissions()
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
                        self.update_submissions()
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
                return parseFloat(submission.scores[0].score).toFixed(2)

            } catch {
                return ""
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

        self.bulk_download = function () {
            const statusBox = document.getElementById('downloadStatus');
            const progressEl = document.getElementById('downloadProgress');
            const textEl = document.getElementById('progressText');

            statusBox.style.display = "flex";
            progressEl.style.display = "flex";
            progressEl.value = 0;
            textEl.textContent = "Preparing download...";

            // Kick the API request
            const req = CODALAB.api.download_many_submissions(self.checked_submissions);

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
                link.download = "bulk_submissions.zip";
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
            // console.log(self.checked_submissions)
            if (self.checked_submissions.length === 0) {
                console.log("no submission is selected");
            } else {
                var submission_operation = self.refs.submission_handling_operation.value
                switch (submission_operation) {
                    case "delete":
                        self.delete_selected_submissions()
                        break;
                    case "download":
                        self.bulk_download("submissions")
                        break;
                    case "download_results":
                        self.bulk_download("results")
                        break;
                    case "download_prediction":
                        self.bulk_download("predictions")
                        break;
                    case "rerun":
                        self.rerun_selected_submissions()
                        break
                    default:
                        console.log("should never be in this state of default..")
                }
            }
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
            height 52px

        table tbody .center.aligned td
            color #8c8c8c

        .failed.question.circle.icon
            color #2c3f4c

        .checkbox-label
            margin-left 5px

        .soft-deleted
            background-color #ffdede !important
    </style>
</submission-manager>
