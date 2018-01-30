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
    <div class="ui modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Edit phase
        </div>
        <div class="content">
            <div class="ui top pointing secondary menu">
                <a class="active item" data-tab="phase_details">Phase details</a>
                <a class="item" data-tab="phase_datasets">Datasets</a>
            </div>

            <form class="ui form" ref="form">
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

                <div class="ui bottom tab" data-tab="phase_datasets">
                    <div class="field required">
                        <a href="{ URLS.DATASET_MANAGEMENT }" class="ui fluid large primary button" target="_blank">
                            <i class="icon sign out"></i> Manage Datasets
                        </a>
                    </div>

                    <div class="three fields">
                        <div class="field">
                            <label>
                                Input Data
                                <span data-tooltip="Something useful to know...!" data-inverted="" data-position="bottom center"><i class="help icon circle"></i></span>
                            </label>

                            <div class="ui fluid left icon labeled input search">
                                <i class="search icon"></i>
                                <input type="text" name="input_data" class="prompt">
                                <div class="results"></div>
                            </div>
                        </div>
                        <div class="field">
                            <label>
                                Reference Data
                                <span data-tooltip="Something useful to know...!" data-inverted="" data-position="bottom center"><i class="help icon circle"></i></span>
                            </label>
                            <div class="ui fluid left icon labeled input search">
                                <i class="search icon"></i>
                                <input type="text" name="reference_data" class="prompt">
                                <div class="results"></div>
                            </div>
                        </div>
                        <div class="field required">
                            <label>
                                Scoring Program
                                <span data-tooltip="Something useful to know...!" data-inverted="" data-position="bottom center"><i class="help icon circle"></i></span>
                            </label>
                            <div class="ui fluid left icon labeled input search">
                                <i class="search icon"></i>
                                <input type="text" name="scoring_program" class="prompt">
                                <div class="results"></div>
                            </div>
                        </div>
                    </div>
                    <div class="three fields">
                        <div class="field">
                            <label>
                                Ingestion Program
                                <span data-tooltip="Something useful to know...!" data-inverted="" data-position="bottom center"><i class="help icon circle"></i></span>
                            </label>
                            <div class="ui fluid left icon labeled input search">
                                <i class="search icon"></i>
                                <input type="text" name="ingestion_program" class="prompt">
                                <div class="results"></div>
                            </div>
                        </div>
                        <div class="field">
                            <label>
                                Public Data
                                <span data-tooltip="Something useful to know...!" data-inverted="" data-position="bottom center"><i class="help icon circle"></i></span>
                            </label>
                            <div class="ui fluid left icon labeled input search">
                                <i class="search icon"></i>
                                <input type="text" name="public_data" class="prompt">
                                <div class="results"></div>
                            </div>
                        </div>
                        <div class="field">
                            <label>
                                Starting Kit
                                <span data-tooltip="Something useful to know...!" data-inverted="" data-position="bottom center"><i class="help icon circle"></i></span>
                            </label>
                            <div class="ui fluid left icon labeled input search">
                                <i class="search icon"></i>
                                <input type="text" name="starting_kit" class="prompt">
                                <div class="results"></div>
                            </div>
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
        self.has_initialized_calendars = false
        self.form_is_valid = false
        self.phases = [
            /*{
                name: "Test",
                start: "1/1/1",
                description: "asdfasdf",
                scoring_program: "a"
            }*/
        ]
        self.selected_phase_index = undefined

        self.one("mount", function () {
            // awesome markdown editor
            self.simple_markdown_editor = new SimpleMDE({
                element: self.refs.description,
                autoRefresh: true,
                forceSync: true
            })

            // Form change events
            $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keyup', self.form_updated)
            })

            // data search
            var content = [
                {title: 'Andorra'}
            ];
            $('.ui.search')
                .search({
                    source: content,
                    onSelect: self.form_updated
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
                    if (!phase.name || !phase.start || !phase.description || !phase.scoring_program) {
                        is_valid = false
                    }
                })
            }

            CODALAB.events.trigger('competition_is_valid_update', 'phases', is_valid)

            if (is_valid) {
                self.phases.forEach(function (phase, i) {
                    // Since we have valid data, let's attach our "index" to the phaases
                    phase.index = i

                    // having an empty "end" causes problems with DRF validation, remove that
                    if(!phase.end) {
                        delete phase.end
                    }
                })

                CODALAB.events.trigger('competition_data_update', {phases: self.phases})
            }

            self.form_check_is_valid()
            self.update()
        }

        self.form_check_is_valid = function () {
            // This checks our current form to make sure it's valid
            var data = get_form_data(self.refs.form)
            console.log(data)
            // All of these must be present
            self.form_is_valid = !!data.name && !!data.start && !!data.description && !!data.scoring_program

            console.log("form is valid: " + self.form_is_valid)
        }

        /*self.get_form_data = function() {
            // Wrapper around normal get form data to also include simplemde
            var data = get_form_data(self.refs.form)
            //data.description = self.simple_markdown_editor.value()
            return data
        }*/

        self.clear_form = function () {
            self.selected_phase_index = undefined

            $(':input', self.refs.form).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
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

            set_form_data(self.phases[index], self.refs.form)

            // stupid simplemde special case
            self.simple_markdown_editor.value(self.phases[index].description)

            self.show_modal()
        }

        self.delete_phase = function (index) {
            if (self.phases.length == 1) {
                toastr.error("Cannot delete, you need at least one phase")
            } else {
                if (confirm("Are you sure you want to delete '" + self.phases[page_index].name + "'?")) {
                    self.phases.splice(page_index, 1)
                    self.form_updated()
                }
            }
        }

        self.save = function () {
            var data = get_form_data(self.refs.form)
            console.log(data)
            if (!self.selected_phase_index) {
                self.phases.push(data)
                self.clear_form()
                self.close_modal()
            } else {
                // We have a selected phase, do an update instead of a create
            }
        }
    </script>
    <style>
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