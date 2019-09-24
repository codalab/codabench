<comp-detail-title>
    <div class="title-flex">
        <div class="competition-logo">
            <img class="competition-image ui medium circular image" height="200" width="200" alt="Competition Logo"
                 src="{ competition.logo }">
        </div>
        <div class="competition-details">
            <div class="competition-name">
                <span class="underline">{competition.title}</span>
                <div if={competition.admin_privilege} class="ui admin-dropdown dropdown">
                    <i onclick="{admin_dropdown}" class="admin-icon mini cogs icon"></i>
                    <div class="menu">
                        <div onclick="{admin_modal.bind(this, 'competition')}" class="item">
                            <i class="wrench icon"></i>
                            <span class="label-text">Manage Competition</span>
                        </div>
                        <div onclick="{admin_modal.bind(this, 'submissions')}" class="item">
                            <i class="file archive outline icon"></i>
                            <span class="label-text">Manage Submissions</span>
                        </div>
                        <div onclick="{admin_modal.bind(this, 'participants')}" class="item">
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
                    {competition.participant_count}
                </a>
                <div class="ui tiny red button">
                    Participants
                </div>
            </div>
            <div class="ui tiny left labeled button">
                <a class="ui tiny basic teal label">
                    {competition.submission_count}
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
            justify-content flex-end

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
