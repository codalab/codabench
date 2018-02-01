<comp-detail-title>


    <div class="ui container grid">
        <div class="row">
            <div class="sixteen wide column">
                <div class="ui message">
                    <h1 class="ui header">{competition.title}</h1>
                    <p>
                        {competition.description}
                    </p>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this
        self.competition = opts.competition
    </script>
</comp-detail-title>