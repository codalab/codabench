<comp-phase-info>
    <div class="ui container grid">
        <div class="row">
            <div class="sixteen wide column">
                <div align="center" class="ui stacked centered message">
                    <h5>Competition Run Time</h5>
                    <div class="ui ordered centered steps">
                        <div each="{competition.phases}" class="step">
                            <div class="content">
                                <div class="title">{title}</div>
                                <div class="description">{description}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this
        self.competition = opts.competition
    </script>
</comp-phase-info>