<comp-detail-timeline>
    <section>
        <canvas id="myChart" height="120" width="800"></canvas>
    </section>

    <script>
        var self = this

        self.phase_timeline = []
        self.point_styles = []

        CODALAB.events.on('competition_loaded', function (competition) {
            competition.admin_privilege = CODALAB.state.user.has_competition_admin_privileges(competition)
            self.phases = competition.phases
            self.make_phase_timeline(competition.phases)
            self.get_competition_progress()
            self.update()
            self.draw_chart()
        })


        self.draw_chart = function () {
            let ctx = document.getElementById('myChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    datasets: [
                        // data for blue line (start of comp to today)
                        {
                            ...self.get_competition_progress(),
                            borderWidth: 5,
                            borderColor: '#00bbbb',
                            pointBackgroundColor: '#00bbbb',
                            borderCapStyle: 'round',
                        },
                        // Grey Line (actual comp timeline)
                        {
                            data: _.map(self.phase_timeline, phase => ({x: self.get_date(phase.time), y: 0})),
                            label: _.map(self.phase_timeline, phase => phase.name),
                            borderWidth: 4,
                            pointBackgroundColor: '#4a4a4a',
                            borderColor: '#4a4a4a',
                            pointStyle: self.point_styles
                        }]
                },
                options: {
                    layout: {
                        padding: {
                            left: 50,
                            right: 50,
                        }
                    },
                    scales: {
                        yAxes: [{
                            display: false,
                            gridLines: {
                                display: false
                            },
                        }],
                        xAxes: [{
                            type: 'time',
                            time: {
                                unit: 'month',
                            },
                            display: true,
                            gridLines: {
                                display: true
                            },
                        }]
                    },
                    legend: {
                        display: false
                    },
                    tooltips: {
                        backgroundColor: '#fff',
                        borderColor: '#DCDCDC',
                        borderWidth: 1,
                        titleFontSize: 12,
                        titleFontColor: '#2d3f4b',
                        bodyFontColor: '#2d3f4b',
                        displayColors: false,
                        callbacks: {
                            label: function (tooltipItem, data) {
                                let title = _.get(data.datasets[tooltipItem.datasetIndex], `label[${tooltipItem.index}]`, 'N/A')
                                if (title === 'Competition Never Ends') {
                                    return ''
                                }
                                return pretty_date(new Date(tooltipItem.xLabel).toISOString())
                            },
                            title: function (tooltipItem, data) {
                                tooltipItem = _.head(tooltipItem)
                                return _.get(data.datasets[tooltipItem.datasetIndex], `label[${tooltipItem.index}]`, 'N/A')
                            }
                        }
                    }
                }
            })
        }

        self.get_date = function (phase_date) {
            var date = new Date(phase_date)
            return date.toUTCString()
        }

        self.get_competition_progress = function () {

            let now = new Date()
            let past_phases = _.filter(self.phase_timeline, phase => phase.time < now)

            let data = {
                data: _.map(past_phases, phase => ({x: phase.time, y: 0})),
                label: _.map(past_phases, phase => phase.name),
                pointStyle: _.map(past_phases, phase => 'circle')
            }
            if (past_phases.length < self.phase_timeline.length) {
                data.data.push({x: new Date().getTime(), y: 0})
                data.label.push('Today')
                data.pointStyle.push('line')
            }

            return data
        }

        self.make_phase_timeline = function (phases) {
            _.forEach(phases, function (phase) {
                self.phase_timeline.push({
                    time: new Date(phase.start).getTime(),
                    name: `${phase.name} Start`,
                })
                self.point_styles.push('circle')
                if (phase.end) {
                    self.phase_timeline.push({
                        time: new Date(phase.end).getTime(),
                        name: `${phase.name} End`,
                    })
                    self.point_styles.push('circle')
                } else {
                    self.phase_timeline.push({
                        time: new Date().setDate(new Date().getDate() + 90),
                        name: 'Competition Never Ends',
                    })
                    self.point_styles.push('line')
                }

            })
        }
    </script>

    <style type="text/stylus">
        $white = #fff
        $black = #333
        $gray = #75787b
        $gray-light = #bbb
        $gray-disabled = #e8e8e8
        $blue = #2c3f4c
        $teal = #00bbbb
        $lightblue = #f2faff
        $background = #f6f8fa
        $fontSizeSmall = .75rem
        $fontSizeDefault = .875rem

        *
            box-sizing border-box

        section
            width 70%
            margin 0 auto 2rem

        .phase-date
            display block

        .progress-bar
            display flex
            justify-content space-between
            list-style none
            padding 0
            margin 0 0 1rem 0

        .progress-bar li
            flex 2
            position relative
            padding 0 0 14px 0
            font-size $fontSizeDefault
            line-height 1.5
            color $teal
            font-weight 600
            white-space nowrap
            overflow visible
            min-width 0
            text-align center

        .progress-bar li:first-child,
        .progress-bar li:last-child
            flex 1

        .progress-bar li:first-child
            text-align left

        .progress-bar li:last-child
            text-align right

        .progress-bar li:before
            content ""
            display block
            width 12px
            height 12px
            background-color $gray-disabled
            border-radius 50%
            border 2px solid $background
            position absolute
            left calc(50% - 6px)
            bottom -7px
            z-index 3
            transition all .2s ease-in-out

        .progress-bar li:first-child:before
            left 0

        .progress-bar li:last-child:before
            right 0
            left auto

        .progress-bar div
            transition opacity .3s ease-in-out

        .progress-bar li:not(.is-active) div
            opacity 0

        .prog-span
            width 100%

        .progress-bar li:first-child .prog-span
            width 200%
            left 0 !important

        .progress-bar .is-complete .prog-span
            display inherit
            position absolute
            bottom -2px
            left 50%
            z-index 2
            background-image linear-gradient(to right, $teal, $teal)
            height 2px

        .progress-bar .is-active:not(:last-child) .prog-span,
        .progress-bar .is-active:not(:first-child) .prog-span
            display inherit
            position absolute
            bottom -2px
            left 50%
            z-index 2
            background-image linear-gradient(to right, gainsboro, gainsboro)
            height 2px

        .progress-bar li:last-child div
            display block
            position relative

        .progress-bar .is-complete:before
            background-color: $teal

        .progress-bar .is-active:before,
        .progress-bar li:hover:before,
        .progress-bar .is-hovered:before
            background-color $background
            border-color $teal

        .progress-bar li:hover:before,
        .progress-bar .is-hovered:before
            transform scale(1.33)

        .progress-bar li:hover div,
        .progress-bar li.is-hovered div
            opacity 1

        .progress-bar:hover li:not(:hover) div
            opacity 0

        .progress-bar .has-changes
            opacity 1 !important

        .progress-bar .has-changes:before
            content ""
            display block
            width 12px
            height 12px
            position absolute
            left calc(50% - 4px)
            bottom -20px
            background-image url('data:image/svg+xmlcharset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%208%208%22%3E%3Cpath%20fill%3D%22%23ed1c24%22%20d%3D%22M4%200l4%208H0z%22%2F%3E%3C%2Fsvg%3E')

    </style>
</comp-detail-timeline>
