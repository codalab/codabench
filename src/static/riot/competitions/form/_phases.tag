<competition-phases>
    <button class="ui primary button modal-button" onclick="{ add }">
        <i class="add circle icon"></i> Add phase
    </button>

    <div class="ui container center aligned grid" show="{ phases.length == 0 }">
        <div class="row">
            <div class="four wide column">
                <i>No phases added yet, at least 1 is required!</i>
            </div>
        </div>
    </div>

    <div class="ui top vertical centered segment grid">

        <div class="ten wide column">

            <div class="ui one cards">
                <a each="{phase, index in phases}" class="green card">
                    <div class="content">
                        <sorting-chevrons data="{ phases }" index="{ index }"></sorting-chevrons>
                        <div class="header">{ phase.name }</div>
                        <div class="description">
                            { phase.description }
                        </div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like hover" onclick="{ edit.bind(this, index) }">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star hover-red" onclick="{ delete_phase.bind(this, index) }">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>
            </div>
        </div>
    </div>
    <div class="ui large modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Edit phase
        </div>
        <div class="content">
            <div class="ui top pointing secondary menu">
                <a class="active item" data-tab="phase_details">Phase details</a>
                <a class="item" data-tab="phase_data">Data</a>
            </div>

            <form class="ui form" ref="form">

                <!-- #####################
                     ##  Phase Details  ##
                     ##################### -->

                <div class="ui bottom active tab" data-tab="phase_details">
                    <div class="field required">
                        <label>Name</label>
                        <input name="name">
                    </div>

                    <div class="two fields">
                        <div class="ui calendar field required" ref="calendar_start">
                            <label>Start</label>
                            <div class="ui input left icon">
                                <i class="calendar icon"></i>
                                <input type="text" name="start">
                            </div>
                        </div>

                        <div class="ui calendar field" ref="calendar_end">
                            <label>End</label>
                            <div class="ui input left icon">
                                <i class="calendar icon"></i>
                                <input type="text" name="end">
                            </div>
                        </div>
                    </div>

                    <div class="field required smaller-mde">
                        <label>Description</label>
                        <textarea class="markdown-editor" ref="description" name="description"></textarea>
                    </div>



                </div>

                <!-- #####################
                     ##    Phase Data   ##
                     ##################### -->
                <div class="ui bottom tab" data-tab="phase_data">
                    <div class="two fields">
                        <div class="field">
                            <a href="{ URLS.DATASET_MANAGEMENT }" class="ui fluid large primary button" target="_blank">
                                <i class="logout icon"></i>Manage Datasets
                            </a>
                        </div>
                        <div class="field">
                            <a href="{ URLS.TASK_MANAGEMENT }" class="ui fluid large primary button" target="_blank">
                                <i class="logout icon"></i>Manage Tasks
                            </a>
                        </div>
                    </div>
                    <div class="ui toggle checkbox field">
                        <input type="checkbox" name="is_task_and_solution" ref="task_solution_toggle" onchange="{is_task_and_solution_toggle}">
                        <label>Task and Solution
                        <span data-tooltip="Toggle between a Dataset or Task and Solution style phase" data-inverted=""
                              data-position="bottom center"><i class="grey help icon circle"></i></span>
                        </label>
                    </div>

                    <div show="{!is_task_solution}">
                        <div class="three fields" data-no-js>
                            <div class="field {required: file_field === 'scoring_program'}"
                                 each="{file_field in ['scoring_program', 'ingestion_program', 'starting_kit']}">
                                <label>
                                    {_.startCase(file_field)}
                                    <span data-tooltip="Something useful to know...!" data-inverted=""
                                          data-position="bottom center"><i class=" grey help icon circle"></i></span>
                                </label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="{file_field}">
                                    <i class="search icon"></i>
                                    <input type="text" class="prompt">
                                    <div class="results"></div>
                                </div>
                            </div>
                        </div>

                        <div class="three fields" data-no-js>
                            <div class="field" each="{file_field in ['reference_data', 'input_data', 'public_data']}">
                                <label>
                                    {_.startCase(file_field)}
                                    <span data-tooltip="Something useful to know...!" data-inverted=""
                                          data-position="bottom center"><i class="grey help icon circle"></i></span>
                                </label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="{file_field}">
                                    <i class="search icon"></i>
                                    <input type="text" class="prompt">
                                    <div class="results"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div show="{is_task_solution}">
                        <div class="fluid field required">
                            <label>
                                Tasks
                                <span data-tooltip="Use task manager to create new tasks" data-inverted=""
                                      data-position="bottom center"><i class="help icon circle"></i></span>
                            </label>
                            <select name="tasks" class="ui search selection dropdown" ref="multiselect" multiple="multiple">
                            </select>
                        </div>
                    </div>
                </div>
            </form>
        </div>
        <div class="actions">
            <div class="ui button" onclick="{ close_modal }">Cancel</div>
            <div class="ui button primary { disabled: !form_is_valid }" onclick="{ save }">Save</div>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.file_fields = [
            "scoring_program",
            "ingestion_program",
            "starting_kit",
            "reference_data",
            "input_data",
            "public_data"
        ]
        self.has_initialized_calendars = false
        self.form_is_valid = false
        self.phases = []
        self.selected_phase_index = undefined
        self.is_task_solution = false

        // Form datasets have to live on their own, because they don't match up to a representation
        // on form well.. unless we use weird hidden fields everywhere.
        self.form_datasets = {}

        self.one("mount", function () {
            // awesome markdown editor
            self.simple_markdown_editor = new EasyMDE({
                element: self.refs.description,
                autoRefresh: true,
                forceSync: true,
                renderingConfig: {
                    markedOptions: {
                        sanitize: true,
                    }
                }
            });
            // semantic multiselect
            $(self.refs.multiselect).dropdown({
                apiSettings: {
                    url: `${URLS.API}tasksearch/?search={query}`,
                    onResponse: (data) => {
                        return {success: true, results: _.values(data)}
                    },
                },
                onChange: self.form_updated,
            })

            // Form change events
            $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keyup', self.form_updated)
            })

            // data search for all 6 data types
            $('.ui.search.dataset', self.root).each(function (i, item) {
                $(item)
                    .search({
                        apiSettings: {
                            url: URLS.API + 'datasets/?search={query}&type=' + (item.dataset.name || ""),
                            onResponse: function (data) {
                                // Put results in array to use maxResults setting
                                var data_in_array = []

                                Object.keys(data).forEach(key => {
                                    // Get rid of "null" in semantic UI search results
                                    data[key].description = data[key].description || ''
                                    data_in_array.push(data[key])
                                })
                                return {results: data_in_array}
                            }
                        },
                        preserveHTML: false,
                        minCharacters: 2,
                        fields: {
                            title: 'name'
                        },
                        cache: false,
                        maxResults: 4,
                        onSelect: function (result, response) {
                            // It's hard to store the dataset information (hidden fields suck), so let's just put it here temporarily
                            // and grab it back on save
                            self.form_datasets[item.dataset.name] = result
                            self.form_updated()
                        }
                    })
            })

            // Modal callback to draw markdown on EDIT show
            $(self.refs.modal).modal({
                onShow: function () {
                    setTimeout(function () {
                        self.simple_markdown_editor.codemirror.refresh()
                    }.bind(self.simple_markdown_editor), 10)
                }
            })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.is_task_and_solution_toggle = function (event) {
            self.is_task_solution = event.target.checked
            self.form_check_is_valid()
            self.update()
        }

        self.show_modal = function () {
            $(self.refs.modal)
                .modal('show')

            // Focus on the phase tab when opening modal, not dataset tab
            $('.menu .item').tab('change tab', 'phase_details')

            // Have to initialize calendars here (instead of on mount) because they don't exist yet
            if (!self.has_initialized_calendars) {
                var datetime_options = {
                    type: 'date',
                    popupOptions: {
                        position: 'bottom left',
                        lastResort: 'bottom left',
                        hideOnScroll: false
                    },
                    onHide: function () {
                        // Have to do this because onchange isn't fired when date is picked
                        self.form_updated()
                    }
                }
                var start_options = Object.assign({}, datetime_options, {endCalendar: self.refs.calendar_end})
                var end_options = Object.assign({}, datetime_options, {startCalendar: self.refs.calendar_start})

                $(self.refs.calendar_start).calendar(start_options)
                $(self.refs.calendar_end).calendar(end_options)

                self.has_initialized_calendars = true
            }
        }

        self.close_modal = function () {
            $(self.refs.modal).modal('hide')
            self.clear_form()
        }

        self.form_updated = function () {
            // This checks phases overall to make sure they are ready to go
            var is_valid = true

            // Make sure we have at least 1 phase
            if (self.phases.length === 0) {
                is_valid = false
            } else {
                // Make sure each phase has the proper details
                self.phases.forEach(function (phase) {
                    if (!phase.name || !phase.start || !phase.description) {
                        is_valid = false
                    } else {
                        is_valid = phase.is_task_and_solution ? phase.tasks.length > 0 : !!phase.scoring_program
                    }
                })
            }

            CODALAB.events.trigger('competition_is_valid_update', 'phases', is_valid)

            if (is_valid) {
                // We keep a copy of the list where we store JUST the dataset key
                var phases_copy = JSON.parse(JSON.stringify(self.phases))

                phases_copy.forEach(function (phase, i) {
                    // Since we have valid data, let's attach our "index" to the phaases
                    phase.index = i

                    // having an empty "end" causes problems with DRF validation, remove that
                    if (!phase.end) {
                        delete phase.end
                    }

                    // Get just the key from each file field
                    if (!self.is_task_solution) {
                        self.file_fields.forEach(function (file_field_name) {
                            if (!!phase[file_field_name] && !!phase[file_field_name].key) {
                                phase[file_field_name] = phase[file_field_name].key
                            }
                        })
                    }
                })

                CODALAB.events.trigger('competition_data_update', {phases: phases_copy})
            }

            self.form_check_is_valid()
            self.update()
        }

        self.form_check_is_valid = function () {
            // This checks our current form to make sure it's valid
            var data = get_form_data(self.refs.form)
            data.is_task_and_solution = self.refs.task_solution_toggle.checked

            let valid_files = data.is_task_and_solution ? data.tasks.length > 0 : self.form_datasets.scoring_program
            self.form_is_valid = !!data.name && !!data.start && !!data.description && valid_files
        }

        self.clear_form = function () {
            self.selected_phase_index = undefined
            self.form_datasets = {}
            $(self.refs.task_solution_toggle).prop('checked', false)
            $(self.refs.multiselect).dropdown('clear')
            self.is_task_solution = false

            $(':input', self.refs.form)
                .not('[type="file"]')
                .not('button')
                .not('[readonly]').each(function (i, field) {
                $(field).val('')
            })

            self.simple_markdown_editor.value('')

            self.form_updated()
        }

        self.add = function () {
            self.clear_form()
            self.show_modal()
        }

        self.edit = function (index) {
            self.selected_phase_index = index
            var phase = self.phases[index]

            set_form_data(phase, self.refs.form)
            self.is_task_solution = phase.is_task_and_solution
            $(self.refs.task_solution_toggle).prop("checked", self.is_task_solution)

            // Setting selected files
            self.file_fields.forEach(function (file_field_name) {
                if (!!phase[file_field_name]) {
                    //phase[file_field_name] = phase[file_field_name].key
                    $(`.input.search[data-name="${file_field_name}"] input`).val(phase[file_field_name].name)
                    self.form_datasets[file_field_name] = phase[file_field_name]
                }
            })

            // Setting description in markdown editor
            self.simple_markdown_editor.value(self.phases[index].description)

            // Setting Tasks
            $(self.refs.multiselect)
                .dropdown('change values', _.map(phase.tasks, task => {
                    return {name: task.name, value: task.value, selected: true}
                }))

            self.show_modal()
            self.form_check_is_valid()
            self.update()
        }

        self.delete_phase = function (index) {
            if (self.phases.length === 1) {
                toastr.error("Cannot delete, you need at least one phase")
            } else {
                if (confirm("Are you sure you want to delete '" + self.phases[index].name + "'?")) {
                    self.phases.splice(index, 1)
                    self.form_updated()
                }
            }
        }

        self.save = function () {
            var data = get_form_data(self.refs.form)
            data.is_task_and_solution = self.refs.task_solution_toggle.checked
            if (!data.is_task_and_solution) {
                data.tasks = []
                Object.assign(data, self.form_datasets)
            } else {
                _.forEach(self.file_fields, file_field_name => {
                    data[file_field_name] = null
                })
            }

            if (self.selected_phase_index === undefined) {
                self.phases.push(data)

            } else {
                // We have a selected phase, do an update instead of a create
                data.id = self.phases[self.selected_phase_index].id
                self.phases[self.selected_phase_index] = data
            }
            self.close_modal()
        }

        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_loaded', function (competition) {
            self.phases = competition.phases
            self.form_updated()
        })
    </script>
    <style scoped>
        .ui[class*="left icon"].input > i.icon {
            opacity: .15;
        }

        .modal-button {
            margin-bottom: 20px !important;
        }

        .hover:hover {
            color: #262626;
        }

        .hover-red:hover {
            color: #DB2828;
        }
    </style>
</competition-phases>