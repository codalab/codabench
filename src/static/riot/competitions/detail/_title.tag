<comp-detail-title>

    <div class="competition-content">

        <div class="competition-title"><strong>{competition.title}</strong></div>
        <div class="competition-description"><p>{competition.description}</p></div>
        <div class="competition-phases">
            <h2>Phases</h2>
            <ul class="progressbar">

                <li each="{competition.phases}" class="phase-tile"><div>{title}</div> <div>{description}</div></li>
            </ul>
        </div>
    </div>



    <script>
        var self = this
        self.competition = opts.competition
    </script>

    <style type="text/stylus">
        .competition-content
            display grid
            grid-template-rows .25fr .5fr 1fr
            grid-template-columns 1fr 1fr
            grid-template-areas "competition-title competition-title" "competition-description competition-description" "competition-phases competition-phases"

        .competition-title
            grid-area competition-title
            font-size 2em
            text-align center

        .competition-description
            grid-area competition-description
            display grid

        .competition-phases
            grid-area competition-phases

        .progressbar
            counter-reset step
            padding 0

        .progressbar li
            list-style-type none
            width 33.33%
            float left
            font-size 12px
            position relative
            text-align center
            text-transform uppercase
            color #7d7d7d

        .progressbar li:before
            width 30px
            height 30px
            content counter(step)
            counter-increment step
            line-height 30px
            border 2px solid #7d7d7d
            display block
            text-align center
            margin 0 auto 10px auto
            border-radius 50%
            background-color white

        .progressbar li:after
            width 100%
            height 2px
            content ''
            position absolute
            background-color #7d7d7d
            top 15px
            left -50%
            z-index -1

        .progressbar li:first-child:after
            content none

        .progressbar li.completed
            color #71a4be

        .progressbar li.completed:before
            border-color #71a4be
            content '✓'

        .progressbar li.completed + li:after
            background-color #71a4be


    </style>
</comp-detail-title>

