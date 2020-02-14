<competition-phases>
    <div class="ui warning message" if="{warnings.length > 0}">
        <div class="header">
            Phase Errors
        </div>
        <ul class="list">
            <li each="{item in warnings}">{item}</li>
        </ul>
    </div>

    <div class="ui center aligned grid">
        <div class="row">
            <div class="fourteen wide column">
                <table class="ui padded table">
                    <thead>
                    <tr>
                        <th colspan="2">Phases</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr each="{phase, index in phases}">
                        <td>{ phase.name }</td>
                        <td class="right aligned">
                            <a class="chevron">
                                <sorting-chevrons data="{ phases }"
                                                  index="{ index }"
                                                  onupdate="{ form_updated }"></sorting-chevrons>
                            </a>
                            <a class="icon-button"
                               onclick="{ edit.bind(this, index) }">
                                <i class="blue edit icon"></i>
                            </a>
                            <a class="icon-button"
                               onclick="{ delete_phase.bind(this, index) }">
                                <i class="red trash alternate outline icon"></i>
                            </a>
                        </td>
                    </tr>
                    <tr show="{phases.length === 0}">
                        <td colspan="2" class="center aligned">
                            <em>No phases added yet, at least 1 is required!</em>
                        </td>
                    </tr>
                    </tbody>
                    <tfoot>
                    <tr>
                        <th colspan="2" class="right aligned">
                            <button class="ui tiny inverted green icon button" onclick="{ add }">
                                <i class="add circle icon"></i> Add phase
                            </button>
                        </th>
                    </tr>
                    </tfoot>
                </table>
            </div>
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

                <div class="field smaller-mde">
                    <label>Description</label>
                    <textarea class="markdown-editor" ref="description" name="description"></textarea>
                </div>

                <div class="ui accordion" ref="advanced_settings">
                    <div class="title">
                        <i class="dropdown icon"></i>
                        Advanced
                        <i class="cogs icon"></i>
                    </div>
                    <div class="content">
                        <div class="three fields">
                            <div class="field">
                                <label>
                                    Execution Time Limit <span data-tooltip="In milliseconds, 600ms default if unset"
                                                               data-inverted=""
                                                               data-position="bottom center">
                                    <i class="help icon circle"></i></span>
                                </label>
                                <input type="number" name="execution_time_limit">
                            </div>
                            <div class="field">
                                <label>
                                    Max Submissions Per Day <span
                                        data-tooltip="The maximum number of submissions a user can be made per day"
                                        data-inverted=""
                                        data-position="bottom center">
                                    <i class="help icon circle"></i></span>
                                </label>
                                <input type="number" name="max_submissions_per_day">
                            </div>
                            <div class="field">
                                <label>
                                    Max Submissions Per Person <span
                                        data-tooltip="The maximum number of submissions any single user can make to the phase"
                                        data-inverted=""
                                        data-position="bottom center">
                                    <i class="help icon circle"></i></span>
                                </label>
                                <input type="number" name="max_submissions_per_person">
                            </div>
                        </div>

                        <div class="inline field" if="{phases.length > 0 && ![null, undefined, 0].includes(selected_phase_index)}">
                            <div class="ui checkbox">
                                <input type="checkbox" name="auto_migrate_to_this_phase" ref="auto_migrate">
                                <label>Auto migrate to this phase</label>
                            </div>
                        </div>
                    </div>
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
            self.simple_markdown_editor = create_easyMDE(self.refs.description)
            // semantic multiselect
            $(self.refs.multiselect).dropdown({
                apiSettings: {
                    url: `${URLS.API}tasks/?search={query}`,
                    onResponse: (data) => {
                        return {success: true, results: _.values(data.results)}
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
            $('.ui.checkbox', self.root).checkbox()
            $(self.refs.advanced_settings).accordion()
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
                    if (!phase.name || !phase.start || phase.tasks.length === 0) {
                        is_valid = false
                    }
                })
                _.forEach(_.range(self.phases.length), i => {
                    if (i !== 0) {
                        let end = Date.parse(self.phases[i - 1].end)
                        let start = Date.parse(self.phases[i].start)

                        if (end > start || !end) {
                            let message = `Phase "${_.get(self.phases[i], 'name', i + 1)}" must start after phase "${_.get(self.phases[i - 1], 'name', i)}" ends`
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
                        phase.end = null
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
            $(self.refs.auto_migrate).prop('checked', false)

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

            self.update()
            set_form_data(phase, self.refs.form)
            $(self.refs.auto_migrate).prop('checked', _.get(phase, 'auto_migrate_to_this_phase', false))

            // Setting description in markdown editor
            self.simple_markdown_editor.value(self.phases[index].description || '')

            // Setting Tasks
            $(self.refs.multiselect)
                .dropdown('change values', _.map(phase.tasks, task => {
                    // renaming things to work w/ semantic UI multiselect
                    return {
                        value: task.key,
                        text: task.name,
                        name: task.name,
                        selected: true,
                    }
                }))

            self.show_modal()
            self.form_check_is_valid()
            self.update()
        }

        self.delete_phase = function (index) {
            if (confirm("Are you sure you want to delete '" + self.phases[index].name + "'?")) {
                self.phases.splice(index, 1)
                self.form_updated()
            }

        }

        self.save = function () {
            let number_fields = [
                'max_submissions_per_person',
                'max_submissions_per_day',
                'execution_time_limit'
            ]
            var data = get_form_data(self.refs.form)
            data.tasks = self.phase_tasks
            data.auto_migrate_to_this_phase = $(self.refs.auto_migrate).prop('checked')
            _.forEach(number_fields, field => {
                let str = _.get(data, field)
                if (str) {
                    data[field] = parseInt(str)
                } else {
                    delete data[field]
                }
            })
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
    <style type="text/stylus">
        .chevron, .icon-button
            cursor pointer
    </style>
</competition-phases>
