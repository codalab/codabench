<competition-participation>
    <form class="ui form">
        <div class="field required">
            <label>Terms</label>
            <textarea class="markdown-editor" ref="terms" name="terms"></textarea>
        </div>
        <div class="field">
            <div class="ui checkbox">
                <input type="checkbox" name="registration_auto_approve" ref="registration_auto_approve" onchange="{form_updated}">
                <label>Auto approve registration requests
                    <span data-tooltip="If left unchecked, registration requests must be manually approved by the competition creator or collaborators"
                          data-inverted=""
                          data-position="bottom center">
                    <i class="help icon circle"></i></span>
                </label>
            </div>
        </div>
        <div class="field">
            <div class="ui checkbox">
                <input type="checkbox" name="allow_robot_submissions" ref="allow_robot_submissions" onchange="{form_updated}">
                <label>Allow robot submissions
                    <span data-tooltip="If left unchecked, robot users will have to be manually approved by the competition creator or collaborators. This can be changed later."
                          data-inverted=""
                          data-position="bottom center">
                    <i class="help icon circle"></i></span>
                </label>
            </div>
        </div>
    </form>

    <script>
        let self = this

        self.data = {}

        self.on('mount', () => {
            self.markdown_editor = create_easyMDE(self.refs.terms)

            $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keyup', self.form_updated)
            })
        })

        self.form_updated = () => {
            self.data.registration_auto_approve = $(self.refs.registration_auto_approve).prop('checked')
            self.data.allow_robot_submissions = $(self.refs.allow_robot_submissions).prop('checked')
            self.data.terms = self.markdown_editor.value()

            let is_valid = !!self.data.terms

            CODALAB.events.trigger('competition_is_valid_update', 'participation', is_valid)

            if (is_valid) {
                CODALAB.events.trigger('competition_data_update', self.data)
            }
        }

        CODALAB.events.on('competition_loaded', function (competition) {
            self.refs.registration_auto_approve.checked = competition.registration_auto_approve
            self.refs.allow_robot_submissions.checked = competition.allow_robot_submissions
            self.markdown_editor.value(competition.terms || '')
            self.markdown_editor.codemirror.refresh()
            self.update()
            self.form_updated()
        })

        CODALAB.events.on('update_codemirror', () => {
            self.markdown_editor.codemirror.refresh()
        })
    </script>
</competition-participation>
