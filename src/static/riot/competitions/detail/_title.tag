<comp-detail-title>
    <div class="ui horizontal divider"></div>
    <div class="ui container grid">
        <div class="row">
            <div class="sixteen wide column">
                <h1 class="ui header">{competition.title}</h1>
                <p>{competition.description}</p>
            </div>
        </div>
    </div>
    <script>
        var self = this
        self.competition = opts.competition
    </script>
</comp-detail-title>