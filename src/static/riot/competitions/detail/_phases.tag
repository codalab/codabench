<comp-detail-phases>
    <section>
        <ol class="progress-bar">
            <li each="{ phase in phases }" class="{is-active: phase.status == 'Current'}">
                <div class="phase-name">{ phase.name }<br></div>
                <div class="phase-date">{get_date(phase.start)}</div>
                <span class="prog-span"></span>
            </li>
        </ol>
        <!--<canvas height="35" width="800" id="phase-progress">-->

        </canvas>
    </section>

    <script>
        var self = this

        CODALAB.events.on('competition_loaded', function (competition) {
            competition.admin_privilege = CODALAB.state.user.has_competition_admin_privileges(competition)
            self.phases = competition.phases

            first_phase = _.first(self.phases)
            last_phase = _.last(self.phases)

            first_start = new Date(first_phase.start).getTime()
            first_end = new Date(first_phase.end).getTime()
            today = new Date().getTime()
            last_start = new Date(last_phase.start).getTime()
            last_end = new Date(last_phase.end || last_phase.start).getTime()

            percentage = self.get_scale(today, first_start, last_end, 0, 100)
            linear_gradient = 'linear-gradient(to right, #00bbbb ' + percentage + '%, gainsboro ' + percentage + '%, gainsboro 100%)'
            self.update()
            $('.progress-bar .is-active:not(:last-child) .prog-span').css('background-image', linear_gradient)
        })

        self.get_scale = function (today_date, start_date, end_date, min_percentage=0, max_percentage=100) {
            return (((today_date - start_date) * (max_percentage - min_percentage)) / (end_date - start_date)) + min_percentage
        }


        self.get_date = function (phase_date) {
            var date = new Date(phase_date)
            return date.toUTCString()
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

        //

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
</comp-detail-phases>