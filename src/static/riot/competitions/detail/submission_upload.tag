<submission-upload>
    <div class="ui sixteen wide column submission-container"
         show="{_.get(selected_phase, 'status') === 'Current' || opts.is_admin}">

        <div class="submission-form">
            <h1>Submission upload</h1>
            <form class="ui form coda-animated {error: errors}" ref="form" enctype="multipart/form-data">
                <div class="submission-form" if="{ opts.fact_sheet !== null }">
                    <h2>Metadata or Fact Sheet</h2>
                    <div class="submission-form-question" each="{ question in opts.fact_sheet }">
                        <span if="{ question.type === 'text' }">
                            <label for="{ question.label }">{ question.label }:</label>
                            <input type="text" name="{ question.label }">
                        </span>
                        <span if="{ question.type === 'checkbox' }">
                            <label for="{ question.label }">{ question.label }:</label>
                            <input type="hidden" name="{ question.label }" value="false">
                            <input type="checkbox" name="{ question.label }" value="true">
                        </span>
                        <span if="{ question.type == 'select' }">
                            <label for="{ question.label }">{ question.label }:</label>
                            <select name="{ question.label }">
                                <option each="{ selection_opt in question.selection }" value="{ selection_opt }">{ selection_opt }</option>
                            </select>
                        </span>
                    </div>
                </div>
                <label for="selected_tasks">Selected Tasks</label>
                <input type="text" name="selected_tasks" id="selected_tasks" ref="selected_tasks">
                <input-file name="data_file" ref="data_file" error="{errors.data_file}" accept=".zip"></input-file>
            </form>
        </div>

        <div class="ui indicating progress" ref="progress">
            <div class="bar">
                <div class="progress">{ upload_progress }%</div>
            </div>
        </div>

        <div class="ui styled fluid accordion submission-output-container {hidden: _.isEmpty(selected_submission) || selected_phase.hide_output}"
             ref="accordion">
            <div class="title">
                <i class="dropdown icon"></i>
                {(status_received && selected_submission.filename) ? "Running " + selected_submission.filename :
                "Uploading..."}
            </div>
            <div class="ui basic segment">
                <div class="content">
                    <div id="submission-output" class="ui" ref="submission-output">
                        <div class="header">Output</div>
                        <div class="content">
                            <div if="{!ingestion_during_scoring}">
                                <div if="{_.isEmpty(children)}">
                                    <log_window lines="{lines[selected_submission.id]}"
                                                data="{datasets[selected_submission.id]}"
                                                ref="submission_output"
                                                detailed_result_url="{detailed_result_urls[selected_submission.id]}"
                                                show_graph="{opts.competition.enable_detailed_results}"></log_window>
                                    <div class="ui checkbox" ref="autoscroll_checkbox">
                                        <input type="checkbox" checked/>
                                        <label>Autoscroll Output</label>
                                    </div>
                                </div>
                                <div if="{children}">
                                    <div class="ui secondary menu">
                                        <div each="{child, index in children}" class="item {active: index === 0}"
                                             data-tab="child{child}_tab">
                                            Submission ID: { child }
                                        </div>
                                    </div>
                                    <div each="{child, index in children}" class="ui tab {active: index === 0}"
                                         data-tab="child{child}_tab">
                                        <log_window lines="{lines[child]}"
                                                    data="{datasets[child]}"
                                                    detailed_result_url="{detailed_result_urls[child]}"
                                                    show_graph="{opts.competition.enable_detailed_results}">
                                        </log_window>
                                    </div>
                                </div>
                            </div>
                            <div if="{ingestion_during_scoring}">
                                <div if="{_.isEmpty(children)}">
                                    <log_window lines="{lines[selected_submission.id]}"
                                                data="{datasets[selected_submission.id]}"
                                                split_logs="{true}"
                                                detailed_result_url="{detailed_result_urls[selected_submission.id]}"
                                                show_graph="{opts.competition.enable_detailed_results}"></log_window>
                                </div>
                                <div if="{children}">
                                    <div class="ui secondary menu">
                                        <div each="{child, index in children}" class="item {active: index === 0}"
                                             data-tab="child{child}_tab">
                                            Submission ID: { child }
                                        </div>
                                    </div>
                                    <div each="{child, index in children}" class="ui tab {active: index === 0}"
                                         data-tab="child{child}_tab">
                                        <log_window lines="{lines[child]}"
                                                    data="{datasets[child]}"
                                                    split_logs="{true}"
                                                    detailed_result_url="{detailed_result_urls[child]}"
                                                    show_graph="{opts.competition.enable_detailed_results}"></log_window>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this

        self.mixin(ProgressBarMixin)

        self.chart = undefined
        self.errors = {}
        self.lines = {}
        self.detailed_result_urls = {}
        self.selected_submission = {}
        self.status_received = false
        self.display_output = false
        self.autoscroll_selected = true
        self.ingestion_during_scoring = undefined

        self.children = []
        self.children_statuses = {}
        self.datasets = {}

        self.one('mount', function () {
            $('.dropdown', self.root).dropdown()
            let segment = $('.submission-output-container .ui.basic.segment')
            $('.ui.accordion', self.root).accordion({
                onOpen: () => segment.show(),
                onClose: () => segment.hide(),
            })

            // File upload handler
            $(self.refs.data_file.refs.file_input).on('change', self.check_can_upload)
            self.setup_autoscroll()
            self.setup_websocket()
        })

        self.setup_autoscroll = function () {
            if (!self.refs.autoscroll_checkbox) {
                return
            }
            $(self.refs.autoscroll_checkbox).checkbox({
                onChecked: function () {
                    self.autoscroll_selected = true;
                    self.autoscroll_output()
                },
                onUnchecked: function () {
                    self.autoscroll_selected = false;
                },
            })

            self.set_checkbox()

            $(self.refs.submission_output).scroll(function () {
                var output = self.refs.submission_output
                self.autoscroll_selected = output.scrollTop === output.scrollHeight - Math.ceil($(output).height()) - 30
                self.set_checkbox()
            })

        }
        self.setup_websocket = function () {
            // Submission stream handler
            var url = new URL('/submission_output/', window.location.href);
            url.protocol = url.protocol.replace('http', 'ws');
            var options = {
                automaticOpen: false
            }
            self.ws = new ReconnectingWebSocket(url, null, options)
            self.ws.addEventListener("message", function (event) {
                self.autoscroll_output()
                let event_data = JSON.parse(event.data)
                switch (event_data.type) {
                    case 'catchup':
                        let detailed_result_url = ''
                        _.forEach(_.compact(event_data.data.split('\n')), data => {
                            data = JSON.parse(data)
                            if (data.kind === 'detailed_result_update') {
                                detailed_result_url = data.result_url
                            } else {
                                self.handle_websocket(event_data.submission_id, data)
                            }
                        })
                        self.detailed_result_urls[submission_id] = detailed_result_url
                        self.update()
                        break
                    case 'message':
                        self.handle_websocket(event_data.submission_id, event_data.data)
                        break
                }
            })
            self.ws.open()

        }

        self.handle_websocket = function (submission_id, data) {
            submission_id = _.toNumber(submission_id)
            if (self.selected_submission.id !== submission_id && !_.includes(self.children, submission_id)) {
                // not a submission we care about
                return
            }
            let done_states = ['Finished', 'Cancelled', 'Unknown', 'Failed']
            let message = data.message
            let kind = data.kind
            if (kind === 'status_update') {
                if (submission_id !== self.selected_submission.id) {
                    self.children_statuses[submission_id] = data.status
                    if (_.every(self.children, child => _.includes(done_states, self.children_statuses[child]))) {
                        CODALAB.events.trigger('submission_status_update', {
                            submission_id: self.selected_submission.id,
                            status: 'Finished'
                        })
                    }
                }
                self.status_received = true
                CODALAB.events.trigger('submission_status_update', {submission_id: submission_id, status: data.status})
            } else if (kind === 'child_update') {
                self.children.push(data.child_id)
                self.update()
                $('.menu .item', self.root).tab()
            } else if (kind === 'detailed_result_update') {
                self.detailed_result_urls[submission_id] = data.result_url
                self.update()
            } else {
                try {
                    message = JSON.parse(message);
                    if (message.type === "plot") {
                        self.add_graph_data_point(submission_id, message.value)
                    } else if (message.type === "message") {
                        self.add_line(submission_id, kind, message.message)
                    }
                } catch (e) {
                    // This is the default way to handle socket messages (just print them),  but can be sent as a json message as well
                    self.add_line(submission_id, kind, message)
                }
            }
        }

        self.pull_logs = function () {
            if (_.isEmpty(self.lines) && !_.isEmpty(self.selected_submission)) {
                self.ws.send(JSON.stringify({
                    submission_ids: _.concat(self.selected_submission.id, _.get(self.selected_submission, 'children', []))
                }))
            }
        }

        self.set_checkbox = function () {
            $(self.refs.autoscroll_checkbox).children('input').prop('checked', self.autoscroll_selected)
        }

        self.add_graph_data_point = function (submission_id, value) {
            if (!self.datasets[submission_id]) {
                self.datasets[submission_id] = {
                    label: submission_id,
                    data: [],
                    steppedLine: true,
                    backgroundColor: 'rgba(0,187,187,0.3)',
                    pointBackgroundColor: 'rgba(0,187,187,0.8)',
                    borderColor: 'rgba(0,187,187,0.8)',
                    fill: true,
                }
            }

            self.datasets[submission_id].data.push({x: value[0], y: value[1]})
        }

        self.add_line = function (submission_id, kind, message) {
            if (message === undefined) {
                message = '\n'
            }

            if (self.ingestion_during_scoring) {
                try {
                    self.lines[submission_id][kind].push(message)
                } catch (e) {
                    _.set(self.lines, `${submission_id}.${kind}`, [message])
                }
            } else {
                try {
                    self.lines[submission_id].push(message)
                } catch (e) {
                    self.lines[submission_id] = [message]
                }
            }
            self.update()
            self.autoscroll_output()
        }

        self.clear_form = function () {
            $('input-file[ref="data_file"]').find("input").val('')
            self.errors = {}
            self.update()
        }

        self.set_difference = function (setA, setB) {
            let difference = new Set(setA)
            for (ele of setB){
                difference.delete(ele)
            }
            return difference
        }

        self.check_can_upload = function () {
            CODALAB.api.can_make_submissions(self.selected_phase.id)
                .done(function (data) {
                    if (data.can) {
                        self.prepare_upload(self.upload)()
                    } else {
                        toastr.error(data.reason)
                    }
                })
                .fail(function (data) {
                    toastr.error('Could not verify your ability to make a submission')
                })
        }

        self.get_fact_sheet_answers = function () {
            let form_array = $(self.refs.form).serializeArray()
            let form_json = {}
            for (answer of form_array) {
                if(answer['value'] === 'true'){
                    form_json[answer['name']] = true
                }
                else if(answer['value'] === 'false'){
                    form_json[answer['name']] = false
                } else {
                form_json[answer['name']] = answer['value']
                }
            }
            return form_json
        }

        self.upload = function () {
            self.display_output = true

            console.log(self.refs.selected_tasks.value)
            var data_file_metadata = {
                type: 'submission'
            }
            var data_file = self.refs.data_file.refs.file_input.files[0]
            self.children = []
            self.children_statuses = {}
            CODALAB.api.create_dataset(data_file_metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    self.lines = {}


                    // Call start_submission with dataset key
                    // start_submission returns submission key
                    CODALAB.api.create_submission({
                        "data": data.key,
                        "phase": self.selected_phase.id,
                        "fact_sheet_answers": self.get_fact_sheet_answers(),
                        "tasks": [29,30]
                    })
                        .done(function (data) {
                            CODALAB.events.trigger('new_submission_created', data)
                            CODALAB.events.trigger('submission_selected', data)
                        })
                        .fail(function (response) {
                            try {
                                let errors = JSON.parse(response.responseText)
                                let error_str = Object.keys( errors ).map(function (key) { return errors[key] }).join("; ")
                                toastr.error("Submission Failed: ".concat(error_str))
                            } catch (e) {
                                toastr.error("Submission Failed")
                            }
                        })
                })
                .fail(function (response) {
                    if (response) {
                        try {
                            let errors = JSON.parse(response.responseText);

                            // Clean up errors to not be arrays but plain text
                            Object.keys(errors).map(function (key, index) {
                                errors[key] = errors[key].join('; ')
                            })

                            self.update({errors: errors})
                            console.log(errors)
                        } catch (e) {

                        }
                    }
                    toastr.error("Creation failed, error occurred")
                })
                .always(function () {
                    setTimeout(self.hide_progress_bar, 500)
                    self.clear_form()
                })
        }

        CODALAB.events.on('phase_selected', function (selected_phase) {
            self.selected_phase = selected_phase
            self.ingestion_during_scoring = _.some(selected_phase.tasks, t => t.ingestion_only_during_scoring)
            self.update()
        })

        CODALAB.events.on('submissions_loaded', submissions => {
            let latest_submission = _.head(_.filter(submissions, {parent: null}))
            if (latest_submission && !_.includes(['Finished', 'Cancelled', 'Failed', 'Unknown'], latest_submission.status)) {
                self.selected_submission = latest_submission
                self.children = _.sortBy(latest_submission.children)
                if (self.children) {
                    self.update()
                    $('.menu .item', self.root).tab()
                }
                self.pull_logs()
            }
        })

        CODALAB.events.on('submission_selected', function (selected_submission) {
            self.selected_submission = selected_submission
            self.autoscroll_output()
        })

        self.autoscroll_output = function () {
            if (!self.refs.autoscroll_checkbox) {
                return
            }
            if (self.autoscroll_selected) {
                var output = self.refs.submission_output
                output.scrollTop = output.scrollHeight
            }
        }
    </script>

    <style type="text/stylus">
        .submission-form
            background-color white
            padding 2em
            margin 0, -2.9em
            border solid 1px #dcdcdcdc
            margin-bottom 2em

        .submission-form-question
            padding .66em 2em

            label
                font-size 16px
                font-weight 600

        :scope
            display block
            width 100%
            height 100%
            margin-bottom 15px

        code
            background hsl(220, 80%, 90%)

        .submission-container
            margin-top 1em

        .hidden
            display none

        .submission-output-container
            margin-top 15px

            .ui.basic.segment
                min-height 300px
                display none
                overflow-y auto

        .graph-container
            display block
            height 250px
    </style>
</submission-upload>
