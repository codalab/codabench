<competition-upload>
    <div class="ui grid container">
        <div class="eight wide column centered form-empty">
            <div class="ui segment">
                <div class="flex-header">
                    <h1 class="ui header">Benchmark upload</h1>
                    <help_button href="https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Competition-Creation-Bundle/"
                                 tooltip="More information on bundle creation">
                    </help_button>
                </div>


                <!-- File selection state view -->
                <form hide="{ listening_for_status || resulting_competition || resulting_details }" class="ui form coda-animated {error: errors}" ref="form" enctype="multipart/form-data">
                    <input-file name="data_file" ref="data_file" error="{errors.data_file}" accept=".zip"></input-file>
                </form>

                <!-- Upload progress state view -->
                <div hide="{ listening_for_status || resulting_competition || resulting_details }" class="ui indicating progress" ref="progress">
                    <div class="bar">
                        <div class="progress">{ upload_progress }%</div>
                    </div>
                </div>

                <!-- Error state view -->
                <div class="ui message error" show="{ Object.keys(errors).length > 0 }">
                    <div class="header">
                        Error(s) uploading competition bundle
                    </div>
                    <ul class="list">
                        <li each="{ error, field in errors }">
                            <strong>{field}:</strong> {error}
                        </li>
                    </ul>
                </div>

                <!-- Competition creation task status view -->
                <div ref="task_status_display" class="coda-animated-slow task-status-display">
                    <div class="ui huge text centered inline loader { active: listening_for_status }">Unpacking...</div>

                    <div class="ui success message" show="{ resulting_competition }">
                        <div class="header">
                            Competition created!
                        </div>
                        <p><a href="{ URLS.COMPETITION_DETAIL(resulting_competition) }">View</a> your new competition.</p>
                    </div>

                    <div class="ui negative message" show="{ !listening_for_status && !resulting_competition }">
                        <div class="header">
                            Creation failed
                        </div>
                        <p>{ resulting_details }</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this
        self.mixin(ProgressBarMixin)

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = {}
        self.listening_for_status = false
        self.resulting_competition = undefined

        self.one('mount', function() {
            // Prepare and do the upload on file input change
            $(self.refs.data_file.refs.file_input).on('change', self.check_form)
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.clear_form = function () {
            // Clear form
            $(':input', self.root)
                .not(':button, :submit, :reset, :hidden')
                .val('')

            self.errors = {}
            self.update()
        }

        self.check_form = function (event) {
            if (event) {
                event.preventDefault()
            }

            var data_file = self.refs.data_file.refs.file_input.value

            if(data_file === undefined || !data_file.endsWith('.zip')) {
                toastr.warning("Please select a .zip file to upload")
                setTimeout(self.clear_form, 1)
                return
            }

            self.clear_form()

            // Call the progress bar wrapper and do the upload -- we want to check and display errors
            // first before doing the actual upload
            self.prepare_upload(self.upload)()
        }
        self.upload = function () {
            // Have to get the "FormData" to get the file in a special way
            // jquery likes to work with
            var metadata = {
                type: 'competition_bundle'
            }
            var data_file = self.refs.data_file.refs.file_input.files[0]

            CODALAB.api.create_dataset(metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    setTimeout(function() {
                        self.status_listening_loop(data.status_id)
                    }, 501)  // do this after the always() hide progress bar's 500ms wait
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
                })
        }

        self.status_listening_loop = function(id) {
            // Show listen section nicely, changing max height does animation for us
            self.refs.task_status_display.style.maxHeight = '1000px'
            self.listening_for_status = true
            self.update()

            // Every 2 seconds get status
            setTimeout(function() {
                CODALAB.api.get_competition_creation_status(id)
                    .done(function(data){
                        var status = data.status.toLowerCase()
                        if(status === "finished" || status === "failed") {
                            self.resulting_details = data.details
                            self.resulting_competition = data.resulting_competition
                            self.listening_for_status = false
                            self.update()
                        } else {
                            // Continue looping, we're not done yet!
                            self.status_listening_loop(id)
                        }
                    })
                    .fail(function(data) {
                        self.status_listening_loop(id)
                    })

                    //.always(function() {
                    //    // Hide the task status display now
                    //    self.refs.task_status_display.style.maxHeight = '0'
                    //})
            }, 2000)
        }
    </script>

    <style type="text/stylus">
        :scope
            padding 50px 0

        h1.header
            margin-bottom 35px !important

        .task-status-display
            max-height 0
            overflow hidden

        .loader
            padding-bottom 20px

        .flex-header
            display flex
            flex-direction row
            justify-content space-between
    </style>
</competition-upload>
