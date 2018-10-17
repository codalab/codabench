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

        <pre ref="submission_output">
            <virtual each="{ line in lines }">
                { line }
            </virtual>
        </pre>
        <!--
<pre>Starting upload...upload completed!
Waiting for job to be picked up...picked up!

Output from prediction:
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdfa
    asdf
    asdf
    asdf
    a
    ew
    awef
    f
    32
    q23a
    f23
    fa
    23
    3fq2
    12
    3
    q
    asdf
    af
    q
    32f
    a23f
    aef
    a
    32
    a
    asd
    fa

    32f
    a
    fas
    df
    q23f
    as
    fd


Output from scoring:
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf

</pre>-->
    </div>
    <script>
        var self = this

        self.mixin(ProgressBarMixin)

        self.errors = {}
        self.lines = []

        self.one('mount', function () {
            var loop = function () {
                self.lines.push('asdf')
                self.update()
                self.refs.submission_output.scrollTop = self.refs.submission_output.scrollHeight
                setTimeout(loop, 10000)
            }
            loop()


            $(self.refs.data_file.refs.file_input).on('change', self.prepare_upload(self.upload))




            var url = new URL('/submission_output/', window.location.href);
            url.protocol = url.protocol.replace('http', 'ws');
            var ws = new ReconnectingWebSocket(url)
            ws.onopen = function(event) {
                console.debug("WebSocket opened:", event);
            }
            ws.onmessage = function(event) {
                console.debug("WebSocket message received:", event);
            }
        })

        self.clear_form = function() {
            $(':input', self.root)
                .not(':button, :submit, :reset, :hidden')
                .val('')

            self.errors = {}
            self.update()
        }

        self.upload = function () {



            // TODO: First check that we can even make a submission, are we past the max?





            var data_file_metadata = {
                type: 'submission'
            }
            var data_file = self.refs.data_file.refs.file_input.files[0]

            CODALAB.api.create_dataset(data_file_metadata, data_file, self.file_upload_progress_handler)
                .done(function (data) {
                    // What to do on success?!

                    // Call start_submission with dataset key
                    // start_submission returns submission key
                    CODALAB.api.create_submission({
                        "data": data.key,
                        "phase": 14
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
    </script>

    <style type="text/stylus">
        :scope
            display block
            width 100%
            height 100%

        code
            background: hsl(220, 80%, 90%)

        .submission-container, pre
            height 60vh

        pre
            white-space pre-wrap
            background #1b1c1d
            color #efefef
            overflow-y scroll
            padding 15px

        pre::-webkit-scrollbar
            background-color #efefef

        pre::-webkit-scrollbar-button
            background-color #828282

        pre::-webkit-scrollbar-track
            background-color green

        pre::-webkit-scrollbar-track-piece
            background-color #efefef

        pre::-webkit-scrollbar-thumb
            background-color #575757
            border-radius 0
    </style>
</submission-upload>