<!-- <comp-detail-title>
    <div class="ui segment">
        <div class="competition-content">
            <div class="competition-info">
                <img class="competition-logo" height="200" width="200" alt="Competition Logo"
                     src="{ competition.logo }">
                FIXME the logo gets squished to fit in the box
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
            competition.show_secret_key = CODALAB.state.user.has_competition_admin_privileges(competition)
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
</comp-detail-title> -->

<comp-detail-title>
    <div class="title-flex">
        <div class="competition-logo">
            <img class="competition-image ui medium circular image" height="200" width="200" alt="Competition Logo"
                 src="{ competition.logo }">
            <!-- <img class="competition-image ui medium circular image" height="200" width="200" alt="Competition Logo"
                 src="https://picsum.photos/200"> -->
        </div>
        <div class="competition-details">
            <div class="competition-name">
                <span class="underline">{competition.title}</span>
                <div if={competition.admin_privilege} class="ui admin-dropdown dropdown">
                    <i onclick="{admin_dropdown}" class="admin-icon mini cogs icon"></i>
                    <div class="menu">
                        <div onclick="{admin_modal.bind(self, 'competition')}" class="item">
                            <i class="wrench icon"></i>
                            <span class="label-text">Manage Competition</span>
                        </div>
                        <div onclick="{admin_modal.bind(self, 'submissions')}" class="item">
                            <i class="file archive outline icon"></i>
                            <span class="label-text">Manage Submissions</span>
                        </div>
                        <div onclick="{admin_modal.bind(self, 'participants')}" class="item">
                            <i class="users icon"></i>
                            <span class="label-text">Manage Participants</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="competition-phase-info">
                <div class="organized-by disc-label">
                    Organized by:
                    <span class="organizer-name desc-item">
                        {competition.created_by}
                    </span>
                </div>
                <div class="phase-end disc-label">
                    Current phase ends:
                    <span class="organizer-name desc-item">
                        {get_end_date(competition)}
                    </span>
                </div>
                <div class="competition-secret-key" if="{ competition.admin_privilege }">
                    <span class="secret-label">Secret url:</span>
                    <span id="secret-url">https://{ URLS.SECRET_KEY_URL(competition.id, competition.secret_key) }</span>
                    <span onclick="{copy_secret_url}" class="ui send-pop" data-content="Copied!">
                        <i class="ui copy icon"></i>
                    </span>
                </div>
            </div>
        </div>
        <div class="competition-stats">
            <div class="ui tiny left labeled button">
                <a class="ui tiny basic red label">
                    2,048
                </a>
                <div class="ui tiny red button">
                    Participants
                </div>
            </div>
            <div class="ui tiny left labeled button">
                <a class="ui tiny basic teal label">
                    1,520
                </a>
                <div class="ui tiny teal button">
                    Submissions
                </div>
            </div>
            <div class="ui tiny left labeled button">
                <a class="ui tiny basic green label">
                    5,500
                </a>
                <div class="ui tiny green button">
                    Prize
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this

        self.competition = {}

        CODALAB.events.on('competition_loaded', function (competition) {
            competition.admin_privilege = CODALAB.state.user.has_competition_admin_privileges(competition)
            self.competition = competition
        })


        self.admin_modal = function (name) {
            $('.manage-' + name).modal('show')
        }

        self.admin_dropdown = function () {
            $('.admin-dropdown').dropdown()
        }

        self.copy_secret_url = function () {
            var range = document.createRange();
            range.selectNode(document.getElementById("secret-url"));
            window.getSelection().removeAllRanges(); // clear current selection
            window.getSelection().addRange(range); // to select text
            document.execCommand("copy");
            window.getSelection().removeAllRanges();// to deselect
            $('.send-pop').popup('toggle')
        }

        self.get_end_date = function (competition) {
            let end_date = _.get(
                _.first(
                    _.filter(
                        competition.phases, phase => {
                            return phase.status === 'Current'
                        })),
                'end')
            return end_date ? pretty_date(end_date) : 'Never'

        }

    </script>

    <style type="text/stylus">
        $blue = #2c3f4c
        $teal = #00bbbb
        $lightblue = #f2faff

        .title-flex
            display flex

        .competition-logo
            text-align center
            padding 0 50px
            align-self center
            width 30%

            .competition-image
                box-shadow 3px 3px 5px darkgrey

        .competition-details
            width 100%
            display flex
            flex-direction column
            color $blue

            .competition-name
                font-size 3em
                height auto
                line-height 1.1em
                text-transform uppercase
                font-weight 800

            .disc-label
                font-size 1.25em
                text-transform uppercase
                color $teal
                font-family 'Overpass Mono', monospace

            .desc-item
                color $blue
                text-transform capitalize
                font-family 'Overpass Mono', monospace

            .secret-label
                color #DB2828

            .competition-secret-key
                font-size 13px

                .copy.icon
                    cursor pointer

        .admin-dropdown
            height 24px

            .menu > .item
                color $blue !important

            .menu > .selected
                background-color $lightblue !important

            .menu > .item:hover
                background-color $lightblue !important

        .admin-icon
            vertical-align top
            color $teal
            text-shadow 1px 0 0 $blue

        .underline
            border-bottom 1px solid $teal
            display inline-block
            line-height 0.9em


            .competition-phase-info
                height auto

        .tiny.left.labeled.button
            display flex
            margin-top 15px

            .ui.tiny.button
                width 120px
                text-transform uppercase
                font-weight 100

        .ui.table
            color $blue !important

            thead > tr > th
                color $blue !important
                background-color $lightblue !important
    </style>
</comp-detail-title>
