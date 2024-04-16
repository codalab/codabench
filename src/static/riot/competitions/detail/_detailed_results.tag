<competition-detailed-results>
    <iframe src="{detailed_result}" width="100%" height="100%" frameBorder="0"></iframe>

    <script>

        let self = this
        CODALAB.api.get_submission_detail_result(opts.submission_id)
            .done((data) => {
                self.detailed_result = data
                self.update()
            })
            .fail((response) => {
                toastr.error(response.responseJSON.error_msg)
            })


    </script>

    <style type="text/stylus">
        competition-detailed-results
            width 100%
    </style>
</competition-detailed-results>