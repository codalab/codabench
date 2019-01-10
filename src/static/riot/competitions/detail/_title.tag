<comp-detail-title>
    <div class="ui segment">
        <div class="competition-content">
            <div class="competition-info">
                <img class="competition-logo" height="200" width="200" alt="Competition Logo"
                     src="https://via.placeholder.com/200">
                <button class="ui small green button uploader">
                    <i class="upload icon"></i>Upload your submission
                </button>
            </div>
            <div class="competition-details">
                <div class="competition-title"><strong>{competition.title}</strong>
                    <div class="sub-participant-wrap">
                        <div class=" competition-participants teal ui label">
                            <div class="detail">{competition.submissions | 'x'}</div>
                            Submissions
                        </div>
                        <div class="competition-submissions red ui label">
                            <div class="detail">{competition.participants | 'x'}</div>
                            Participants
                        </div>
                    </div>
                </div>
                <div class="competition-creator">Organized by: {competition.created_by}</div>
                <div class="competition-phasewrap">
                    <div each="{competition.phases}" class="card competition-phase">
                        <div class="content">
                            <div class="phase-status {status}"><strong>{status} Phase</strong></div>
                            <div class="phase-title">{title}</div>
                            <div class="phase-end">{end}</div>
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

    <style type="text/stylus">
        .competition-content
            display inline-flex
            width 100%

        .sub-participant-wrap
            float right
            right 33px
            position absolute

        .uploader
            width 200px
            margin-top 35px !important

        .competition-info
            width 200px

        .competition-title
            font-size 36px
            padding 20px

        .competition-creator
            font-size 18px
            padding 5px 20px

        .competition-details
            display block

        .competition-phasewrap
            margin 20px 0 0 20px
            display inline-flex
            background-color gainsboro

        .competition-phase
            padding 50px 70px

        .phase-status
            font-size 1.2em
            margin-bottom 5px

        .phase-status.Current
            color #476692

    </style>
</comp-detail-title>

<!-- <comp-detail-title>
    <div class="ui segment">
        <div class="competition-content">
            <div class="competition-title"><strong>{competition.title}</strong></div>
            <div class="competition-description">
                <img alt="Competition Logo" src="https://via.placeholder.com/150">
            </div>
            <div class="competition-details">
                <div class="to-go ui fluid tiny menu">
                    <div class="time fluid item">
                        <i class="bell icon"></i> 3 weeks, 1 day to go
                    </div>
                </div>
                <div class="use-stats ui two item tiny menu">
                    <div class="participants fluid item">
                        <i class="icon users"></i>10 Participants
                    </div>
                    <div class="submissions fluid item">
                        <i class="icon server"></i>60 Submissions
                    </div>
                </div>
                <button class="ui small button uploader">
                    <i class="upload icon"></i>Upload your submission
                </button>
            </div>


            <div class="competition-phases">
                <ul class="progressbar">
                    <li each="{competition.phases}" class="phase-tile">
                        <div>{title}</div>
                    </li>
                </ul>
            </div>
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
            grid-template-areas "competition-title competition-title" "competition-description competition-description" "competition-details competition-details" "competition-phases competition-phases"

        @media screen and (min-width 700px)
            .competition-content
                grid-template-areas "competition-title competition-details" "competition-description competition-details" "competition-description competition-details" "competition-phases competition-phases"

        .competition-title
            grid-area competition-title
            font-size 2em
            text-align center

        .competition-details
            grid-area competition-details
            margin-top 2px
            margin-bottom 5px
            display grid
            grid-template-columns 1fr 1fr
            grid-gap 10px
            grid-template-areas "to-go to-go" "use-stats use-stats" "uploader uploader"

            .time.item
                background-color #c7402d
                color white
                border-radius .28571429rem !important
                justify-content center
                width inherit

            .to-go
                grid-area to-go
                margin-bottom 0

            .use-stats
                grid-area use-stats
                margin 0

            .uploader
                grid-area uploader

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

        .progressbar li.active
            color #3ebe32

        .progressbar li.active:before
            border-color rgba(62, 190, 50, .77)
            box-shadow 2px 2px 25px #3ebe32

        .uploader
            width 100%

        .uploader
            margin 0 auto
            border-radius 6px

        .uploader
            border solid 1px rgba(0, 0, 0, .61) !important
            box-shadow 0 2px 0px -0.5px rgba(0, 0, 0, .61) !important
            transition 0.11s ease-in-out !important

        .uploader:active
            box-shadow 2px 3px 5px -3px rgba(46, 46, 58, 0.39) !important
            transform translateY(2px)

    </style>
</comp-detail-title> -->
