<data-management>
    <h1>Dataset Management</h1>

    <div class="ui divider"></div>

    <div class="ui two column grid">
        <div class="five wide column form-empty">
            <div class="ui segment">
                <h3>Form</h3>

                <div class="ui message error" show="{ Object.keys(errors).length > 0 }">
                    <div class="header">
                        Error(s) creating dataset
                    </div>
                    <ul class="list">
                        <li each="{ error, field in errors }">
                            <strong>{field}:</strong> {error}
                        </li>
                    </ul>
                </div>

                <form class="ui form {error: errors}" ref="form" onsubmit="{ save }">
                    <input-text name="name" ref="name" error="{errors.name}" placeholder="Name"></input-text>
                    <input-text name="description" ref="description" error="{errors.description}" placeholder="Description"></input-text>

                    <div class="field {error: errors.type}">
                        <select name="type" ref="type" class="ui dropdown">
                            <option value="">Type</option>
                            <option value="-">----</option>
                            <option>Ingestion Program</option>
                            <option>Input Data</option>
                            <option>Public Data</option>
                            <option>Reference Data</option>
                            <option>Scoring Program</option>
                            <option>Starting Kit</option>
                        </select>
                    </div>

                    <input-file name="data_file" error="{errors.data_file}" accept=".zip"></input-file>

                    <div class="field">
                        <div class="ui checkbox">
                            <input type="checkbox" name="is_public" tabindex="0" class="hidden">
                            <label>Public?</label>
                        </div>
                    </div>

                    <div class="ui grid">
                        <div class="sixteen wide column right aligned">
                            <button class="ui button" type="submit">
                                <i class="add circle icon"></i> Add new dataset
                            </button>
                        </div>
                    </div>
                </form>

                <div class="ui indicating progress" ref="progress">
                    <div class="bar">
                        <div class="progress">{ upload_progress }%</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="eleven wide column">
            <div class="ui icon input">
                <input type="text" placeholder="Filter by name..." ref="search" onkeyup="{ filter }">
                <i class="search icon"></i>
            </div>
            <select class="ui dropdown" ref="type_filter" onchange="{ filter }">
                <option value="">Type</option>
                <option value="-">----</option>
                <option>Ingestion Program</option>
                <option>Input Data</option>
                <option>Public Data</option>
                <option>Reference Data</option>
                <option>Scoring Program</option>
                <option>Starting Kit</option>
            </select>

            <table class="ui celled compact table">
                <thead>
                <tr>
                    <th>Name</th>
                    <th width="175px">Type</th>
                    <th width="125px">Uploaded...</th>
                    <th width="50px">Public</th>
                    <th width="50px">Delete?</th>
                </tr>
                </thead>
                <tbody>
                <tr class="dataset-row" each="{ dataset, index in filtered_datasets }">
                    <td><a href="{ URLS.DATASET_DOWNLOAD(dataset.key) }">{ dataset.name }</a></td>
                    <td>{ dataset.type }</td>
                    <td>{ timeSince(Date.parse(dataset.created_when)) } ago</td>
                    <td class="center aligned">
                        <i class="checkmark box icon green" show="{ dataset.is_public }"></i>
                    </td>
                    <td class="center aligned">
                        <button class="mini ui button red icon" onclick="{ delete_dataset.bind(this, dataset) }">
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

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []
        self.datasets = []



        // Clone of original list of datasets, but filtered to only what we want to see
        self.filtered_datasets = self.datasets.slice(0)
        self.upload_progress = undefined

        self.one("mount", function () {
            // Make semantic elements work
            $(".ui.dropdown").dropdown()
            $(".ui.checkbox").checkbox()

            // init
            self.update_datasets()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.show_progress_bar = function() {
            // The transition delays are for timing the animations, so they're one after the other
            self.refs.form.style.transitionDelay = '0s'
            self.refs.form.style.maxHeight = 0
            self.refs.form.style.overflow = 'hidden'

            self.refs.progress.style.transitionDelay = '1s'
            self.refs.progress.style.height = '24px'
        }

        self.hide_progress_bar = function() {
            // The transition delays are for timing the animations, so they're one after the other
            self.refs.progress.style.transitionDelay = '0s'
            self.refs.progress.style.height = 0

            self.refs.form.style.transitionDelay = '.1s'
            self.refs.form.style.maxHeight = '1000px'
            setTimeout(function() {
                // Do this after transition has been totally completed
                self.refs.form.style.overflow = 'visible'
            }, 1000)
        }

        self.filter = function () {
            // Delay makes this batch filters and only send one out after 100ms of not
            // receiving a call to filter
            delay(function () {
                // Clone of original
                self.filtered_datasets = self.datasets.slice(0)

                // Filters
                var search = self.refs.search.value.toLowerCase()
                var type = self.refs.type_filter.value

                if (search) {
                    self.filtered_datasets = self.filtered_datasets.filter(function (dataset) {
                        return dataset.name.toLowerCase().indexOf(search) >= 0
                    })
                }

                // A dash is the "N/A" filter option
                if (type && type !== "-") {
                    self.filtered_datasets = self.filtered_datasets.filter(function (dataset) {
                        return dataset.type === type
                    })
                }

                self.update()
            }, 100)
        }

        self.update_datasets = function () {
            CODALAB.api.get_datasets()
                .done(function (data) {
                    self.datasets = data

                    // We need to filter to actually display the results!
                    self.filter()

                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load datasets...")
                })
        }

        self.delete_dataset = function (dataset) {
            if (confirm("Are you sure you want to delete '" + dataset.name + "'?")) {
                CODALAB.api.delete_dataset(dataset.id)
                    .done(function () {
                        self.update_datasets()
                        toastr.success("Dataset deleted successfully!")
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete dataset!")
                    })
            }
        }

        self.file_upload_progress_handler = function (upload_progress) {
            if(self.upload_progress === undefined) {
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

            var required_fields = ['name', 'type', 'data_file']
            required_fields.forEach(field => {
                if(validate_data[field] === '') {
                    self.errors[field] = "This field is required"
                }
            })

            if(Object.keys(self.errors).length > 0) {
                // display errors and drop out
                self.update()
                return
            }

            // Have to get the "FormData" to get the file in a special way
            // jquery likes to work with
            var data = new FormData(self.refs.form)

            CODALAB.api.create_dataset(data, self.file_upload_progress_handler)
                .done(function (data) {
                    toastr.success("Dataset successfully uploaded!")
                    self.update_datasets()
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
                        } catch(e) {

                        }
                    }
                    toastr.error("Creation failed, error occurred")
                })
                .always(function() {
                    self.hide_progress_bar()
                })

        }
    </script>

    <style>
        .dataset-row:hover {
            background-color: rgba(46, 91, 183, 0.05);
        }

        *, div {

        }

        .progress {
            -webkit-transition: all .1s ease-in-out;
            -moz-transition: all .1s ease-in-out;
            -o-transition: all .1s ease-in-out;
            transition: all .1s ease-in-out;
            margin: 0;
            height: 0;
            -ms-flex: 1 0 auto;
            flex: 1 0 auto;
            overflow: hidden;
        }

        form {
            max-height: 1000px;  /* a max height we'll never hit, useful for CSS transitions */

            -webkit-transition: all 1s ease-in-out;
            -moz-transition: all 1s ease-in-out;
            -o-transition: all 1s ease-in-out;
            transition: all 1s ease-in-out;
        }

        .progress .bar {
            height: 24px;
        }

    </style>
</data-management>