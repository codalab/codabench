<comp-tags>
    <div class="ui container relaxed grid">
        <div align="center" class="row">
            <div class="sixteen wide column">
                <div class="ui">
                    <h1>Tags</h1>
                    <div class="ui tag labels">
                        <a class="ui label">
                            <i class="icon settings"></i> Beginner
                        </a>
                        <a class="ui label">
                            <i class="icon wrench"></i> Mechanics
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this
        self.competition = {}
        CODALAB.events.on('competition_loaded', function(competition) {
            self.competition = competition
        })
    </script>
</comp-tags>