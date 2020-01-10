<log_window>
    <div if="{!opts.split_logs}">
        <pre class="submission_output"><virtual
                if="{ opts.lines === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                each="{ line in opts.lines }">{ line }</virtual></pre>
    </div>
    <div if="{opts.split_logs}">
        <div>Scoring</div>
        <pre class="submission_output"><virtual
                if="{ _.get(opts.lines, 'program') === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                each="{ line in _.get(opts.lines, 'program', []) }">{ line }</virtual></pre>
        <div>Ingestion</div>
        <pre class="submission_output"><virtual
                if="{ _.get(opts.lines, 'ingestion') === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                each="{ line in _.get(opts.lines, 'ingestion', []) }">{ line }</virtual></pre>
    </div>
    <script>
        let self = this
        self.on('mount', function () {

        })
    </script>
    <style type="text/stylus">
        .submission_output
            height 400px
            padding 15px !important
            overflow auto
    </style>
</log_window>
