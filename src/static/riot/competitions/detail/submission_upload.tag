<submission-upload>
    <div class="ui sixteen wide column submission-container">
        <h1>Submission upload</h1>

        <form class="ui form coda-animated {error: errors}" ref="form" enctype="multipart/form-data">
            <input-file name="data_file" ref="data_file" error="{errors.data_file}" accept=".zip"></input-file>
        </form>

        <div class="ui indicating progress" ref="progress">
            <div class="bar">
                <div class="progress">{ upload_progress }%</div>
            </div>
        </div>

        <button onclick="">Show modal</button>

        <div class="ui modal">
            <i class="close icon"></i>
            <div class="header">Output</div>
            <div class="content">
                <canvas ref="chart" style="width: 100%; height: 150px;"></canvas>
                <pre class="submission_output" ref="submission_output"><virtual each="{ line in lines[selected_submission.id] }">{ line }</virtual></pre>
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

        self.graph_config = {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    backgroundColor: 'red',
                    borderColor: 'red',
                    data: [],
                    fill: false,
                }]
            },
            options: {
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



            /*
            var loop = function () {
                self.chart.data.labels.push('');
                self.chart.data.datasets.forEach((dataset) => {
                    dataset.data.push(Math.random() * 100);
                });
                self.chart.update();

                //self.lines.push('asdf')
                //self.update()
                //self.refs.submission_output.scrollTop = self.refs.submission_output.scrollHeight
                setTimeout(loop, 1000)
            }
            loop()
             */


            // File upload handler
            $(self.refs.data_file.refs.file_input).on('change', self.check_can_upload)


            // Submission stream handler
            var url = new URL('/submission_output/', window.location.href);
            url.protocol = url.protocol.replace('http', 'ws');
            var options = {
                automaticOpen: false
            }
            var ws = new ReconnectingWebSocket(url, null, options)
            ws.addEventListener("open", function (event) {
                console.log("open event, again?")
                console.log(event)
            })
            ws.addEventListener("message", function (event) {
                console.log("message event")
                console.log(event)

                try {
                    var event_data = event.data.split(';')[1]
                    var data = JSON.parse(event_data);

                    if(data.type === "error_rate_update") {
                        self.add_graph_data_point(data.error_rate)
                    } else if(data.type === "message") {
                        self.add_line(data.message)
                    }
                } catch (e) {
                    // This is the default way to handle socket messages (just print them),  but can be sent as a json message as well
                    self.add_line(event.data)
                }
            })
            ws.open()
        })

        self.add_graph_data_point = function(number) {
            // Add empty label for the graph, may not be necessary?
            self.chart.data.labels.push('');

            // Add actual number to dataset
            self.chart.data.datasets.forEach((dataset) => {
                dataset.data.push(number);
            });
            self.chart.update();
        }

        self.add_line = function(line) {
            var line_parts = line.split(/;(.+)/)
            var submission_id = line_parts[0]
            var message = line_parts[1]

            if(!self.lines[submission_id]) {
                self.lines[submission_id] = []
            }

            self.lines[submission_id].push(message + "\n")
            self.update()
            self.refs.submission_output.scrollTop = self.refs.submission_output.scrollHeight
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
                        self.prepare_upload(self.upload())
                    } else {
                        toastr.error(data.reason)
                    }
                })
                .fail(function (data) {
                    toastr.error('Could not verify your ability to make a submission')
                })
        }

        self.upload = function () {
            var data_file_metadata = {
                type: 'submission'
            }
            var data_file = self.refs.data_file.refs.file_input.files[0]

            CODALAB.api.create_dataset(data_file_metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    $('.ui.modal', self.root).modal('show')
                    // Init chart AFTER modal is shown
                    self.chart = new Chart(self.refs.chart, self.graph_config)

                    console.log("Created submission dataset:")
                    console.log(data)

                    // Call start_submission with dataset key
                    // start_submission returns submission key
                    CODALAB.api.create_submission({
                        "data": data.key,
                        "phase": self.selected_phase.id
                    })
                        .done(function(data){
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

        CODALAB.events.on('phase_selected', function(selected_phase) {
            self.selected_phase = selected_phase
        })
        CODALAB.events.on('submission_selected', function(selected_submission) {
            console.log("selected_submission")
            console.log(selected_submission)
            self.selected_submission = selected_submission
        })
    </script>

    <style type="text/stylus">
        :scope
            display block
            width 100%
            height 100%

        code
            background: hsl(220, 80%, 90%)

        .submission-container
            min-height 50vh
    </style>
</submission-upload>