<competition-detailed-results>
    <h3>Detailed Results</h3>
    <iframe src="{detailed_result}" width="100%" height="100%" frameBorder="0"></iframe>

    <script>

        let self = this
        CODALAB.api.get_submission_details(opts.submission_id)
            .done(function (data) {
                self.detailed_result = data.detailed_result
                self.update()
            })   
        
         
    </script>
</competition-detailed-results>