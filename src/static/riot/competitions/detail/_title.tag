<comp-detail-title>
    <div class="ui horizontal divider"></div>
    <div class="ui container relaxed center aligned grid">
        <div align="center" class="ui twelve wide row">
            <div class="six wide column">
                <h1 class="ui header">{competition.title}</h1>
                <p>{competition.description}</p>
            </div>
            <div class="six wide column">
                <div align="center" class="ui stacked centered">
                    <h2 class="ui medium header">Phases</h2>
                    <div class="ui ordered centered labels">
                        <div each="{competition.phases}" class="ui small label">
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
</comp-detail-title>