<submission-management>

    <!--  Search -->
    <div class="ui icon input">
        <input type="text" placeholder="Search..." ref="search" onkeyup="{ filter.bind(this, undefined) }">
        <i class="search icon"></i>
    </div>
    <div class="ui checkbox inline-div" onclick="{ filter.bind(this, undefined) }">
        <label>Show Public</label>
        <input type="checkbox" ref="show_public">
    </div>
    <button class="ui green right floated labeled icon button" onclick="{show_creation_modal}">
        <i class="plus icon"></i>
        Add Submission
    </button>
    <button class="ui red right floated labeled icon button {disabled: marked_submissions.length === 0}" onclick="{delete_submissions}">
        <i class="icon delete"></i>
        Delete Selected Submissions
    </button>

    <!-- Data Table -->
    <table id="submissionsTable" class="ui {selectable: submissions.length > 0} celled compact sortable table">
        <thead>
        <tr>
            <th>File Name</th>
            <th>Competition in</th>
            <th width="175px">Size</th>
            <th width="125px">Uploaded</th>
            <th width="60px" class="no-sort">Public</th>
            <th width="50px" class="no-sort">Delete?</th>
            <th width="25px" class="no-sort"></th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ submission, index in submissions }"
            class="submission-row"
            onclick="{show_info_modal.bind(this, submission)}">
            <!--  show file name if exists otherwise show name(for old submissions)  -->
            <td>{ submission.file_name || submission.name }</td>
            <!--  show compeition name as link if competition is available -->
            <td if="{submission.competition}"><a class="link-no-deco" target="_blank" href="../competitions/{ submission.competition.id }">{ submission.competition.title }</a></td>
            <!--  show empty td if competition is not available  -->
            <td if="{!submission.competition}"></td>
            <td>{ pretty_bytes(submission.file_size) }</td>
            <td>{ timeSince(Date.parse(submission.created_when)) } ago</td>
            <td class="center aligned">
                <i class="checkmark box icon green" show="{ submission.is_public }"></i>
            </td>
            <td class="center aligned">
                <button show="{submission.created_by === CODALAB.state.user.username}" class="ui mini button red icon" onclick="{ delete_submission.bind(this, submission) }">
                    <i class="icon delete"></i>
                </button>
            </td>
            <td class="center aligned">
                <div show="{submission.created_by === CODALAB.state.user.username}" class="ui fitted checkbox">
                    <input type="checkbox" name="delete_checkbox" onclick="{ mark_submission_for_deletion.bind(this, submission) }">
                    <label></label>
                </div>
            </td>
        </tr>

        <tr if="{submissions.length === 0}">
            <td class="center aligned" colspan="6">
                <em>No Submissions Yet!</em>
            </td>
        </tr>
        </tbody>
        <tfoot>

        <!-- Pagination -->
        <tr>
            <th colspan="8" if="{submissions.length > 0}">
                <div class="ui right floated pagination menu" if="{submissions.length > 0}">
                    <a show="{!!_.get(pagination, 'previous')}" class="icon item" onclick="{previous_page}">
                        <i class="left chevron icon"></i>
                    </a>
                    <div class="item">
                        <label>{page}</label>
                    </div>
                    <a show="{!!_.get(pagination, 'next')}" class="icon item" onclick="{next_page}">
                        <i class="right chevron icon"></i>
                    </a>
                </div>
            </th>
        </tr>
        </tfoot>
    </table>

    <!--  Submission Detail Model  -->
    <div ref="info_modal" class="ui modal">
        <div class="header">
            {selected_row.file_name || selected_row.name}
        </div>
        <div class="content">
            <h3>Details</h3>

            <table class="ui basic table">
                <thead>
                <tr>
                    <th>Key</th>
                    <th>Competition in</th>
                    <th>Created By</th>
                    <th>Created</th>
                    <th>Type</th>
                    <th>Public</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>{selected_row.key}</td>
                    <!--  show compeition name as link if competition is available -->
                    <td if="{selected_row.competition}"><a class="link-no-deco" target="_blank" href="../competitions/{ selected_row.competition.id }">{ selected_row.competition.title }</a></td>
                    <!--  show empty td if competition is not available  -->
                    <td if="{!selected_row.competition}"></td>
                    <td><a href="/profiles/user/{selected_row.created_by}/" target=_blank>{selected_row.owner_display_name}</a></td>
                    <td>{pretty_date(selected_row.created_when)}</td>
                    <td>{_.startCase(selected_row.type)}</td>
                    <td>{_.startCase(selected_row.is_public)}</td>
                </tr>
                </tbody>
            </table>
            <virtual if="{!!selected_row.description}">
                <div>Description:</div>
                <div class="ui segment">
                    {selected_row.description}
                </div>
            </virtual>
            <table class="ui compact basic table">
                <thead>
                <tr>
                    <th colspan=2>File Sizes</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td style="width: 180px;">Submission:</td>
                    <td>{pretty_bytes(selected_row.submission_file_size)}</td>
                </tr>
                <tr>
                    <td>Prediction result:</td>
                    <td>{pretty_bytes(selected_row.prediction_result_file_size)}</td>
                </tr>
                <tr>
                    <td>Scoring result:</td>
                    <td>{pretty_bytes(selected_row.scoring_result_file_size)}</td>
                </tr>
                <tr>
                    <td>Detailed result:</td>
                    <td>{pretty_bytes(selected_row.detailed_result_file_size)}</td>
                </tr>
                </tbody>
            </table>
        </div>
        <div class="actions">
            <button show="{selected_row.created_by === CODALAB.state.user.username}"
                class="ui primary icon button" onclick="{toggle_is_public}">
                <i class="share icon"></i> {selected_row.is_public ? "Make Private" : "Make Public"}
            </button>
            <a href="{URLS.DATASET_DOWNLOAD(selected_row.key)}" class="ui green icon button">
                <i class="download icon"></i>Download File
            </a>
            <button class="ui cancel button">Close</button>
        </div>
    </div>

    <!--  Add Submission Model  -->
    <div ref="submission_creation_modal" class="ui modal">
        <div class="header">Add Submission Form</div>

        <div class="content">
            <div class="ui message error" show="{ Object.keys(errors).length > 0 }">
                <div class="header">
                    Error(s) creating submission
                </div>
                <ul class="list">
                    <li each="{ error, field in errors }">
                        <strong>{field}:</strong> {error}
                    </li>
                </ul>
            </div>

            <form class="ui form coda-animated {error: errors}" ref="form">
                <input-text name="name" ref="name" error="{errors.name}" placeholder="Name"></input-text>
                <input-text name="description" ref="description" error="{errors.description}"
                            placeholder="Description"></input-text>

                <input type=hidden name="type" ref="type" value="submission">
                
                <input-file name="data_file" ref="data_file" error="{errors.data_file}"
                            accept=".zip"></input-file>
            </form>

            <div class="ui indicating progress" ref="progress">
                <div class="bar">
                    <div class="progress">{ upload_progress }%</div>
                </div>
            </div>

        </div>
        <div class="actions">
            <button class="ui blue icon button" onclick="{check_form}">
                <i class="upload icon"></i>
                Upload
            </button>
            <button class="ui basic red cancel button">Cancel</button>
        </div>
    </div>

    <script>
        var self = this
        self.mixin(ProgressBarMixin)

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []
        self.submissions = []
        self.selected_row = {}
        self.marked_submissions = []

        self.upload_progress = undefined

        self.page = 1

        self.one("mount", function () {
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()
            $('#submissionsTable').tablesort()
            self.update_submissions()
        })

        self.show_info_modal = function (row, e) {
            // Return here so the info modal doesn't pop up when a checkbox is clicked
            if (e.target.type === 'checkbox') {
                return
            }
            self.selected_row = row
            self.update()
            $(self.refs.info_modal).modal('show')
        }

        self.show_creation_modal = function () {
            $(self.refs.submission_creation_modal).modal('show')
        }


        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.pretty_date = date => luxon.DateTime.fromISO(date).toLocaleString(luxon.DateTime.DATE_FULL)

        self.filter = function (filters) {
            filters = filters || {}
            _.defaults(filters, {
                search: $(self.refs.search).val(),
                page: 1,
            })
            self.page = filters.page
            self.update_submissions(filters)
        }

        self.next_page = function () {
            if (!!self.pagination.next) {
                self.page += 1
                self.filter({page: self.page})
            } else {
                alert("No valid page to go to!")
            }
        }
        self.previous_page = function () {
            if (!!self.pagination.previous) {
                self.page -= 1
                self.filter({page: self.page})
            } else {
                alert("No valid page to go to!")
            }
        }

        self.update_submissions = function (filters) {
            filters = filters || {}
            filters._public = $(self.refs.show_public).prop('checked')
            filters._type = "submission"
            CODALAB.api.get_datasets(filters)
                .done(function (data) {
                    self.submissions = data.results
                    self.pagination = {
                        "count": data.count,
                        "next": data.next,
                        "previous": data.previous
                    }
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load submissions...")
                })
        }

        self.delete_submission = function (submission, e) {
            name = submission.file_name || submission.name
            if (confirm(`Are you sure you want to delete '${name}'?`)) {
                CODALAB.api.delete_dataset(submission.id)
                    .done(function () {
                        self.update_submissions()
                        toastr.success("Submission deleted successfully!")
                        CODALAB.events.trigger('reload_quota_cleanup')
                    })
                    .fail(function (response) {
                        toastr.error(response.responseJSON['error'])
                    })
            }
            event.stopPropagation()
        }

        self.delete_submissions = function () {
            if (confirm(`Are you sure you want to delete multiple submissions?`)) {
                CODALAB.api.delete_datasets(self.marked_submissions)
                    .done(function () {
                        self.update_submissions()
                        toastr.success("Submission deleted successfully!")
                        self.marked_submissions = []
                        CODALAB.events.trigger('reload_quota_cleanup')
                    })
                    .fail(function (response) {
                        for (e in response.responseJSON) {
                            toastr.error(`${e}: '${response.responseJSON[e]}'`)
                        }
                    })
            }
            event.stopPropagation()
        }

        self.clear_form = function () {
            // Clear form
            $(':input', self.refs.form)
                .not(':button, :submit, :reset, :hidden')
                .val('')
                .removeAttr('checked')
                .removeAttr('selected');

            
            self.errors = {}
            self.update()
        }

        self.check_form = function (event) {
            if (event) {
                event.preventDefault()
            }

            // Reset upload progress, in case we're trying to re-upload or had errors -- this is the
            // best place to do it -- also resets animations
            self.file_upload_progress_handler(undefined)

            // Let's do some quick validation
            self.errors = {}
            var validate_data = get_form_data(self.refs.form)

            var required_fields = ['name', 'type', 'data_file']
            required_fields.forEach(field => {
                if (validate_data[field] === '') {
                    self.errors[field] = "This field is required"
                }
            })

            if (Object.keys(self.errors).length > 0) {
                // display errors and drop out
                self.update()
                return
            }

            // Call the progress bar wrapper and do the upload -- we want to check and display errors
            // first before doing the actual upload
            self.prepare_upload(self.upload)()

        }

        self.upload = function () {
            // Have to get the "FormData" to get the file in a special way
            // jquery likes to work with
            var metadata = get_form_data(self.refs.form)
            delete metadata.data_file  // dont send this with metadata

            if (metadata.is_public === 'on') {
                var public_confirm = confirm("Creating a public submission means this will be sent to Chahub and publicly available on the internet. Are you sure you wish to continue?")
                if (!public_confirm) {
                    return
                }
            }

            var data_file = self.refs.data_file.refs.file_input.files[0]

            CODALAB.api.create_dataset(metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    toastr.success("Submission successfully uploaded!")
                    self.update_submissions()
                    self.clear_form()
                    $(self.refs.submission_creation_modal).modal('hide')
                    CODALAB.events.trigger('reload_quota_cleanup')
                })
                .fail(function (response) {
                    if (response) {
                        try {
                            var errors = JSON.parse(response.responseText)

                            // Clean up errors to not be arrays but plain text
                            Object.keys(errors).map(function (key, index) {
                                errors[key] = errors[key].join('; ')
                            })

                            self.update({errors: errors})
                        } catch (e) {

                        }
                    }
                    toastr.error("Creation failed, error occurred")
                })
                .always(function () {
                    self.hide_progress_bar()
                })
        }

        self.toggle_is_public = () => {
            let message = self.selected_row.is_public
                ? 'Are you sure you want to make this submission private? It will no longer be available to other users.'
                : 'Are you sure you want to make this submission public? It will become visible to everyone'
            if (confirm(message)) {
                CODALAB.api.update_dataset(self.selected_row.id, {id: self.selected_row.id, is_public: !self.selected_row.is_public})
                    .done(data => {
                        toastr.success('Submission updated')
                        $(self.refs.info_modal).modal('hide')
                        self.filter()
                    })
                    .fail(resp => {
                        toastr.error(resp.responseJSON['is_public'])
                    })
            }
        }

        self.mark_submission_for_deletion = function(submission, e) {
            if (e.target.checked) {
                self.marked_submissions.push(submission.id)
            }
            else {
                self.marked_submissions.splice(self.marked_submissions.indexOf(submission.id), 1)
            }
        }

        // Update submissions on unused/failed submissions delete
        CODALAB.events.on('reload_submissions', self.update_submissions)

    </script>

    <style type="text/stylus">
        .submission-row:hover
            cursor pointer
    </style>
</submission-management>
