<competition-phases>
    <button class="ui primary button modal-button" onclick="{ add }">
        <i class="add circle icon"></i> Add phase
    </button>
    <div class="ui warning message" if="{warnings.length > 0}">
        <div class="header">
            Phase Errors
        </div>
        <ul class="list">
            <li each="{item in warnings}">{item}</li>
        </ul>
    </div>

    <div class="ui container center aligned grid" show="{ phases.length == 0 }">
        <div class="row">
            <div class="four wide column">
                <i>No phases added yet, at least 1 is required!</i>
            </div>
        </div>
    </div>

    <div class="ui centered">
        <div class="ui one cards">
            <a each="{phase, index in phases}" class="green card no-pointer">
                <div class="content">
                    <sorting-chevrons data="{ phases }" index="{ index }" class="hover" onupdate="{form_updated}"></sorting-chevrons>
                    <div class="header">{ phase.name }</div>
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
    <div class="ui large modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Edit phase
        </div>
        <div class="content">
            <form class="ui form" ref="form">
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

                <div class="fluid field required">
                    <label for="tasks">
                        Tasks
                        <span data-tooltip="Use task manager to create new tasks" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                    </label>
                    <select name="tasks" id="tasks" class="ui search selection dropdown" ref="multiselect"
                            multiple="multiple">
                    </select>
                </div>

                <div class="field required smaller-mde">
                    <label>Description</label>
                    <textarea class="markdown-editor" ref="description" name="description"></textarea>
                </div>
            </form>
        </div>
        <div class="actions">
            <a href="{ URLS.TASK_MANAGEMENT }" class="ui inverted green button" target="_blank">
                <i class="logout icon"></i>Manage Tasks / Datasets
            </a>
            <div class="ui button" onclick="{ close_modal }">Cancel</div>
            <div class="ui button primary { disabled: !form_is_valid }" onclick="{ save }">Save</div>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.has_initialized_calendars = false
        self.form_is_valid = false
        self.phases = []
        self.phase_tasks = []
        self.selected_phase_index = undefined
        self.warnings = []

        self.one("mount", function () {
            // awesome markdown editor
            self.simple_markdown_editor = new EasyMDE({
                element: self.refs.description,
                autoRefresh: true,
                forceSync: true,
                hideIcons: ["preview", "side-by-side", "fullscreen"]
            })
            // semantic multiselect
            $(self.refs.multiselect).dropdown({
                apiSettings: {
                    url: `${URLS.API}tasksearch/?search={query}`,
                    onResponse: (data) => {
                        return {success: true, results: _.values(data)}
                    },
                },
                onAdd: self.task_added,
                onRemove: self.task_removed,
            })

            // Form change events
            $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keyup', self.form_updated)
            })

            // Modal callback to draw markdown on EDIT show
            $(self.refs.modal).modal({
                onShow: function () {
                    setTimeout(function () {
                        self.simple_markdown_editor.codemirror.refresh()
                    }.bind(self.simple_markdown_editor), 10)
                },
                onHidden: () => {
                    self.clear_form()
                }
            })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.task_added = (key, text, item) => {
            let index = _.findIndex(self.phase_tasks, (task) => {
                return task.value === key
            })
            if (index === -1) {
                let task = {name: text, value: key, selected: true}
                self.phase_tasks.push(task)
            }
            self.form_updated()
        }

        self.task_removed = (key, text, item) => {
            let index = _.findIndex(self.phase_tasks, (task) => {
                return task.value === key
            })
            self.phase_tasks.splice(index, 1)
            self.form_updated()
        }

        self.show_modal = function () {
            $(self.refs.modal).modal('show')

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
                    if (!phase.name || !phase.start || !phase.description || phase.tasks.length === 0) {
                        is_valid = false
                    }
                })
                _.forEach(_.range(self.phases.length), i => {
                    if (i !== 0) {
                        let end = Date.parse(self.phases[i-1].end)
                        let start = Date.parse(self.phases[i].start)

                        if (end > start || !end) {
                            let message = `Phase "${_.get(self.phases[i], 'name', i + 1)}" must start after phase "${_.get(self.phases[i-1], 'name', i)}" ends`
                            if (!self.warnings.includes(message)) {
                                self.warnings.push(message)
                                self.update()
                            }
                            is_valid = false
                        }
                    }
                })
            }

            CODALAB.events.trigger('competition_is_valid_update', 'phases', is_valid)

            if (is_valid) {
                self.warnings = []
                self.update()
                // We keep a copy of the list where we store JUST the dataset key
                var indexed_phases = _.map(self.phases, (phase, i) => {
                    phase.index = i
                    if (!phase.end) {
                        delete phase.end
                    }
                    return phase
                })
                CODALAB.events.trigger('competition_data_update', {phases: indexed_phases})
            }

            self.form_check_is_valid()
            self.update()
        }

        self.form_check_is_valid = function () {
            // This checks our current form to make sure it's valid
            var data = get_form_data(self.refs.form)
            self.form_is_valid = !!data.name && !!data.start && !!data.description && self.phase_tasks.length > 0
        }

        self.clear_form = function () {
            self.selected_phase_index = undefined
            self.phase_tasks = []
            $(self.refs.multiselect).dropdown('clear')

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

        self.parse_date = function (date) {
            if (!date) {
                return date
            }
            return new Date(Date.parse(date))
        }


        self.edit = function (index) {
            self.selected_phase_index = index
            var phase = self.phases[index]
            self.phase_tasks = phase.tasks

            set_form_data(phase, self.refs.form)

            // Setting description in markdown editor
            self.simple_markdown_editor.value(self.phases[index].description)

            // Setting Tasks
            $(self.refs.multiselect)
                .dropdown('change values', _.map(phase.tasks, task => {
                    task.selected = true
                    return task
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
            data.tasks = self.phase_tasks

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
        .no-pointer:hover {
            cursor: auto !important;
        }

        .hover:hover {
            color: #262626;
            cursor: pointer;
        }

        .hover-red:hover {
            color: #DB2828;
            cursor: pointer;
        }
    </style>
</competition-phases>
