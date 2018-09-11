<submission-management>
    <h1>Submission Management</h1>

    <div class="ui divider"></div>

    <div class="form-grid">
        <div class="submission-phases">
            <div class="phase-parent ui styled fluid accordion">
                <div class="title">
                    <i class="dropdown icon"></i>
                    Submit Data to Phase One
                </div>
                <div class="content">
                    <div class="phase-children">
                        <button class="ui button child-btn">
                            Dataset One
                        </button>
                        <button class="ui button child-btn">
                            Dataset Two
                        </button>
                    </div>
                </div>
                <div class="title">
                    <i class="dropdown icon"></i>
                    Submit Data to Phase Two
                </div>
                <div class="content">
                    <div class="phase-children">
                        <button class="ui button child-btn">
                            Dataset One
                        </button>
                        <button class="ui button child-btn">
                            Dataset Two
                        </button>
                        <button class="ui button child-btn">
                            Dataset Three
                        </button>
                        <button class="ui button child-btn">
                            Dataset Four
                        </button>
                    </div>
                </div>

            </div>


        </div>

        <div class="submission-info">
            Lorem ipsum dolor sit amet, consectetur adipisicing elit.
        </div>

        <div class="submission-results">
            <div class="ui icon input">
                <input type="text" placeholder="Filter by name..." ref="search" onkeyup="{ filter }">
                <i class="search icon"></i>
            </div>
            <!--<select class="ui dropdown" ref="type_filter" onchange="{ filter }">-->
            <!--&lt;!&ndash;<option value="">Type</option>&ndash;&gt;-->
            <!--<option value="-">&#45;&#45;&#45;&#45;</option>-->
            <!--<option>Ingestion Program</option>-->
            <!--<option>Input Data</option>-->
            <!--<option>Public Data</option>-->
            <!--<option>Reference Data</option>-->
            <!--<option>Scoring Program</option>-->
            <!--<option>Starting Kit</option>-->
            <!--</select>-->

            <table class="ui celled compact table">
                <thead>
                <tr>
                    <th>Name</th>
                    <th>Phase</th>
                    <th>File</th>
                    <!--<th width="175px">Type</th>-->
                    <th width="125px">Uploaded...</th>
                    <th width="50px">Public</th>
                    <th width="50px">Delete?</th>
                </tr>
                </thead>
                <tbody>
                <tr class="submission-row" each="{ submission, index in filtered_submissions }">
                    <td>{ submission.name }</td>
                    <td>{ submission.phase }</td>
                    <!--<td>{ submission.zip_file }</td>-->
                    <td><a href="{submission.zip_file}" class="ui small blue button">Download File</a></td>
                    <!--<td>{ submission.type }</td>-->
                    <td>{ timeSince(Date.parse(submission.created_when)) } ago</td>
                    <td class="center aligned">
                        <i class="checkmark box icon green" show="{ submission.is_public }"></i>
                    </td>
                    <td class="center aligned">
                        <button class="mini ui button red icon"
                                onclick="{ delete_submission.bind(this, submission) }">
                            <i class="icon delete"></i>
                        </button>
                    </td>
                </tr>
                </tbody>
                <tfoot>
                <!-- Pagination that we may want later...
                <tr>
                    <th colspan="3">
                        <div class="ui right floated pagination menu">
                            <a class="icon item">
                                <i class="left chevron icon"></i>
                            </a>
                            <a class="item">1</a>
                            <a class="item">2</a>
                            <a class="item">3</a>
                            <a class="item">4</a>
                            <a class="icon item">
                                <i class="right chevron icon"></i>
                            </a>
                        </div>
                    </th>
                </tr>
                -->
                </tfoot>
            </table>
        </div>
    </div>

    <!-- Form Modal -->
    <div class="ui modal submission-form form-empty">
        <div class="ui segment">
            <h1 class="ui header">Phase X</h1>
            <h3 class="ui header">Dataset Y</h3>

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

            <form class="ui form {error: errors}" ref="form" onsubmit="{ save }">
                <input-text name="name" ref="name" error="{errors.name}" placeholder="Name"></input-text>
                <input-text name="description" ref="description" error="{errors.description}"
                            placeholder="Description"></input-text>
                <input-text name="phase" ref="phase" error="{errors.phase}" placeholder="Phase"></input-text>

                <!--<div class="field {error: errors.type}">-->
                <!--<select name="type" ref="type" class="ui dropdown">-->
                <!--<option value="">Type</option>-->
                <!--<option value="-">&#45;&#45;&#45;&#45;</option>-->
                <!--<option>Ingestion Program</option>-->
                <!--<option>Input Data</option>-->
                <!--<option>Public Data</option>-->
                <!--<option>Reference Data</option>-->
                <!--<option>Scoring Program</option>-->
                <!--<option>Starting Kit</option>-->
                <!--</select>-->
                <!--</div>-->

                <input-file name="zip_file" error="{errors.zip_file}" accept=".zip"></input-file>

                <div class="field">
                    <div class="ui checkbox">
                        <input type="checkbox" name="is_public" tabindex="0" class="hidden">
                        <label>Public?</label>
                    </div>
                </div>

                <div class="ui grid">
                    <div class="sixteen wide column right aligned">
                        <button class="ui button" type="submit">
                            <i class="add circle icon"></i> Add new submission
                        </button>
                    </div>
                </div>
                <div class="ui indicating progress" ref="progress">
                    <div class="bar">
                        <div class="progress">{ upload_progress }%</div>
                    </div>
                </div>
            </form>
        </div>
    </div>


    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []
        self.submissions = []


        // Clone of original list of submissions, but filtered to only what we want to see
        self.filtered_submissions = self.submissions.slice(0)
        self.upload_progress = undefined

        self.one("mount", function () {
            // Make semantic elements work
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()

            // init
            self.update_submissions()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.show_progress_bar = function () {
            // The transition delays are for timing the animations, so they're one after the other
            self.refs.form.style.transitionDelay = '0s'
            self.refs.form.style.maxHeight = 0
            self.refs.form.style.overflow = 'hidden'

            self.refs.progress.style.transitionDelay = '1s'
            self.refs.progress.style.height = '24px'
        }

        self.hide_progress_bar = function () {
            // The transition delays are for timing the animations, so they're one after the other
            self.refs.progress.style.transitionDelay = '0s'
            self.refs.progress.style.height = 0

            self.refs.form.style.transitionDelay = '.1s'
            self.refs.form.style.maxHeight = '1000px'
            setTimeout(function () {
                // Do this after transition has been totally completed
                self.refs.form.style.overflow = 'visible'
            }, 1000)
        }

        self.filter = function () {
            // Delay makes this batch filters and only send one out after 100ms of not
            // receiving a call to filter
            delay(function () {
                // Clone of original
                self.filtered_submissions = self.submissions.slice(0)

                // Filters
                var search = self.refs.search.value.toLowerCase()
                // var type = self.refs.type_filter.value

                if (search) {
                    self.filtered_submissions = self.filtered_submissions.filter(function (submission) {
                        return submission.name.toLowerCase().indexOf(search) >= 0
                    })
                }

                // A dash is the "N/A" filter option
                // if (type && type !== "-") {
                //     self.filtered_submissions = self.filtered_submissions.filter(function (submission) {
                //         return submission.type === type
                //     })
                // }

                self.update()
            }, 100)
        }

        self.update_submissions = function () {
            CODALAB.api.get_submissions()
                .done(function (data) {
                    self.submissions = data

                    // We need to filter to actually display the results!
                    self.filter()

                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load submissions...")
                })
        }

        self.delete_submission = function (submission) {
            if (confirm("Are you sure you want to delete '" + submission.name + "'?")) {
                CODALAB.api.delete_submission(submission.id)
                    .done(function () {
                        self.update_submissions()
                        toastr.success("Submission deleted successfully!")
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete submission!")
                    })
            }
        }

        self.file_upload_progress_handler = function (upload_progress) {
            if (self.upload_progress === undefined) {
                // First iteration of this upload, nice transitions
                self.show_progress_bar()
            }

            self.upload_progress = upload_progress * 100;
            $(self.refs.progress).progress({percent: self.upload_progress})
            self.update();
        }

        self.clear_form = function () {
            // Clear form
            $(':input', self.refs.form)
                .not(':button, :submit, :reset, :hidden')
                .val('')
                .removeAttr('checked')
                .removeAttr('selected');

            $('.dropdown', self.refs.form).dropdown('restore defaults')

            self.errors = {}
            self.update()
        }

        self.save = function (event) {
            if (event) {
                event.preventDefault()
            }

            // Reset upload progress, in case we're trying to re-upload or had errors -- this is the
            // best place to do it
            self.upload_progress = undefined

            // Let's do some quick validation
            self.errors = {}
            var validate_data = get_form_data(self.refs.form)

            // var required_fields = ['name', 'type', 'data_file']
            var required_fields = ['name', 'phase', 'zip_file']
            required_fields.forEach(field => {
                if (validate_data[field] === ''
                ) {
                    self.errors[field] = "This field is required"
                }
            })

            if (Object.keys(self.errors).length > 0) {
                // display errors and drop out
                self.update()
                return
            }

            // Have to get the "FormData" to get the file in a special way
            // jquery likes to work with
            var data = new FormData(self.refs.form)

            CODALAB.api.create_submission(data, self.file_upload_progress_handler)
                .done(function (data) {
                    toastr.success("Submission successfully uploaded!")
                    self.update_submissions()
                    self.clear_form()
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

        $(document).ready(function () {
            $('.phase-parent.accordion')
                .accordion()

            $('.submission-form.modal')
                .modal('attach events', '.child-btn', 'show')
        })
    </script>

    <style>
        .submission-row:hover {
            background-color: rgba(46, 91, 183, 0.05);
        }

        *, div {

        }

        .progress {
            -webkit-transition: all .1s ease-in-out;
            -moz-transition: all .1s ease-in-out;
            -o-transition: all .1s ease-in-out;
            transition: all .1s ease-in-out;
            height: 0;
            -ms-flex: 1 0 auto;
            flex: 1 0 auto;
            overflow: hidden;
        }

        form {
            max-height: 1000px; /* a max height we'll never hit, useful for CSS transitions */

            -webkit-transition: all 1s ease-in-out;
            -moz-transition: all 1s ease-in-out;
            -o-transition: all 1s ease-in-out;
            transition: all 1s ease-in-out;
        }

        .progress .bar {
            height: 24px;
        }

        .form-grid {
            display: grid;
            width: 100%;
            margin-bottom: 2em;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr .5fr 1fr;
            grid-template-areas: "submission-phases submission-phases" "submission-info submission-info" "submission-results submission-results";
        }

        .phase-children {
            display: grid;
            grid-template-columns: 1fr 1fr;
        }

        .child-btn {
            margin-top: 0.25em !important;
        }

        .submission-info {
            grid-area: submission-info;
        }

        .submission-results {
            margin-top: 1em;
            grid-area: submission-results;
        }

        .submission-phases {
            grid-area: submission-phases;
        }

        @media screen and (min-width: 600px) {
            .form-grid {
                display: grid;
                margin-bottom: 1em;
                width: 100%;
                grid-template-columns: 1fr 1fr;
                grid-template-rows: 1fr 1fr;
                grid-template-areas: "submission-phases submission-phases" "submission-info submission-results";
            }

            .submission-results {
                margin-left: 2em;
            }
        }

    </style>
</submission-management>