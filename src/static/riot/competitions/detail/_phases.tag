<comp-detail-phases>
    <section>
        <ol class="progress-bar">
            <li class="is-complete"><span>asdf</span></li>
            <li each="{ phase in phases }" class="{is-active: phase.status == 'Current'}">
                <span class="phase-name">{ phase.name }</span>
                <span class="phase-date">{get_date(phase.start)}</span>
            </li>

            <li><span>asdf</span></li>

        </ol>
    </section>

    <script>
        var self = this

        CODALAB.events.on('competition_loaded', function (competition) {
            competition.admin_privilege = CODALAB.state.user.has_competition_admin_privileges(competition)
            self.phases = competition.phases

        })

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
            border-bottom 2px solid $gray-disabled


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


        .progress-bar span
            transition opacity .3s ease-in-out


        .progress-bar li:not(.is-active) span
            opacity 0


        .progress-bar .is-complete:not(:first-child):after,
        .progress-bar .is-active:not(:first-child):after
            content ""
            display block
            width 100%
            position absolute
            bottom -2px
            left -50%
            z-index 2
            border-bottom 2px solid $teal


        .progress-bar li:last-child span
            width 200%
            display inline-block
            position absolute
            left -100%


        .progress-bar .is-complete:last-child:after,
        .progress-bar .is-active:last-child:after
            width 200%
            left -100%


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


        .progress-bar li:hover span,
        .progress-bar li.is-hovered span
            opacity 1


        .progress-bar:hover li:not(:hover) span
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