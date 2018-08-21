<competition-upload>



















    <!--



    Competition bundle can just be a type of DATASET!!!!

    Use all the same dataset upload shit we have

    Pass Competition Bundle dataset to some celery task

    Task unpacks bundle, makes all the baby datsets, etc.
        - Returns any form errors



    -->

























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

                <form enctype="multipart/form-data" class="ui form {error: errors}" ref="form" onsubmit="{ upload }">
                    <input-file name="data_file" error="{errors.data_file}" accept=".zip"></input-file>
                    <input type="hidden" name="type" ref="type" class="ui dropdown" value="Competition Bundle">

                    <div class="ui grid">
                        <div class="sixteen wide column right aligned">
                            <button class="ui button" type="submit">
                                <i class="upload icon"></i> Upload
                            </button>
                        </div>
                    </div>
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


        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.upload = function (event) {
            if (event) {
                event.preventDefault()
            }

            // Reset upload progress, in case we're trying to re-upload or had errors -- this is the
            // best place to do it
            self.upload_progress = undefined

            // Have to get the "FormData" to get the file in a special way
            // jquery likes to work with
            var data = new FormData(self.refs.form)

            CODALAB.api.create_dataset(data, self.file_upload_progress_handler)
                .done(function (data) {
                    toastr.success("Competition uploaded successfully!")
                    self.update_datasets()
                    self.clear_form()
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
                    self.hide_progress_bar()
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
