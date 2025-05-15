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
                                <i selenium="add-phase" class="add circle icon"></i> Add phase
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
            <!--  When no phase is selected selected_phase_index is undefined  -->
            { typeof selected_phase_index === 'undefined' ?  'Add Phase' : 'Edit Phase' }
        </div>
        <div class="content">
            <form selenium="phase-form" class="ui form" ref="form">
                <div class="field required">
                    <label>Name</label>
                    <input name="name">
                </div>

                <!--  Start Date and Time  -->
                <div class="two fields">
                    <div class="ui calendar field required" ref="calendar_start_date">
                        <label>Start Date</label>
                        <div class="ui input left icon">
                            <i class="calendar icon"></i>
                            <input type="text" name="start_date">
                        </div>
                    </div>
                    <div class="ui calendar field required" ref="calendar_start_time">
                        <label>Start Time
                        <span data-tooltip="Select time in UTC+0 time zone" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                        </label> 
                        
                        <div class="ui input left icon">
                            <i class="clock icon"></i>
                            <input type="text" name="start_time">
                        </div>
                    </div>
                </div>

                <!--  End Date and Time  -->
                <div class="two fields">
                    <div class="ui calendar field" ref="calendar_end_date">
                        <label>End Date</label>
                        <div class="ui input left icon">
                            <i class="calendar icon"></i>
                            <input type="text" name="end_date">
                        </div>
                    </div>

                    <div class="ui calendar field" ref="calendar_end_time">
                        <label>End Time
                        <span data-tooltip="Select time in UTC+0 time zone" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                        </label>
                        <div class="ui input left icon">
                            <i class="clock icon"></i>
                            <input type="text" name="end_time">
                        </div>
                    </div>
                </div>

                <div class="fluid field required" ref="tasks_select_container" id="tasks_select_container">
                    <label for="tasks">
                        Tasks (Order will be saved) Note: Adding a new task will cause all submissions to be run against it.
                        <span data-tooltip="Use Resources section to create new tasks" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                    </label>
                    <select name="tasks" id="tasks" class="ui search selection dropdown" ref="multiselect"
                            multiple="multiple">
                    </select>
                </div>
                <!--  BB Adding public_data and starting_kit dropdowns  -->
                <div class="fluid field" ref="public_data_select_container" id="public_data_select_container">
                    <label for="public_data">
                        Public Data (Only 1 per phase)
                        <span data-tooltip="Use Resources section to create new public datasets" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                    </label>
                    <select name="public_data" id="public_data" class="ui search selection dropdown" ref="public_data_multiselect"
                            multiple="multiple">
                    </select>
                </div>
                <div class="fluid field" ref="starting_kit_select_container" id="starting_kit_select_container">
                    <label for="starting_kit">
                        Starting Kit (Only 1 per phase)
                        <span data-tooltip="Use Resources section to create new starting kits" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                    </label>
                    <select name="starting_kit" id="starting_kit" class="ui search selection dropdown" ref="starting_kit_multiselect"
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
                                    Execution Time Limit (seconds)<span data-tooltip="600s if unset, { CODALAB.state.public_env_variables.MAX_EXECUTION_TIME_LIMIT }s max with default queue."
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
                        <div class="field">
                            <div class="ui checkbox">
                                <label>Hide Submission Output
                                    <span data-tooltip="Hide all submission output" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                                </label>
                                <input type="checkbox" ref="hide_output">
                            </div>
                        </div>
                        <div class="field">
                            <div class="ui checkbox">
                                <label>Hide Prediction Output 
                                    <span data-tooltip="Prevent participants from downloading 'Output from prediction step'" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                                </label>
                                <input type="checkbox" ref="hide_prediction_output">
                            </div>
                        </div>
                        <div class="field">
                            <div class="ui checkbox">
                                <label>Hide Score Output 
                                    <span data-tooltip="Prevent participants from downloading 'Output from scoring step'" data-inverted=""
                              data-position="bottom center"><i class="help icon circle"></i></span>
                                </label>
                                <input type="checkbox" ref="hide_score_output">
                            </div>
                        </div>

                        <div class="inline field" if="{phases.length > 0 && ![null, undefined, 0].includes(selected_phase_index)}">
                            <div class="ui checkbox">
                                <input type="checkbox" name="auto_migrate_to_this_phase" ref="auto_migrate">
                                <label>
                                    Auto migrate to this phase <span data-tooltip="Re-submit all leaderboard submissions automatically when the phase starts."
                                                               data-inverted=""
                                                               data-position="bottom center">
                                    <i class="help icon circle"></i></span>
                                </label>
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
            <div selenium="save2" class="ui button primary { disabled: !form_is_valid }" onclick="{ save }">Save</div>
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
        self.phase_public_data = []
        self.phase_starting_kit = []
        self.selected_phase_index = undefined
        self.warnings = []

        self.one("mount", function () {
            $('.ui.checkbox', self.root).checkbox()

            // awesome markdown editor
            self.simple_markdown_editor = create_easyMDE(self.refs.description)

            // semantic multiselect
            $(self.refs.multiselect).dropdown({
                apiSettings: {
                    url: `${URLS.API}tasks/?public=true&search={query}`,
                    cache: false,
                    onResponse: (data) => {
                        return {success: true, results: _.values(data.results)}
                    },
                },
                onAdd: self.task_added,
                onRemove: self.task_removed,
            })

            $(self.refs.public_data_multiselect).dropdown({
                apiSettings: {
                    url: `${URLS.API}datasets/?search={query}&type=public_data`,
                    cache: false,
                    onResponse: (data) => {
                        return {success: true, results: _.values(data.results)}
                    },
                },
                onAdd: self.public_data_added,
                onRemove: self.public_data_removed,
            })
            
            $(self.refs.starting_kit_multiselect).dropdown({
                apiSettings: {
                    url: `${URLS.API}datasets/?search={query}&type=starting_kit`,
                    cache: false,
                    onResponse: (data) => {
                        return {success: true, results: _.values(data.results)}
                    },
                },
                onAdd: self.starting_kit_added,
                onRemove: self.starting_kit_removed,
            })
            // When adding \ removing phase we need to code it like above

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
            $(self.refs.advanced_settings).accordion()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        // Tasks
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

        // Public Data
        self.public_data_added = (key, text, item) => {
            let index = _.findIndex(self.phase_public_data, (public_data) => {
                if (public_data === null){
                    return false
                }else{
                    if (public_data.value != key){
                        // Remove if not first selected. We can have only one.
                        alert("Only one Public Data set allowed per phase.")
                        setTimeout(()=>{$('a[data-value="'+ key +'"] .delete.icon').click()},100)
                    }
                    return public_data.value === key
                }
            })
            if (index === -1 && (self.phase_public_data.length === 0 || self.phase_public_data[0] === null)) {
                let public_data = {name: text, value: key, selected: true}
                self.phase_public_data[0] = public_data
            }
            self.form_updated()
        }

        self.public_data_removed = (key, text, item) => {
            let index = _.findIndex(self.phase_public_data, (public_data) => {
                return public_data.value === key
            })
            if (index != -1){
                self.phase_public_data.splice(index, 1)
            }
            self.form_updated()
        }

        // Starting Kit
        self.starting_kit_added = (key, text, item) => {
            let index = _.findIndex(self.phase_starting_kit, (starting_kit) => {
                if (starting_kit === null){
                    return false
                }else{
                    if (starting_kit.value != key){
                        // Remove if not first selected. We can have only one.
                        alert("Only one Starting Kit set allowed per phase.")
                        setTimeout(()=>{$('a[data-value="'+ key +'"] .delete.icon').click()},100)
                    }
                    return starting_kit.value === key
                }
            })
            if (index === -1 && (self.phase_starting_kit.length === 0 || self.phase_starting_kit[0] === null)) {
                let starting_kit = {name: text, value: key, selected: true}
                self.phase_starting_kit[0] = starting_kit
            }
            self.form_updated()
        }

        self.starting_kit_removed = (key, text, item) => {
            let index = _.findIndex(self.phase_starting_kit, (starting_kit) => {
                return starting_kit.value === key
            })
            self.phase_starting_kit.splice(index, 1)
            self.form_updated()
        }



        self.show_modal = function () {
            $(self.refs.modal).modal('show')

            // Focus on the phase tab when opening modal, not dataset tab
            $('.menu .item').tab('change tab', 'phase_details')

            // Have to initialize calendars here (instead of on mount) because they don't exist yet
            if (!self.has_initialized_calendars) {

                // Initialize date calendars options
                var date_options = {
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

                // Initialize time calendars options
                var time_options = {
                    type: 'time',
                    popupOptions: {
                        position: 'bottom left',
                        lastResort: 'bottom left',
                        hideOnScroll: false
                    },
                    ampm: false,
                    onHide: function () {
                        // Have to do this because onchange isn't fired when date is picked
                        self.form_updated()
                    }
                }

                // Create a new options object for the start date calendar using 'date_options'
                $(self.refs.calendar_start_date).calendar(date_options)
                // Create a new options object for the end date calendar using 'date_options'
                $(self.refs.calendar_end_date).calendar(date_options)

                // Initialize the start time calendar with the defined options. 
                // This will create a time picker for the 'start time' field.
                $(self.refs.calendar_start_time).calendar(time_options)

                // Initialize the end time calendar with the same time picker options.
                // This will create a time picker for the 'end time' field.
                $(self.refs.calendar_end_time).calendar(time_options)

                self.has_initialized_calendars = true
            }

            // This condition is executed when selected_phase_index is not undefined i.e. a phase is selected
            // This means that user is updating a phase and is not creating a new phase
            if(!(self.selected_phase_index === undefined)){
                
                // Set Dates
                $(self.refs.calendar_start_date).calendar('set date', self.getDate(self.phases[self.selected_phase_index].start))
                $(self.refs.calendar_end_date).calendar('set date', self.getDate(self.phases[self.selected_phase_index].end))

                // Set times
                $(self.refs.calendar_start_time).calendar('set date', self.getTime(self.phases[self.selected_phase_index].start))
                $(self.refs.calendar_end_time).calendar('set date', self.getTime(self.phases[self.selected_phase_index].end))
            }
        }

        self.close_modal = function () {
            $(self.refs.modal).modal('hide')
        }

        self.formatDateToYYYYMMDD = function(input) {
            // This function formats date in the format YYYY-MM-DD

            // convert input to date
            var dateObject = new Date(input)

            // check if date has a time
            if (!isNaN(dateObject.getTime())) {
                // Extract year
                var year = dateObject.getFullYear()
                // Extract Month
                var month = (dateObject.getMonth() + 1).toString().padStart(2, '0')
                // Extract day
                var day = dateObject.getDate().toString().padStart(2, '0')
                return `${year}-${month}-${day}`
            }
            return input
        }
        self.getDate = function(dt) {
            // function for extracting date only from the start or end date of a phase
            // format: 'YYYY-MM-DD'
            if (dt != null){
                dt = new Date(dt)
                return dt.toISOString().split('T')[0]
            }else{
                return ""
            }
        }
        self.getTime = function(dt) {
            // function for extracting time only from the start or end date of a phase
            // format: 'HH:MM' 24-hour format in UTC
            if (dt != null){
                dt = new Date(dt)
                return dt.toLocaleTimeString('en-GB', { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    timeZone: 'UTC' // Set time zone to UTC
                })
            }else{
                return ""
            }
        }
        self.formatDateTo_Y_m_d_T_H_M_S = function(input) {
            // This function formats date in the format YYYY-MM-DDTHH:MM:SS

            // Convert input to date
            var dateObject = new Date(input)

            // Check if date is valid
            if (!isNaN(dateObject.getTime())) {
                // Extract year
                var year = dateObject.getFullYear()
                // Extract month
                var month = (dateObject.getMonth() + 1).toString().padStart(2, '0') // Months are zero-based
                // Extract day
                var day = dateObject.getDate().toString().padStart(2, '0')
                // Extract hours
                var hours = dateObject.getHours().toString().padStart(2, '0')
                // Extract minutes
                var minutes = dateObject.getMinutes().toString().padStart(2, '0')
                // Extract seconds
                var seconds = dateObject.getSeconds().toString().padStart(2, '0')
                
                // Return formatted date string
                return year + '-' + month + '-' + day + 'T' + hours + ':' + minutes + ':' + seconds
            }
            return input
        }


        self.form_updated = function () {
            // This checks phases overall to make sure they are ready to go
            var is_valid = true

            // Make sure we have at least 1 phase
            if (self.phases.length === 0) {
                is_valid = false
            } else {
                // Make sure each phase has the proper details
                // BB - check for public_data and starting_kit - NOT DONE
                self.phases.forEach(function (phase) {
                    if (!phase.name || !phase.start || phase.tasks.length === 0) {
                        is_valid = false
                    }
                })
                _.forEach(_.range(self.phases.length), i => {
                    if (i !== 0) {
                        let end = Date.parse(self.formatDateToYYYYMMDD(self.phases[i - 1].end))
                        let start = Date.parse(self.formatDateToYYYYMMDD(self.phases[i].start))
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
            // Phase add/update form is valid if it has 
            // name, start_date, start_time, and at least one task
            self.form_is_valid = !!data.name && !!data.start_date && !!data.start_time && self.phase_tasks.length > 0
        }

        self.clear_form = function () {
            self.selected_phase_index = undefined
            self.phase_tasks = []
            $(self.refs.multiselect).dropdown('clear')
            $(self.refs.public_data_multiselect).dropdown('clear')
            $(self.refs.starting_kit_multiselect).dropdown('clear')

            $(':input', self.refs.form)
                .not('[type="file"]')
                .not('button')
                .not('[readonly]').each(function (i, field) {
                $(field).val('')
            })
            $(self.refs.auto_migrate).prop('checked', false)

            // Clear date and time fields values
            $(self.refs.calendar_start_date).find('input[name="start_date"]').val('')
            $(self.refs.calendar_start_time).find('input[name="start_time"]').val('')
            $(self.refs.calendar_end_date).find('input[name="end_date"]').val('')
            $(self.refs.calendar_end_time).find('input[name="end_time"]').val('')

            // Clear the date fields calendars
            // This will make sure that when you click add new phase, the date and time pickers
            // will not show other phase date/time preselected in the date and time pickers
            $(self.refs.calendar_start_date).calendar('clear');
            $(self.refs.calendar_end_date).calendar('clear');
            $(self.refs.calendar_start_time).calendar('clear');
            $(self.refs.calendar_end_time).calendar('clear');

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
            self.phase_public_data = [phase.public_data]
            self.phase_starting_kit = [phase.starting_kit]

            self.update()
            set_form_data(phase, self.refs.form)
            $(self.refs.auto_migrate).prop('checked', _.get(phase, 'auto_migrate_to_this_phase', false))
            self.refs.hide_output.checked = phase.hide_output
            self.refs.hide_prediction_output.checked = phase.hide_prediction_output
            self.refs.hide_score_output.checked = phase.hide_score_output

            // Setting description in markdown editor
            self.simple_markdown_editor.value(self.phases[index].description || '')

            // Setting Tasks
            $(self.refs.multiselect)
                .dropdown('change values', _.map(self.phase_tasks, task => {
                    // renaming things to work w/ semantic UI multiselect
                    return {
                        value: task.value,
                        text: task.name,
                        name: task.name,
                        selected: true,
                    }
                }))
            // Setting Public Data
            if(self.phase_public_data[0] != null){
                $(self.refs.public_data_multiselect)
                    .dropdown('change values', _.map(self.phase_public_data, public_data => {
                        // renaming things to work w/ semantic UI multiselect
                        return {
                            value: public_data.value,
                            text: public_data.name,
                            name: public_data.name,
                            selected: true,
                        }
                    }))
            }
            // Setting Starting Kit
            if(self.phase_starting_kit[0] != null){
                $(self.refs.starting_kit_multiselect)
                    .dropdown('change values', _.map(self.phase_starting_kit, starting_kit => {
                        // renaming things to work w/ semantic UI multiselect
                        return {
                            //value: starting_kit.value, // Maybe need to grab from serializer?
                            value: starting_kit.value,
                            text: starting_kit.name,
                            name: starting_kit.name,
                            selected: true,
                        }
                    }))
            }

            self.show_modal()

            // make semantic multiselect sortable -- Sortable library imported in competitions/form.html
            Sortable.create($('.search.dropdown.multiple', self.refs.tasks_select_container)[0])
            Sortable.create($('.search.dropdown.multiple', self.refs.public_data_select_container)[0])
            Sortable.create($('.search.dropdown.multiple', self.refs.starting_kit_select_container)[0])

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
            // Get tasks order from DOM and order the task array by that.
            let tasks_from_dom = []
            $("#tasks_select_container a").each(function () {
                tasks_from_dom.push($(this).data("value"))
            })
            let sorted_phase_tasks = []
            tasks_from_dom.forEach( function(key) {
                let found = false;
                self.phase_tasks = self.phase_tasks.filter(function (item) {
                    if(!found && item['value'] == key){
                        sorted_phase_tasks.push(item)
                        found = true
                        return false
                    } else
                        return true
                })
            })
            self.phase_tasks = sorted_phase_tasks.slice()

            // Get public data from DOM
            let public_data_from_dom = []
            $("#public_data_select_container a").each(function () {
                public_data_from_dom.push($(this).data("value"))
            })
            let sorted_phase_public_data = []
            public_data_from_dom.forEach( function(key) {
                let found = false;
                self.phase_public_data = self.phase_public_data.filter(function (item) {
                    if(!found && item['value'] == key){
                        sorted_phase_public_data.push(item)
                        found = true
                        return false
                    } else
                        return true
                })
            })
            self.phase_public_data = sorted_phase_public_data.slice()

            // Get starting kit from DOM
            let starting_kit_from_dom = []
            $("#starting_kit_select_container a").each(function () {
                starting_kit_from_dom.push($(this).data("value"))
            })
            let sorted_phase_starting_kit = []
            starting_kit_from_dom.forEach( function(key) {
                let found = false;
                self.phase_starting_kit = self.phase_starting_kit.filter(function (item) {
                    if(!found && item['value'] == key){
                        sorted_phase_starting_kit.push(item)
                        found = true
                        return false
                    } else
                        return true
                })
            })
            self.phase_starting_kit = sorted_phase_starting_kit.slice()

            var data = get_form_data(self.refs.form)

            // Fill default start time if start time is empty
            if (data.start_time == "") {
                data.start_time = "00:00"
            } 
            // Change phase start format to ISO date format "Y-m-dTH:M:S"
            data.start = self.formatDateTo_Y_m_d_T_H_M_S(data.start_date + " " + data.start_time)

            
            if (data.end_date) {
                // Fill default end time if end time is empty
                if (data.end_time == "") {
                    data.end_time = "00:00"
                }
                data.end = self.formatDateTo_Y_m_d_T_H_M_S(data.end_date + " " + data.end_time)

                // Check: start date must not be after end date
                if (new Date(data.start) > new Date(data.end)) {
                    toastr.error("End date cannot be earlier than the start date. Please choose a valid date range.")
                    return
                }
            }else{
                // end date is set to null if it is not selected because it is optional in the form
                data.end = null
            }

            data.tasks = self.phase_tasks
            data.public_data = self.phase_public_data.length === 0 ? null : self.phase_public_data[0]
            data.starting_kit = self.phase_starting_kit.length === 0 ? null : self.phase_starting_kit[0]
            data.task_instances = []
            for(task of self.phase_tasks){
                data.task_instances.push({
                    order_index: data.task_instances.length,
                    task: task.value,
                })
            }
            data.auto_migrate_to_this_phase = $(self.refs.auto_migrate).prop('checked')
            data.hide_output = self.refs.hide_output.checked
            data.hide_prediction_output = self.refs.hide_prediction_output.checked
            data.hide_score_output = self.refs.hide_score_output.checked
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
