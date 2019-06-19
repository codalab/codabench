<show-stats>
    <button id="stats-btn" onclick="{ stats_button_clicked }"
            class="ui black big launch left attached {fixed: show_stats} button">
        <i class="icon {minus: !show_stats, 'chart bar': show_stats}"></i>
        <span class="btn-text">Stats</span>
    </button>
    <div id="stat-card" show="{ !show_stats }" class="ui fixed card">
        <div class="header-bg content">
            <div class="header">By the numbers...</div>
        </div>
        <div class="stat-content content">
            <h4 class="ui sub blue header">{producer_name} brings together</h4>
            <div class="ui three column grid">
                <div class="column" each="{ stat in general_stats }" no-reorder>
                    <div class="ui seven tiny statistics">
                        <div class="statistic">
                            <div class="value">
                                { stat.count }
                            </div>
                            <div class="label">
                                { stat.label }
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this
        self.show_stats = false
        self.general_stats = {}

        self.on("mount", function () {
            $(".tooltip", self.root).popup()
            self.get_general_stats()
        })

        self.get_general_stats = function () {
            var endpoint = CODALAB.api.by_the_numbers()
            endpoint
                .done(function (data) {
                    console.log("Received Codalab Competition Stats")
                    self.update({
                            general_stats: [
                                {label: "Total Competitions", count: num_formatter(data.total_competitions, 1)},
                                {label: "Public Competitions", count: num_formatter(data.public_competitions, 1)},
                                {label: "Private Competitions", count: num_formatter(data.private_competitions, 1)},
                                {label: "Submissions", count: num_formatter(data.submissions, 1)},
                                {label: "Users", count: num_formatter(data.users, 1)},
                                {label: "Competition Participants", count: num_formatter(data.competition_participants, 1)},
                            ],
                        },
                        self.producer_name = 'Codalab',
                    )
                })
        }

        self.stats_button_clicked = function () {
            self.show_stats = !self.show_stats
            self.update()
        }

        function num_formatter(num, digits) {
            var si = [
                {value: 1, symbol: ""},
                {value: 1E3, symbol: "K"},
                {value: 1E6, symbol: "M"},
                {value: 1E9, symbol: "G"},
                {value: 1E12, symbol: "T"},
                {value: 1E15, symbol: "P"},
                {value: 1E18, symbol: "E"}
            ]
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/
            var i
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break
                }
            }
            return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol
        }
    </script>

    <style type="text/stylus">
        :scope

            #stats-btn
                position relative
                float right
                top -72px
                right 0
                width 55px
                height auto
                white-space nowrap
                overflow hidden
                transition 0.3s width ease, 0.5s transform ease

                .icon
                    margin 0 .5em 0 -0.45em

            #stats-btn.fixed
                position fixed !important
                top 110px
                right 0 !important

                #stat-card
                    position fixed

            #stats-btn:hover
                width 130px

                .btn-text
                    opacity 1

            .btn-text
                position absolute
                white-space nowrap
                top auto
                right 54px
                opacity 0
                -webkit-transition 0.23s opacity 0.2s
                -moz-transition 0.23s opacity 0.2s
                -o-transition 0.23s opacity 0.2s
                -ms-transition 0.23s opacity 0.2s
                transition 0.23s opacity 0.2s

            #stat-card
                z-index -1
                position fixed
                right 19px
                top 43px
                width 290px

                .header-bg
                    background-color #f2faff
                    text-align left

                .column
                    padding-bottom 0 !important

                .column:last-of-type
                    padding-bottom 0.5em !important

            .stat-content
                font-size 0.7em !important
                line-height 1.2em !important
                padding 1em 2em 2em 2em !important

            .ui.card > .content > .sub.header
                font-size 1.25em !important
                padding-bottom 10px
                text-align left

            .ui.statistics > .statistic
                flex 1 1 auto

                .value
                    font-weight 800

                .label
                    font-weight 100
    </style>
</show-stats>