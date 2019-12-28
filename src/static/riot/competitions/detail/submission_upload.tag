<submission-upload>
    <div class="ui sixteen wide column submission-container" show="{_.get(selected_phase, 'status') === 'Current' || opts.is_admin}">
        <h1>Submission upload</h1>

        <form class="ui form coda-animated {error: errors}" ref="form" enctype="multipart/form-data">
            <input-file name="data_file" ref="data_file" error="{errors.data_file}" accept=".zip"></input-file>
        </form>


        <div class="ui indicating progress" ref="progress">
            <div class="bar">
                <div class="progress">{ upload_progress }%</div>
            </div>
        </div>

        <div class="ui styled fluid accordion submission-output-container {hidden: !status_received}" ref="accordion">
            <div class="title">
                <i class="dropdown icon"></i>
                {(status_received && selected_submission.filename) ? "Running " + selected_submission.filename : "Uploading..."}
            </div>
            <div class="ui basic segment">
                <div class="content">
                    <div id="submission-output" class="ui" ref="submission-output">
                        <div class="header">Output</div>
                        <div class="content">
                            <!-- We have to have this on a gross line so Pre formatting stays nice -->
                            <div show="{!ingestion_during_scoring}">
                                <pre class="submission_output" ref="submission_output"><virtual
                                        if="{ lines[selected_submission.id] === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                                        each="{ line in lines[selected_submission.id] }">{ line }</virtual></pre>
                                <div class="ui checkbox" ref="autoscroll_checkbox">
                                    <input type="checkbox" checked/>
                                    <label>Autoscroll Output</label>
                                </div>
                            </div>
                            <div if="{ingestion_during_scoring}">
                                <div>Scoring</div>
                                <pre class="submission_output"><virtual
                                        if="{ lines[selected_submission.id] === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                                        each="{ line in _.get(lines[selected_submission.id], 'program', []) }">{ line }</virtual></pre>
                                <div>Ingestion</div>
                                <pre class="submission_output"><virtual
                                        if="{ lines[selected_submission.id] === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                                        each="{ line in _.get(lines[selected_submission.id], 'ingestion', []) }">{ line }</virtual></pre>
                            </div>
                            <div class="graph-container">
                                <canvas class="output-chart" height="200" ref="chart"></canvas>
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
        self.selected_submission = {}
        self.status_received = false
        self.display_output = false
        self.autoscroll_selected = true
        self.ingestion_during_scoring = undefined

        self.graph_data = {
            labels: [],
            datasets: [{
                backgroundColor: 'rgba(0,187,187,0.3)',
                pointBackgroundColor: 'rgba(0,187,187,0.8)',
                borderColor: 'rgba(0,187,187,0.8)',
                data: [],
                // fill: false,
            }]
        }

        self.graph_config = {
            type: 'line',
            data: self.graph_data,
            options: {
                maintainAspectRatio: false,
                legend: false,
                responsive: true,
                animation: {
                    duration: 100,
                    easing: 'easeInCirc'
                },
                tooltips: {
                    mode: 'index',
                    intersect: false,
                },
                hover: {
                    mode: 'nearest',
                    intersect: true
                },
                scales: {
                    /*xAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Month'
                        }
                    }],*/
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            maxTicksLimit: 2,
                            suggestedMin: 0,
                            suggestedMax: 1,
                            display: true
                        }
                    }]
                }
            }
        }

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
                        _.forEach(_.compact(event_data.data.split('\n')), data => {
                            self.handle_websocket(event_data.submission_id, data)
                        })
                        break
                    case 'message':
                        self.handle_websocket(event_data.submission_id, event_data.data)
                        break
                }
            })
            self.ws.open()

        }
        self.handle_websocket = function (submission_id, data) {
            data = JSON.parse(data)
            let message = data.message
            let kind = data.kind
            if (kind === 'status_update') {
                self.status_received = true
                self.update()
                CODALAB.events.trigger('submission_status_update', {submission_id: submission_id, status: message})
            } else {
                try {
                    message = JSON.parse(message);
                    if (message.type === "plot") {
                        self.add_graph_data_point(message.value)
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
                self.ws.send(self.selected_submission.id)
            }
        }

        self.set_checkbox = function () {
            $(self.refs.autoscroll_checkbox).children('input').prop('checked', self.autoscroll_selected)
        }


        self.add_graph_data_point = function (number) {
            if (!self.chart) {
                self.chart = new Chart(self.refs.chart, self.graph_config)
            }
            // Add empty label for the graph, may not be necessary?
            self.chart.data.labels.push('')

            // Add actual number to dataset
            self.chart.data.datasets.forEach((dataset) => {
                dataset.data.push(number)
            });
            self.chart.update();
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
            $(':input', self.root)
                .not(':button, :submit, :reset, :hidden')
                .val('')

            self.errors = {}
            self.update()
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

        self.upload = function () {
            self.display_output = true

            var data_file_metadata = {
                type: 'submission'
            }
            var data_file = self.refs.data_file.refs.file_input.files[0]

            CODALAB.api.create_dataset(data_file_metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    self.lines = {}

                    if (self.chart) {
                        self.chart.data = self.graph_data
                        self.chart.update()
                    } else {
                        self.chart = new Chart(self.refs.chart, self.graph_config)
                    }

                    console.log("Created submission dataset:")
                    console.log(data)

                    // Call start_submission with dataset key
                    // start_submission returns submission key
                    CODALAB.api.create_submission({
                        "data": data.key,
                        "phase": self.selected_phase.id
                    })
                        .done(function (data) {
                            console.log("Submission created:")
                            console.log(data)
                            CODALAB.events.trigger('new_submission_created', data)
                            CODALAB.events.trigger('submission_selected', data)
                        })
                })
                .fail(function (response) {
                    if (response) {
                        try {
                            var errors = JSON.parse(response.responseText)

                            // Clean up errors to not be arrays but plain text
                            Object.keys(errors).map(function (key, index) {
                                errors[key] = errors[key].join('; ')
                            })

                            self.update({errors: errors})
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
            let latest_submission = _.head(submissions)
            if (latest_submission && !_.includes(['Finished', 'Cancelled', 'Failed', 'Unknown'], latest_submission.status)) {
                self.selected_submission = latest_submission
                self.pull_logs()
            }
        })

        CODALAB.events.on('submission_selected', function (selected_submission) {
            self.selected_submission = selected_submission
            self.autoscroll_output()
        })

        self.autoscroll_output = function () {
            if (self.autoscroll_selected) {
                var output = self.refs.submission_output
                output.scrollTop = output.scrollHeight
            }
        }
    </script>

    <style type="text/stylus">
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

        .submission_output
            max-height 400px
            padding 15px !important
            overflow auto

        .graph-container
            display block
            height 250px
    </style>
</submission-upload>