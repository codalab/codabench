<competition-details>
    <div class="ui form">
        <div class="field required">
            <label>Title</label>
            <input ref="title">
        </div>

        <div class="field required">
            <label>Logo</label>
            <!-- This is the SINGLE FILE with NO OTHER OPTIONS example -->
            <!-- In the future, we'll have this type AND a type that is pre-filled with nice options -->
            <label show="{ uploaded_logo }">
                Uploaded Logo: <a href="{ uploaded_logo }">{ uploaded_logo_name }</a>
            </label>
            <div class="ui left action file input">
                <button class="ui icon button" onclick="document.getElementById('form_file_logo').click()">
                    <i class="attach icon"></i>
                </button>
                <input id="form_file_logo" type="file" ref="logo" accept="image/*">

                <!-- Just showing the file after it is uploaded -->
                <input value="{ logo_file_name }" readonly onclick="document.getElementById('form_file_logo').click()">
            </div>
        </div>
        <div class="field smaller-mde">
            <label>Description</label>
            <textarea class="markdown-editor" ref="comp_description" name="description"></textarea>
        </div>
        <div class="field">
            <label>Queue</label>
            <select class="ui fluid search selection dropdown" ref="queue"></select>
        </div>

    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.data = {}
        self.is_editing_competition = false

        // We temporarily store this to display it nicely to the user, could be a behavior we break out into its own
        // component later!
        self.logo_file_name = ''

        self.one("mount", function () {
            self.markdown_editor = create_easyMDE(self.refs.comp_description)

            // Form change events
            $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keyup', self.form_updated)
            })

            // Draw in logo filename as it's changed
            $(self.refs.logo).change(function () {
                self.logo_file_name = self.refs.logo.value.replace(/\\/g, '/').replace(/.*\//, '')
                self.update()
                getBase64(this.files[0]).then(function (data) {
                    self.data['logo'] = JSON.stringify({file_name: self.logo_file_name, data: data})
                    self.form_updated()
                })
                self.form_updated()
            })

            $(self.refs.queue).dropdown({
                // Note: Passing `public=true` so default behavior is users can search for public queues
                apiSettings: {
                    url: `${URLS.API}queues/?search={query}&public=true`,
                },
                clearable: true,
                minCharacters: 2,
                fields: {
                    remoteValues: 'results',
                    value: 'id',
                },
                maxResults: 5,
                onChange: (value, title) => {
                    self.form_updated()
                }
            })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.form_updated = function () {
            var is_valid = true

            // NOTE: logo is excluded here because it is converted to 64 upon changing and set that way
            self.data['title'] = self.refs.title.value
            self.data['description'] = self.markdown_editor.value()
            self.data['queue'] = self.refs.queue.value

            // Require title, logo is optional IF we are editing -- will just keep the old one if
            // a new one is not provided
            if (!self.data['title'] || (!self.data['logo'] && !self.is_editing_competition)) {
                is_valid = false
            }

            CODALAB.events.trigger('competition_is_valid_update', 'details', is_valid)

            if (is_valid) {
                // If we don't have logo data AND we're editing, put in empty data (otherwise
                // we send garbage to the backend)
                if (!self.data['logo'] && self.is_editing_competition) {
                    self.data['logo'] = undefined
                }
                CODALAB.events.trigger('competition_data_update', self.data)
            }
        }

        self.filter_queues = function (filters) {
            filters = filters || {}
            _.defaults(filters, {
                search: $(self.refs.queue_search).val(),
                page: 1,
            })
            self.page = filters.page
            self.get_available_queues(filters)
        }

        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_loaded', function (competition) {
            self.is_editing_competition = true
            self.refs.title.value = competition.title
            self.markdown_editor.value(competition.description || '')

            // Value comes like c:/fakepath/file_name.txt -- cut out everything but file_name.txt
            self.uploaded_logo_name = competition.logo.replace(/\\/g, '/').replace(/.*\//, '')
            self.uploaded_logo = competition.logo
            if (competition.queue) {
                $(self.refs.queue)
                    .dropdown('set text', competition.queue.name)
                    .dropdown('set value', competition.queue.id)
            }
            self.form_updated()
        })
        CODALAB.events.on('update_codemirror', () => {
            self.markdown_editor.codemirror.refresh()
        })
    </script>
</competition-details>
