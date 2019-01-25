<comp-stats>
    <div class="ui container relaxed grid comp-stats">
        <div class="middle aligned row">
            <div class="four wide column">
                <div class="ui forced-full-height">
                    <div class="ui compact menu">
                        <a class="item">
                            <i class="icon users"></i> Teams
                            <div class="floating ui red label">10</div>
                        </a>
                        <a class="item">
                            <i class="icon user"></i> Participants
                            <div class="floating ui teal label">63</div>
                        </a>
                    </div>
                </div>
            </div>
            <div class="twelve wide column">
                <div class="ui forced-full-height">
                    <h4>
                        Points and Tiers?
                    </h4>
                    <p>
                        Vestibulum in ultricies sapien, eu lacinia ante. Orci varius natoque
                        penatibus et magnis dis parturient montes, nascetur ridiculus mus.
                        Phasellus malesuada ipsum sed orci varius, et finibus felis lobortis.
                        Aliquam commodo turpis ut augue volutpat pulvinar. Etiam vel mollis
                        diam. Sed eu elit imperdiet, aliquam leo sit amet, pulvinar elit. Fusce
                        vitae elementum odio. Curabitur tristique aliquam nisi, ut rhoncus ipsum
                        consectetur in. Nunc at leo dolor.
                    </p>
                </div>
            </div>
        </div>
    </div>
    <style type="text/stylus">
        .comp-stats
            margin 2vh !important
    </style>
    <script>
        var self = this
        self.competition = {}
        CODALAB.events.on('competition_loaded', function(competition) {
            self.competition = competition
        })
    </script>
</comp-stats>