<competition-upload>
    <div class="ui grid container">
        <div class="eight wide column centered form-empty">
            <div class="ui segment">
                <h1 class="ui header">
                    Competition upload
                    <div class="sub header">
                        For more information on creating bundles, please visit the <a href="https://github.com/codalab/competitions-v2/wiki">Wiki</a>!
                    </div>
                </h1>

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

                <form class="ui form coda-animated {error: errors}" ref="form" enctype="multipart/form-data">
                    <input-file name="data_file" ref="data_file" error="{errors.data_file}" accept=".zip"></input-file>
                </form>

                <div class="ui indicating progress" ref="progress">
                    <div class="bar">
                        <div class="progress">{ upload_progress }%</div>
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

        self.one('mount', function() {
            // Prepare and do the upload on file input change
            $(self.refs.data_file.refs.file_input).on('change', self.prepare_upload(self.upload))
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.upload = function () {
            // Have to get the "FormData" to get the file in a special way
            // jquery likes to work with
            var metadata = {
                type: 'competition_bundle'
            }
            var data_file = self.refs.data_file.refs.file_input.files[0]

            CODALAB.api.create_dataset(metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    toastr.success("Competition uploaded successfully!")
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
    </script>

    <style type="text/stylus">
        :scope
            padding 50px

        .header
            margin-bottom 35px !important
    </style>
</competition-upload>
