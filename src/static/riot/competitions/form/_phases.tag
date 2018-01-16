<competition-phases>
    <button class="ui primary button modal-button" ref="modal_button">
        <i class="add circle icon"></i> Create new phase
    </button>

    <div class="ui top vertical centered segment grid">

        <div class="ten wide column">

            <div class="ui one cards">
                <a each="{phase, index in phases}" class="green card">
                    <div class="content">
                        <i class="right floated chevron down icon" show="{ index + 1 < phases.length }" onclick="{ move_phase_down.bind(this, index) }"></i>
                        <i class="right floated chevron up icon" show="{ index > 0 }" onclick="{ move_phase_up.bind(this, index) }"></i>
                        <div class="header">{ phase.name }</div>
                        <div class="description">
                            { phase.description }
                        </div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>

                <!--
                <a class="red card">
                    <div class="content">
                        <i class="right floated chevron down icon"></i>
                        <i class="right floated chevron up icon"></i>
                        <div class="header">How to determine something</div>
                        <div class="description">
                            Matthew is an interior designer living in New York.
                        </div>
                    </div>
                    <div class="extra content">
                                        <span class="left floated like">
                                            <i class="edit icon"></i>
                                            Edit
                                        </span>
                        <span class="right floated star">
                                            <i class="delete icon"></i>
                                            Delete
                                        </span>
                    </div>
                </a>

                <a class="orange card">
                    <div class="content">
                        <i class="right floated chevron down icon"></i>
                        <i class="right floated chevron up icon"></i>
                        <div class="header">Testing something</div>
                        <div class="description">
                            Matthew is an interior designer living in New York.
                        </div>
                    </div>
                    <div class="extra content">
                                        <span class="left floated like">
                                            <i class="edit icon"></i>
                                            Edit
                                        </span>
                        <span class="right floated star">
                                            <i class="delete icon"></i>
                                            Delete
                                        </span>
                    </div>
                </a>-->
            </div>
        </div>
    </div>
    <div class="ui modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Edit phase
        </div>
        <div class="content">

            <div class="ui form">
                <div class="field required">
                    <label>Name</label>
                    <input/>
                </div>

                <div class="two fields">
                    <div class="ui calendar field required" ref="calendar">
                        <label>Start</label>
                        <div class="ui input left icon">
                            <i class="calendar icon"></i>
                            <input type="text">
                        </div>
                    </div>

                    <div class="ui calendar field" ref="calendar">
                        <label>End</label>
                        <div class="ui input left icon">
                            <i class="calendar icon"></i>
                            <input type="text">
                        </div>
                    </div>
                </div>

                <div class="field required smaller-mde">
                    <label>Description</label>
                    <textarea class="markdown-editor" ref="description"></textarea>
                </div>

                <div class="three fields">
                    <div class="field">
                        <label>Input Data</label>
                        <select class="ui dropdown">
                            <option value="test">Test</option>
                            <option value="test">Test</option>
                        </select>
                    </div>
                    <div class="field">
                        <label>Reference Data</label>
                        <select class="ui dropdown">
                            <option value="test">Test</option>
                            <option value="test">Test</option>
                        </select>
                    </div>
                    <div class="field required">
                        <label>Scoring Program</label>
                        <select class="ui dropdown">
                            <option value="test">Test</option>
                            <option value="test">Test</option>
                        </select>
                    </div>
                </div>
                <div class="three fields">
                    <div class="field">
                        <label>Ingestion Program</label>
                        <select class="ui dropdown">
                            <option value="test">Test</option>
                            <option value="test">Test</option>
                        </select>
                    </div>
                    <div class="field">
                        <label>Public Data</label>
                        <select class="ui dropdown">
                            <option value="test">Test</option>
                            <option value="test">Test</option>
                        </select>
                    </div>
                    <div class="field">
                        <label>Starting Kit</label>
                        <select class="ui dropdown">
                            <option value="test">Test</option>
                            <option value="test">Test</option>
                        </select>
                    </div>
                </div>

            </div>
        </div>
        <div class="actions">
            <div class="ui button">Cancel</div>
            <div class="ui button primary">Save</div>
        </div>
    </div>

    <script>
        var self = this

        self.has_initialized_calendars = false
        self.phases = [
            {name: "First phase"},
            {name: "Second phase"},
            {name: "Third phase"}
        ]

        self.one("mount", function () {
            // modals
            $(self.refs.modal_button).click(function () {
                $(self.refs.modal).modal('show')

                // Have to initialize calendars here (instead of on mount) because they don't exist yet
                if(!self.has_initialized_calendars) {
                    $(self.refs.calendar).calendar({
                        type: 'date',
                        popupOptions: {
                            position: 'bottom left',
                            lastResort: 'bottom left',
                            hideOnScroll: false
                        }
                    })

                    self.has_initialized_calendars = true
                }
            })

            // awesome markdown editor
            $(self.refs.description).each(function (i, ele) {
                new SimpleMDE({element: ele})
            })

            // datetime pickers
            $(self.refs.calendar).calendar({
                type: 'date',
                popupOptions: {
                    position: 'bottom left',
                    lastResort: 'bottom left',
                    hideOnScroll: false
                }
            })
        })

        self.move_phase_up = function(phase_index) {
            self.move_phase(phase_index, -1)
        }

        self.move_phase_down = function(phase_index) {
            self.move_phase(phase_index, 1)
        }
        self.move_phase = function(phase_index, offset){
            var phase_to_move = self.phases[phase_index]

            // Remove 1 item
            self.phases.splice(phase_index, 1)

            // Add 1 item offset up OR down
            self.phases.splice(phase_index + offset, 0, phase_to_move)

            self.update()
        }
    </script>
</competition-phases>