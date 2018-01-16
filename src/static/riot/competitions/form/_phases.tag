<competition-phases>
    <button class="ui primary button modal-button" ref="modal_button">
        <i class="add circle icon"></i> Create new phase
    </button>

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
    </script>
</competition-phases>