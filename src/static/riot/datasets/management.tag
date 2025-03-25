<data-management>
    <!-- Search and filter bits -->
      
    <div class="ui icon input">
        <input type="text" placeholder="Search..." ref="search" onkeyup="{ filter.bind(this, undefined) }">
        <i class="search icon"></i>
    </div>
    <select class="ui dropdown" ref="type_filter" onchange="{ filter.bind(this, undefined) }">
        <option value="">Filter By Type</option>
        <option value="-">----</option>
        <option each="{type in types}" value="{type}">{_.startCase(type)}</option>
    </select>
    <div class="ui checkbox" onclick="{ filter.bind(this, undefined) }">
        <label>Show Auto Created</label>
        <input type="checkbox" ref="auto_created">
    </div>
    <div class="ui checkbox inline-div" onclick="{ filter.bind(this, undefined) }">
        <label>Show Public</label>
        <input type="checkbox" ref="show_public">
    </div>
    <button class="ui green right floated labeled icon button" onclick="{show_creation_modal}">
        <i selenium="add-dataset" class="plus icon"></i>
        Add Dataset/Program
    </button>
    <button class="ui red right floated labeled icon button {disabled: marked_datasets.length === 0}" onclick="{delete_datasets}">
        <i class="icon delete"></i>
        Delete Selected
    </button>

    <!-- Data Table -->
    <table id="datasetsTable" class="ui {selectable: datasets.length > 0} celled compact sortable table">
        <thead>
        <tr>
            <th>File Name</th>
            <th width="175px">Type</th>
            <th width="175px">Size</th>
            <th width="125px">Uploaded</th>
            <th width="60px" class="no-sort">In Use</th>
            <th width="60px" class="no-sort">Public</th>
            <th width="50px" class="no-sort">Delete?</th>
            <th width="25px" class="no-sort"></th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ dataset, index in datasets }"
            class="dataset-row"
            onclick="{show_info_modal.bind(this, dataset)}">
            <td>{ dataset.name }</td>
            <td>{ dataset.type }</td>
            <td>{ pretty_bytes(dataset.file_size) }</td>
            <td>{ timeSince(Date.parse(dataset.created_when)) } ago</td>
            <td class="center aligned">
                <i class="checkmark box icon green" show="{ dataset.in_use.length > 0 }"></i>
            </td>
            <td class="center aligned">
                <i class="checkmark box icon green" show="{ dataset.is_public }"></i>
            </td>
            <td class="center aligned">
                <button show="{dataset.created_by === CODALAB.state.user.username}" class="ui mini button red icon" onclick="{ delete_dataset.bind(this, dataset) }">
                    <i class="icon delete"></i>
                </button>
            </td>
            <td class="center aligned">
                <div show="{dataset.created_by === CODALAB.state.user.username}" class="ui fitted checkbox">
                    <input type="checkbox" name="delete_checkbox" onclick="{ mark_dataset_for_deletion.bind(this, dataset) }">
                    <label></label>
                </div>
            </td>
        </tr>

        <tr if="{datasets.length === 0}">
            <td class="center aligned" colspan="6">
                <em>No Datasets Yet!</em>
            </td>
        </tr>
        </tbody>
        <tfoot>

        <!-- Pagination -->
        <tr>
            <th colspan="8" if="{datasets.length > 0}">
                <div class="ui right floated pagination menu" if="{datasets.length > 0}">
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

    <!--  Dataset Detail Model  -->
    <div ref="info_modal" class="ui modal">
        <div class="header">
            {selected_row.name}
        </div>
        <div class="content">
            <h3>Details</h3>

            <table class="ui basic table">
                <thead>
                <tr>
                    <th>Key</th>
                    <th>Created By</th>
                    <th>Created</th>
                    <th>Type</th>
                    <th>Public</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>{selected_row.key}</td>
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
            <div show="{!!_.get(selected_row.in_use, 'length')}"><strong>Used by:</strong>
                <div class="ui bulleted list">
                    <div class="item" each="{comp in selected_row.in_use}">
                        <a href="{URLS.COMPETITION_DETAIL(comp.pk)}" target="_blank">{comp.title}</a>
                    </div>
                </div>
            </div>
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

    <!--  Add Dataset Model  -->
    <div ref="dataset_creation_modal" class="ui modal">
        <div class="header">Add Dataset/Program Form</div>

        <div class="content">
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

            <form class="ui form coda-animated {error: errors}" ref="form">
                <input-text selenium="scoring-name" name="name" ref="name" error="{errors.name}" placeholder="Name"></input-text>
                <input-text selenium="scoring-desc" name="description" ref="description" error="{errors.description}"
                            placeholder="Description"></input-text>

                <div class="field {error: errors.type}">
                    <select selenium="type" id="type_of_data" name="type" ref="type" class="ui dropdown">
                        <option value="">Type</option>
                        <option value="-">----</option>
                        <option each="{type in types}" value="{type}">{_.startCase(type)}</option>
                    </select>
                </div>

                <input-file selenium="file" name="data_file" ref="data_file" error="{errors.data_file}"
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
                <i selenium="upload" class="upload icon"></i>
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
        self.types = [
            "ingestion_program",
            "input_data",
            "public_data",
            "reference_data",
            "scoring_program",
            "starting_kit",
        ]
        self.errors = []
        self.datasets = []
        self.selected_row = {}
        self.marked_datasets = []


        self.upload_progress = undefined

        self.page = 1

        self.one("mount", function () {
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()
            $('#datasetsTable').tablesort()
            self.update_datasets()
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
            $(self.refs.dataset_creation_modal).modal('show')
        }


        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.pretty_date = date => luxon.DateTime.fromISO(date).toLocaleString(luxon.DateTime.DATE_FULL)

        self.filter = function (filters) {
            let type = $(self.refs.type_filter).val()
            filters = filters || {}
            _.defaults(filters, {
                type: type === '-' ? '' : type,
                search: $(self.refs.search).val(),
                page: 1,
            })
            self.page = filters.page
            self.update_datasets(filters)
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

        self.update_datasets = function (filters) {
            filters = filters || {}
            filters.was_created_by_competition = $(self.refs.auto_created).prop('checked')
            filters._public = $(self.refs.show_public).prop('checked')
            filters._type = "dataset"
            CODALAB.api.get_datasets(filters)
                .done(function (data) {
                    self.datasets = data.results
                    self.pagination = {
                        "count": data.count,
                        "next": data.next,
                        "previous": data.previous
                    }
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load datasets...")
                })
        }

        self.delete_dataset = function (dataset, e) {
            if (confirm(`Are you sure you want to delete '${dataset.name}'?`)) {
                CODALAB.api.delete_dataset(dataset.id)
                    .done(function () {
                        self.update_datasets()
                        toastr.success("Dataset deleted successfully!")
                        CODALAB.events.trigger('reload_quota_cleanup')
                    })
                    .fail(function (response) {
                        toastr.error(response.responseJSON['error'])
                    })
            }
            event.stopPropagation()
        }

        self.delete_datasets = function () {
            if (confirm(`Are you sure you want to delete multiple datasets?`)) {
                CODALAB.api.delete_datasets(self.marked_datasets)
                    .done(function () {
                        self.update_datasets()
                        toastr.success("Dataset deleted successfully!")
                        self.marked_datasets = []
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

            $('.dropdown', self.refs.form).dropdown('restore defaults')

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
                var public_confirm = confirm("Creating a public dataset means this will be sent to Chahub and publicly available on the internet. Are you sure you wish to continue?")
                if (!public_confirm) {
                    return
                }
            }

            var data_file = self.refs.data_file.refs.file_input.files[0]

            CODALAB.api.create_dataset(metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    toastr.success("Dataset successfully uploaded!")
                    self.update_datasets()
                    self.clear_form()
                    $(self.refs.dataset_creation_modal).modal('hide')
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
                ? 'Are you sure you want to make this dataset private? It will no longer be available to other users.'
                : 'Are you sure you want to make this dataset public? It will become visible to everyone'
            if (confirm(message)) {
                CODALAB.api.update_dataset(self.selected_row.id, {id: self.selected_row.id, is_public: !self.selected_row.is_public})
                    .done(data => {
                        toastr.success('Dataset updated')
                        $(self.refs.info_modal).modal('hide')
                        self.filter()
                    })
                    .fail(resp => {
                        toastr.error(resp.responseJSON['is_public'])
                    })
            }
        }

        self.mark_dataset_for_deletion = function(dataset, e) {
            if (e.target.checked) {
                self.marked_datasets.push(dataset.id)
            }
            else {
                self.marked_datasets.splice(self.marked_datasets.indexOf(dataset.id), 1)
            }
        }


        // Update datasets on unused datasets delete
        CODALAB.events.on('reload_datasets', self.update_datasets)

    </script>

    <style type="text/stylus">
        .dataset-row:hover
            cursor pointer
    </style>
</data-management>
