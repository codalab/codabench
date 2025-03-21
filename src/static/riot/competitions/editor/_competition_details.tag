<competition-details>
    <div class="ui form">

        <!--  Title  -->
        <div class="field required">
            <label>Title</label>
            <input type="text" ref="title" onchange="{form_updated}">
        </div>

        <!--  Logo  -->
        <div class="field required">
            <label>Logo</label>
            <!-- This is the SINGLE FILE with NO OTHER OPTIONS example -->
            <!-- In the future, we'll have this type AND a type that is pre-filled with nice options -->
            <label show="{ uploaded_logo }">
                Uploaded Logo: <a href="{ uploaded_logo }" target="_blank">{ uploaded_logo_name }</a>
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

        <!--  Description  -->
        <div class="field smaller-mde">
            <label>Description</label>
            <textarea class="markdown-editor" ref="comp_description" name="description" onchange="{form_updated}"></textarea>
        </div>

        <!--  Queue  -->
        <div class="field">
            <label>Queue</label>
            <select class="ui fluid search selection dropdown" ref="queue"></select>
        </div>

        <!--  Docker Image  -->
        <div class="field required">
            <label>Competition Docker Image</label>
            <input type="text" ref="docker_image" placeholder="Example: codalab/codalab-legacy:py37" onchange="{form_updated}">
        </div>

        <!--  Type  -->
        <div class="field">
            <label>Competition Type</label>
            <div ref="competition_type" class="ui selection dropdown">
                <input type="hidden" name="competition_type" value="{ data.competition_type || 'competition' }" onchange="{form_updated}">
                <div class="text">Competition</div>
                <i class="dropdown icon"></i>
                <div class="menu">
                    <div class="item" data-value="competition">Competition</div>
                    <div class="item" data-value="benchmark">Benchmark</div>
                </div>
            </div>
        </div>

        <!--  Reward  -->
        <div class="field">
            <label>Competition Reward</label>
            <input type="text" ref="reward" placeholder="Example: $1000 for the top participant" onchange="{form_updated}">
        </div>
        <!--  Contact Email  -->
        <div class="field">
            <label>Organizer Contact Email</label>
            <input type="email" ref="contact_email" placeholder="Example: email@example.com" onchange="{form_updated}">
        </div>
        <!--  Report  -->
        <div class="field">
            <label>Competition Report</label>
            <input type="text" ref="report" placeholder="Example: https://example.com/report.pdf" onchange="{form_updated}">
        </div>

        <!--  Fact Sheet  -->
        <div class="field smaller-mde">
            <label>Fact Sheet</label>
            <div class="row">
                <button class="ui basic blue button" onclick="{ add_question.bind(this, 'boolean') }">Boolean +</button>
                <button class="ui basic blue button" onclick="{ add_question.bind(this, 'text') }">Text +</button>
                <button class="ui basic blue button" onclick="{ add_question.bind(this, 'selection') }">Selection +</button>
            </div>
            <br>
            <form ref="comp_fact_sheet">
            <div class="fact-sheet-question" each="{question in fact_sheet_questions}">
                <div class="row" id="q-div-{question.id}">
                    <p  if="{ question.type === 'checkbox' }">Type: Boolean
                    <input type="hidden" name="type-{question.id}" value="checkbox">
                    </p>
                    <p if="{ question.type === 'text' }">Type: Text
                    <input type="hidden" name="type-{question.id}" value="text">
                    </p>
                    <p if="{ question.type === 'select' }">Type: Select
                    <input type="hidden" name="type-{question.id}" value="select">
                    </p>
                    <p>
                        <label style="font-size: 1em; font-weight: 500;" for="key-{question.id}">Key name: </label>
                        <a class="float-right" data-tooltip="Key is required for programmatic access to data. Best Practice is to have no whitespace." data-position="right center">
                            <i class="grey question circle icon"></i>
                        </a>
                        <input name="key-{question.id}" id="key-{question.id}" type="text" value="{question.key}">
                    </p>
                    <p if="{ question.type === 'select' }">
                        <label for="selection-{question.id}">Choices (Comma Separated): </label>
                        <input name="selection-{question.id}" id="selection-{question.id}" type="text" value="{question.selection.join()}">
                    </p>
                    <p>
                        <label for="is_on_leaderboard-{question.id}">Show On Leaderboard: </label>
                        <input type="hidden" name="is_on_leaderboard-{question.id}" value="false">
                        <input if="{question.is_on_leaderboard === 'true'}" type="checkbox" name="is_on_leaderboard-{question.id}" value="true" onchange="{form_updated}" checked>
                        <input if="{question.is_on_leaderboard !== 'true'}" type="checkbox" name="is_on_leaderboard-{question.id}" value="true" onchange="{form_updated}">
                    </p>
                    <p>
                        <label for="title-{question.id}">Display Name: </label>
                        <a class="float-right" data-tooltip="This is what the user sees when prompted for an answer, and the category name on the leaderboard." data-position="right center">
                            <i class="grey question circle icon"></i>
                        </a>
                        <input name="title-{question.id}" id="title-{question.id}" type="text" value="{question.title}">
                    </p>
                    <p>
                        <label for="is-required-{question.id}">Is Required:</label>
                        <input type="hidden" name="is_required-{question.id}" value="false">
                        <input if="{question.is_required === 'true'}" type="checkbox" name="is_required-{question.id}" value="true" onchange="{form_updated}" checked>
                        <input if="{question.is_required !== 'true'}" type="checkbox" name="is_required-{question.id}" value="true" onchange="{form_updated}">
                    </p>
                </div>
                <br>
                <button class="ui basic red button" onclick="{remove_question.bind(this, question.id)}">Remove</button>
            </div>
            </form>
        </div>

        <!--  Files Available  -->
        <div class="field smaller-mde">
            <label>
                Files Available
                <sup>
                    <a href="https://github.com/codalab/codabench/wiki/Yaml-Structure"
                       target="_blank"
                       data-tooltip="What's this?">
                        <i class="grey question circle icon"></i>
                    </a>
                </sup>
            </label>
            <div class="ui checkbox">
                <label>Make Programs Available</label>
                <input type="checkbox" ref="make_programs_available" onchange="{form_updated}">
            </div>
            <br>
            <div class="ui checkbox">
                <label>Make Input Data Available</label>
                <input type="checkbox" ref="make_input_data_available" onchange="{form_updated}">
            </div>
        </div>

        <!--  Detailed results  -->
        <div class="field">
            <label>Detailed Results</label>
            <div class="ui checkbox">
                <label>Enable Detailed Results</label>
                <input type="checkbox" ref="detailed_results" onchange="{form_updated}">
            </div>
            <sup>
                <a href="https://github.com/codalab/competitions-v2/wiki/Detailed-Results-and-Visualizations"
                   target="_blank"
                   data-tooltip="What's this?">
                    <i class="grey question circle icon"></i>
                </a>
            </sup>
            <br>
            <div class="ui checkbox">
                <label>Show Detailed Results in submission pannel</label>
                <input type="checkbox" ref="show_detailed_results_in_submission_panel" onchange="{form_updated}">
            </div>
            <sup>
                <span data-tooltip="If checked and detailed results are enabled, participants can see detailed results in submission panel"
                          data-inverted=""
                          data-position="bottom center">
                    <i class="help icon circle"></i>
                </span>
            </sup>
            <br>
            <div class="ui checkbox">
                <label>Show Detailed Results in leaderboard</label>
                <input type="checkbox" ref="show_detailed_results_in_leaderboard" onchange="{form_updated}">
            </div>
            <sup>
                <span data-tooltip="If checked and detailed results are enabled, participants can see detailed results in leaderboard"
                          data-inverted=""
                          data-position="bottom center">
                    <i class="help icon circle"></i>
                </span>
            </sup>
        </div>

        <!--  Auto Run submissions  -->
        <div class="field">
            <label>Submission execution</label>
            <div class="ui checkbox">
                <label>Auto-run submissions</label>
                <input type="checkbox" ref="auto_run_submissions" onchange="{form_updated}">
            </div>
            <sup>
                <span data-tooltip="If unchecked, organizers will have to manually run each submission"
                          data-inverted=""
                          data-position="bottom center">
                    <i class="help icon circle"></i>
                </span>
            </sup>
        </div>

        <!--  Public submissions  -->
        <div class="field">
            <label>Public Submissions</label>
            <div class="ui checkbox">
                <label>Participants can make submission public</label>
                <input type="checkbox" ref="can_participants_make_submissions_public" onchange="{form_updated}">
            </div>
            <sup>
                <span data-tooltip="If unchecked, participants cannot make their submissions public from submission panel"
                          data-inverted=""
                          data-position="bottom center">
                    <i class="help icon circle"></i>
                </span>
            </sup>
        </div>

        <!--  Forum  -->
        <div class="field">
            <label>Forum</label>
            <div class="ui checkbox">
                <label>Enable Competition Forum</label>
                <input type="checkbox" ref="forum_enabled" onchange="{form_updated}">
            </div>
            <sup>
                <span data-tooltip="If unchecked, organizers and participants cannot see competition forum"
                          data-inverted=""
                          data-position="bottom center">
                    <i class="help icon circle"></i>
                </span>
            </sup>
        </div>

        
    </div>

    <script>
        var self = this
        self.fact_sheet_questions = []
        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.data = {}
        self.is_editing_competition = false
        // We temporarily store this to display it nicely to the user, could be a behavior we break out into its own
        // component later!
        self.logo_file_name = ''

        self.one("mount", function () {
            // Set placeholder here so we can have multiple lines
            $(self.refs.comp_fact_sheet).attr('placeholder', '{\n  "key": ["value1","value2",true,false]\n  "leave_blank_to_accept_any": ""\n}\n')
            self.markdown_editor = create_easyMDE(self.refs.comp_description)
            $('.ui.checkbox', self.root).checkbox({
                onChange: self.form_updated
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

            $(self.refs.competition_type).dropdown({
                onChange: self.form_updated,
            })
            $(self.refs.queue).dropdown({
                // Note: Passing `public=true` so default behavior is users can search for public queues
                apiSettings: {
                    url: `${URLS.API}queues/?search={query}&public=true`,
                    cache: false
                },
                clearable: true,
                minCharacters: 2,
                fields: {
                    remoteValues: 'results',
                    value: 'id',
                },
                maxResults: 5,
                onChange: self.form_updated
            })
            self.update()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.form_updated = function () {
            var is_valid = true

            // NOTE: logo is excluded here because it is converted to 64 upon changing and set that way
            self.data["title"] = self.refs.title.value
            self.data["description"] = self.markdown_editor.value()
            self.data["queue"] = self.refs.queue.value
            self.data["enable_detailed_results"] = self.refs.detailed_results.checked
            self.data["show_detailed_results_in_submission_panel"] = self.refs.show_detailed_results_in_submission_panel.checked
            self.data["show_detailed_results_in_leaderboard"] = self.refs.show_detailed_results_in_leaderboard.checked
            self.data["auto_run_submissions"] = self.refs.auto_run_submissions.checked
            self.data["can_participants_make_submissions_public"] = self.refs.can_participants_make_submissions_public.checked
            self.data["forum_enabled"] = self.refs.forum_enabled.checked
            self.data["make_programs_available"] = self.refs.make_programs_available.checked
            self.data["make_input_data_available"] = self.refs.make_input_data_available.checked
            self.data["docker_image"] = $(self.refs.docker_image).val()
            self.data["competition_type"] = $(self.refs.competition_type).dropdown('get value')
            self.data['fact_sheet'] = self.serialize_fact_sheet_questions()
            self.data['reward'] = $(self.refs.reward).val()
            self.data['contact_email'] = $(self.refs.contact_email).val()
            self.data['report'] = $(self.refs.report).val()
            if (self.data.fact_sheet === false){
                is_valid = false
            }

            // Require title, logo is optional IF we are editing -- will just keep the old one if
            // a new one is not provided
            if (!self.data['title'] || !self.data['docker_image'] || (!self.data['logo'] && !self.is_editing_competition)) {
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

        self.add_question = (type) => {
            let current_id = 0
            if(self.fact_sheet_questions[0] !== undefined) {
                current_id = self.fact_sheet_questions[self.fact_sheet_questions.length - 1].id + 1
            }
            if(type === 'boolean'){
                self.fact_sheet_questions.push({
                    "id": current_id,
                    "label": "",
                    "type": "checkbox"
                })
            }
            else if(type === 'text'){
                self.fact_sheet_questions.push({
                    "id": current_id,
                    "label": "",
                    "type": "text"
                })
            }
            else if(type === 'selection'){
                self.fact_sheet_questions.push({
                    "id": current_id,
                    "label": "",
                    "type": "select",
                    "selection": []
                })
            }
            self.update()
            $(':input', self.refs.comp_fact_sheet).not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keyup', self.form_updated)
            })
        }

        self.remove_question = function (id) {
            self.fact_sheet_questions = self.fact_sheet_questions.filter(q => q.id !== id)
            self.update()
            self.form_updated()
        }

        self.serialize_fact_sheet_questions = function (){
            let form = $(self.refs.comp_fact_sheet).children()
            let form_json = {}
            for(question of form){
                let q_serialized = $(question).find(":input").serializeArray()
                let question_key = q_serialized[1].value
                form_json[question_key] = {}
                if(q_serialized[0].value === "checkbox"){
                    form_json[question_key]['selection'] = [true, false]
                } else if(q_serialized[0].value === "text") {
                    form_json[question_key]['selection'] = ""
                }
                for(entry of q_serialized){
                    if(entry.name.split('-')[0] === 'selection') {
                        let selection = entry.value.split(',')
                        selection = selection.map(s => s.trim()).filter(s => s !== '')
                        form_json[question_key][entry.name.split('-')[0]] = selection
                    } else if (entry.name.split('-')[0] === 'key'){
                        // Check to make sure key isn't empty
                        if(!entry.value){
                            return false
                        }
                        form_json[question_key][entry.name.split('-')[0]] = entry.value
                    } else {
                        form_json[question_key][entry.name.split('-')[0]] = entry.value
                    }
                }
                if(form_json[question_key]['type'] === 'select' && form_json[question_key]['is_required'] === 'false'){
                    form_json[question_key]['selection'].unshift('')
                }
            }
            if(form_json.length === 0){
                return null
            }
            return form_json
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
            self.refs.detailed_results.checked = competition.enable_detailed_results
            self.refs.show_detailed_results_in_submission_panel.checked = competition.show_detailed_results_in_submission_panel
            self.refs.show_detailed_results_in_leaderboard.checked = competition.show_detailed_results_in_leaderboard
            self.refs.auto_run_submissions.checked = competition.auto_run_submissions
            self.refs.can_participants_make_submissions_public.checked = competition.can_participants_make_submissions_public
            self.refs.forum_enabled.checked = competition.forum_enabled
            self.refs.make_programs_available.checked = competition.make_programs_available
            self.refs.make_input_data_available.checked = competition.make_input_data_available
            $(self.refs.docker_image).val(competition.docker_image)
            $(self.refs.reward).val(competition.reward)
            $(self.refs.contact_email).val(competition.contact_email)
            $(self.refs.report).val(competition.report)
            if(competition.fact_sheet !== null){
                for(question in competition.fact_sheet){
                    var q_json = competition.fact_sheet[question]
                    q_json.id = self.fact_sheet_questions.length
                    if(q_json.type === "select"){
                        q_json.selection = q_json.selection.filter(s => s !== "")
                    }
                    self.fact_sheet_questions.push(q_json)
                }
            }
            self.update()
            self.form_updated()
            // Put dropdown 'set selected' here so it doesn't trigger on_change:form_updated() before fact_sheet_questions is set
            $(self.refs.competition_type).dropdown('set selected', competition.competition_type)
            // Form change events
            $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keyup', self.form_updated)
            })
        })
        CODALAB.events.on('update_codemirror', () => {
            self.markdown_editor.codemirror.refresh()
        })
    </script>
    <style>
        .fact-sheet-question {
            border: 1px solid #dcdcdcdc;
            background-color: white;
            padding: 1.5em;
        }
    </style>
</competition-details>
