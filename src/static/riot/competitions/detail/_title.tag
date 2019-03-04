<comp-detail-title>
    <div class="ui segment">
        <div class="competition-content">
            <div class="competition-info">
                <img class="competition-logo" height="200" width="200" alt="Competition Logo"
                     src="{ competition.logo }">
                <!-- FIXME the logo gets squished to fit in the box -->
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
                <div class="competition-secret-key" if="{ competition.show_secret_key }">
                    <span style="color: #DB2828;">Secret url:</span>
                        https://{ URLS.SECRET_KEY_URL(competition.id, competition.secret_key) }
                </div>
                <div class="competition-phasewrap">
                    <div each="{competition.phases}" class="card competition-phase">
                        <div class="content">
                            <div class="phase-status {status}"><strong>{status} Phase</strong></div>
                            <div class="phase-title">{name}</div>
                            <div class="phase-end">Ends: {end}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>


    <script>
        var self = this

        self.competition = {}

        CODALAB.events.on('competition_loaded', function(competition) {
            competition.show_secret_key = (CODALAB.state.user.username === competition.created_by || competition.collaborators.includes(parseInt(CODALAB.state.user.id)))
            self.competition = competition
        })

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

        .competition-secret-key
            font-size 12px
            padding 0px 20px

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

