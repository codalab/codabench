<comp-tabs>
    <div class="ui grid comp-tabs">
        <!-- Tab menu -->
        <div class="ui tiny fluid four secondary pointing tabular menu details-menu">
            <div class="item" data-tab="home-tab">Home</div>
            <div class="item" data-tab="pages-tab">Get Started</div>
            <div class="item" data-tab="phases-tab">Phases</div>
            <div class="item" data-tab="participate-tab">My Submissions</div>
            <div class="item" data-tab="results-tab">Results</div>
        </div>

        <!-- Details tab -->
        <!-- <div class="ui active tab" data-tab="details_tab">
            <div class="ui grid">
                <div class="row">
                    <div class="sixteen wide column">
                        <div class="ui side green tabular secondary menu">
                            <div each="{page, index in competition.pages}" class="item {active: index === 0}"
                                 data-tab="page_{index}">
                                {page.title}
                            </div>
                            <div class="item" data-tab="_tags_placeholder">Cool tags (placeholders)</div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="sixteen wide column">
                        <div each="{page, index in competition.pages}" class="ui tab {active: index === 0}"
                             data-tab="page_{index}" id="page_{index}">
                        </div>
                        <div class="ui tab" data-tab="_tags_placeholder">
                            <div class="comp-data-containers">
                                <comp-run-info competition={competition}></comp-run-info>
                                <comp-stats competition={competition}></comp-stats>
                                <comp-tags competition={competition}></comp-tags>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="_tab_terms">
                            <div class="ui">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div> -->

        <div class="ui home-tab tab" data-tab="home-tab">
            <div class="ui two column grid">
                <div class="row">
                    <div class="seven wide column">
                        <div class="short-description">
                            FULLY AUTOMATED IMAGE CLASSIFICATION WITHOUT ANY HUMAN INTERVENTION
                        </div>
                    </div>
                    <div class="nine wide column">
                        <div class="long-description">
                            Despite recent successes of deep learning and other machine learning
                            techniques, practical experience and expertise is still required to select
                            models and/or choose hyper-parameters when applying techniques to new
                            datasets. This problem is drawing increasing interest, yielding progress
                            towards fully automated solutions. In this challenge your machine learning
                            code is trained and tested on this platform, without human intervention
                            whatsoever, on image classification tasks you have never seen before, with
                            time and memory limitations. All problems are multi-label classification
                            problems, coming from various domains including medical imaging, satellite
                            imaging, object recognition, character recognition, face recognition, etc.
                        </div>
                    </div>
                </div>
                <div class="sixteen wide row">
                    <div class="leaderboard">
                        <h1>Top 10 Results</h1>
                        <a class="float-right" href="#">View Full Results<i class="angle right icon"></i>
                        </a>
                        <table class="ui center aligned striped table">
                            <thead>
                            <tr>
                                <th>#</th>
                                <th>Username</th>
                                <th>Average Rank</th>
                                <th>Last Submission</th>
                                <th>Total Compute Time</th>
                            </tr>
                            </thead>
                            <tbody>
                            <tr>
                                <td><img class="medal" src="{ URLS.STATIC('img/gold_medal.svg') }"></td>
                                <td>A person</td>
                                <td>2.25</td>
                                <td>May 15, 2019, 3:33 p.m.</td>
                                <td>4:54:42</td>
                            </tr>
                            <tr>
                                <td><img class="medal" src="{ URLS.STATIC('img/silver_medal.svg') }"></td>
                                <td>A person</td>
                                <td>2.25</td>
                                <td>May 15, 2019, 3:33 p.m.</td>
                                <td>4:54:42</td>
                            </tr>
                            <tr>
                                <td><img class="medal" src="{ URLS.STATIC('img/bronze_medal.svg') }"></td>
                                <td>A person</td>
                                <td>2.25</td>
                                <td>May 15, 2019, 3:33 p.m.</td>
                                <td>4:54:42</td>
                            </tr>
                            <tr>
                                <td><img class="medal" src="{ URLS.STATIC('img/4th_medal.svg') }"></td>
                                <td>A person</td>
                                <td>2.25</td>
                                <td>May 15, 2019, 3:33 p.m.</td>
                                <td>4:54:42</td>
                            </tr>
                            <tr>
                                <td><img class="medal" src="{ URLS.STATIC('img/5th_medal.svg') }"></td>
                                <td>A person</td>
                                <td>2.25</td>
                                <td>May 15, 2019, 3:33 p.m.</td>
                                <td>4:54:42</td>
                            </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!--Get Started tab-->
        <div class="pages-tab ui tab" data-tab="pages-tab">
            <div class="ui relaxed grid">
                <div class="row">
                    <div class="four wide column">
                        <div class="ui side teal vertical tabular pages-menu menu">
                            <div each="{ page, i in competition.pages }" class="{active: i == 0} item"
                                 data-tab="_tab_page{page.index}">
                                { page.title }
                            </div>
                            <div class="{active: _.get(competition.pages, 'length') === 0} item" data-tab="files">
                                Files
                            </div>
                        </div>
                    </div>
                    <div class="twelve wide column">
                        <div each="{ page, i in competition.pages }" class="ui {active: i == 0} tab"
                             data-tab="_tab_page{page.index}">
                            <div class="ui" id="page_{i}">
                            </div>
                        </div>
                        <div class="ui tab {active: _.get(competition.pages, 'length') === 0}" data-tab="files">
                            <div class="ui" id="files">

                                <table class="ui celled selectable table">
                                    <thead>
                                    <tr>
                                        <th class="index-column">Download</th>
                                        <th>Size</th>
                                        <th>Phase</th>
                                        <th class="center aligned {admin-action-column: opts.admin, action-column: !opts.admin}">
                                            Actions
                                        </th>
                                    </tr>
                                    </thead>
                                    <tbody>
                                    <tr each="{ file, index in files }" class="file_row">
                                        <td>
                                            <a href="{ file.url }"><div class="ui button">{ file.name }</div></a>
                                        </td>
                                        <td></td>
                                        <td>{ file.phase }</td>
                                        <td class="center aligned">
                                            <!-- <virtual if="{ opts.admin }">
                                               <button class="mini ui button basic blue icon"
                                                        data-tooltip="Rerun Submission"
                                                        data-inverted=""
                                                        onclick="{ rerun_submission.bind(this, file) }">
                                                    <i class="icon redo"></i>

                                                </button>
                                                <button class="mini ui button basic yellow icon"
                                                        data-tooltip="Cancel Submission"
                                                        data-inverted=""
                                                        onclick="{ cancel_submission.bind(this, file) }">
                                                    <i class="x icon"></i>

                                                </button>
                                                <button class="mini ui button basic red icon"
                                                        data-tooltip="Delete Submission"
                                                        data-inverted=""
                                                        onclick="{ delete_submission.bind(this, file) }">
                                                    <i class="icon trash alternate"></i>

                                                </button>
                                            </virtual>
                                            <button if="{!submission.leaderboard}"
                                                    class="mini ui button basic green icon"
                                                    data-tooltip="Add to Leaderboard"
                                                    data-inverted=""
                                                    onclick="{ add_to_leaderboard.bind(this, file) }">
                                                <i class="icon share"></i>

                                            </button>
                                            <div if="{!!submission.leaderboard}"
                                                 class="mini ui green button icon on-leaderboard"
                                                 data-tooltip="On the Leaderboard"
                                                 data-inverted=""
                                                 onclick="{do_nothing}">
                                                <i class="icon check"></i>
                                            </div>
                                            send submission to leaderboard-->
                                        </td>
                                    </tr>
                                    </tbody>
                                </table>

                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!--Phases tab-->
        <div class="phases-tab ui tab" data-tab="phases-tab">
            <div class="ui relaxed grid">
                <div class="row">
                    <div class="twelve wide centered column">
                        <div each="{ phase, i in competition.phases }" class="ui segments">
                            <div class="ui teal segment phase-header">
                                <span class="underline">{phase.name}</span>
                            </div>
                            <div class="ui bottom attached segment">
                                <div class="phase-label">Start:</div>
                                <div class="phase-info">{pretty_date(phase.start)}</div>
                                <div class="phase-label">End:</div>
                                <div class="phase-info">{pretty_date(phase.end)}</div>
                                <span class="phase-label">Description: </span>
                                <div class="phase-markdown" id="phase_{i}"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Submissions tab-->
        <div class="submission-tab ui tab" data-tab="participate-tab">
            <!-- Tab Content !-->
            <div if="{competition.participant_status === 'approved'}">
                <div class="ui button-container">
                    <div class="ui inline button {active: selected_phase_index == phase.id}"
                         each="{ phase in competition.phases }"
                         onclick="{ phase_selected.bind(this, phase) }">{ phase.name }
                    </div>
                </div>
                <div>
                    <submission-upload phases="{ competition.phases }"></submission-upload>
                </div>
                <div>
                    <submission-manager competition="{ competition }"></submission-manager>
                </div>
            </div>
            <div if="{competition.participant_status !== 'approved'}">
                <registration></registration>
            </div>
        </div>

        <!-- Leaderboard tab-->
        <div class="results-tab ui tab" data-tab="results-tab">
            <!-- Tab Content !-->
            <div>
                <leaderboards competition_pk="{ competition.id }"
                              leaderboards="{ competition.leaderboards }"></leaderboards>
            </div>
        </div>

        <!-- Manage Competition Modal -->
        <div class="ui manage-competition modal">
            <a href="{window.URLS.COMPETITION_EDIT(competition.id)}" class="ui blue button">Edit competition</a>
            <button class="ui button published icon { grey: !competition.published, green: competition.published }"
                    onclick="{ toggle_competition_publish }">
                <i class="icon file"></i> {competition.published ? "Published" : "Draft"}
            </button>
            <button class="ui yellow button icon" onclick="{create_dump}">
                <i class="download icon"></i> Create Competition Dump
            </button>
            <button class="ui teal icon button" onclick="{update_files}"><i class="sync alternate icon"></i> Refresh
                Table
            </button>
            <table class="ui table">
                <thead>
                <tr>
                    <th>Files</th>
                </tr>
                </thead>
                <tbody>
                <tr show="{files.bundle}">
                    <td class="selectable"><a href="{files.bundle ? files.bundle.url : ''}"><i
                            class="file archive outline icon"></i>Bundle: {files.bundle ? files.bundle.name : ''}
                    </a></td>
                </tr>
                <tr each="{file in files.dumps}" show="{files.dumps}">
                    <td class="selectable"><a href="{file.url}"><i class="file archive outline icon"></i>Dump:
                        {file.name}</a></td>
                </tr>
                <tr>
                    <td show="{!files.dumps && !files.bundle}"><em>No Files Yet</em></td>
                </tr>
                </tbody>
            </table>
        </div>
        <!-- Manage Submissions Modal -->
        <div class="ui manage-submissions modal">
            <div class="ui">
                <submission-manager admin="true" competition="{ competition }"></submission-manager>
            </div>
        </div>

        <!-- Manage Participants Modal -->
        <div class="ui manage-participants modal">
            <div class="ui">
                <participant-manager competition_id="{competition}"></participant-manager>
            </div>
        </div>
    </div>

    <div class="ui basic modal" ref="dump_modal">
        <div class="header">
            Creating Competition Dump
        </div>
        <div class="content">
            Success! You competition dump is being created. This may take some time.
            If the files table does not update with the new dump, try refreshing the table.
        </div>
        <div class="actions">
            <div class="ui primary inverted ok button">Dismiss</div>
        </div>
    </div>

    <style type="text/stylus">
        $blue = #2c3f4c
        $teal = #00bbbb
        $lightblue = #f2faff

        .comp-tabs
            margin-top 1em !important

        .ui.secondary.pointing.menu .active.item
            border-color rgba(42, 68, 88, .5)
            color rgb(42, 68, 88)

        .ui.secondary.pointing.menu .active.item:hover
            border-color rgba(42, 68, 88, .5)
            color rgb(42, 68, 88)

        .float-right
            float right

        .details-menu
            width 100%

        .details-menu .active.item, .details-menu .item
            margin -2px auto !important
            cursor pointer

        .home-tab
            padding 2em 0.5em

            .short-description
                font-size 44px
                font-weight 600
                color $blue
                line-height 1em

            .seven.column
                align-self center


            .long-description
                border-left solid 2px $teal
                color $blue
                font-size 14px
                padding 10px
                font-family 'Overpass Mono', monospace

            .leaderboard
                width 100%
                text-align center
                color $blue
                font-family 'Overpass Mono', monospace

                table
                    color $blue !important

                    thead > tr > th
                        color $blue !important
                        background-color $lightblue !important

                    .medal
                        height 25px
                        width auto


        .submission-tab
            margin 0 auto
            width 100%
            @media screen and (min-width 768px)
                width 85%

        .results-tab
            margin 0 auto
            width 100%
            @media screen and (min-width 768px)
                width 85%

        .pages-tab
            margin 0 auto
            width 100%
            @media screen and (min-width 768px)
                width 85%

            .vertical.tabular.menu > .item
                cursor pointer

            .vertical.tabular.menu > .active.item
                z-index 1

            .twelve.wide.column .tab.active
                z-index 0
                background-color white
                margin 0 -2.9em
                padding 2em
                border solid 1px gainsboro

        .phases-tab
            margin 0 auto
            width 100%
            color #2c3f4c

            @media screen and (min-width 768px)
                width 85%

            .underline
                border-bottom 1px solid $teal
                display inline-block
                line-height 0.9em

            .ui.segments
                font-family 'Overpass Mono', monospace
                font-size 14px

            .phase-header
                font-family 'Roboto', sans-serif
                font-size 20px !important
                text-transform uppercase
                font-weight 600
                background-color #e5fbfa

            .phase-label
                font-size 15px
                font-weight 600
                font-family 'Roboto', sans-serif
                color $teal
                text-transform uppercase

            .phase-info
                margin-bottom 10px

        .admin-tab
            margin 0 auto
            width 100%
            @media screen and (min-width 768px)
                width 85%

        pre
            background #f4f4f4
            border 1px solid #ddd
            border-left 3px solid $teal
            border-radius 6px
            color #666
            page-break-inside avoid
            font-family monospace
            font-size 0.85em
            line-height 1.6
            margin-bottom 1.6em
            max-width 100%
            overflow auto
            padding 1em 1.5em
            display block
            word-wrap break-word

        .ui.table
            color $blue !important

            thead > tr > th
                color $blue !important
                background-color $lightblue !important

            .medal
                height 25px
                width auto

    </style>
    <script>
        var self = this

        self.competition = {}
        self.files = {}
        self.selected_phase_index = undefined
        self.competition_file = {}

        CODALAB.events.on('competition_loaded', function (competition) {
            console.log(competition)
            self.competition = competition
            self.competition.is_admin = CODALAB.state.user.has_competition_admin_privileges(competition)
            self.update()
            if (self.competition.is_admin) {
                self.update_files()
            }

            $('.tabular.menu .item', self.root).tab({
                history: true,
                historyType: 'hash',
            })

            $('.tabular.menu .item', self.root).tab('change tab', (window.location.hash || 'home-tab').replace('#/', ''))

            _.forEach(competition.pages, (page, index) => {
                $(`#page_${index}`)[0].innerHTML = render_markdown(page.content)
            })
            _.forEach(competition.phases, (phase, index) => {
                $(`#phase_${index}`)[0].innerHTML = render_markdown(phase.description)
            })
        })

        self.pretty_date = function (date_string) {
            if (!!date_string) {
                return luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATETIME_FULL)
            } else {
                return ''
            }
        }

        self.toggle_competition_publish = function () {
            CODALAB.api.toggle_competition_publish(self.competition.id)
                .done(function (data) {
                    var published_state = data.published ? "published" : "unpublished"
                    toastr.success(`Competition has been ${published_state} successfully`)
                    self.update()
                    CODALAB.api.get_competition(self.competition.id)
                        .done((competition) => {
                            CODALAB.events.trigger('competition_loaded', competition)
                        })
                })
        }

        self.create_dump = () => {
            CODALAB.api.create_dump(self.competition.id)
                .done(data => {
                    $(self.refs.dump_modal).modal('show')
                    // toastr.success(data.status + '<br>This may take a few minutes.')
                    setTimeout(self.update_files, 2000)
                })
                .fail(response => {
                    toastr.error("Error trying to create competition dump.")
                })
        }

        self.phase_selected = function (data, event) {
            self.selected_phase_index = data.id
            self.update()

            CODALAB.events.trigger('phase_selected', data)
        }

        self.update_files = (e) => {
            CODALAB.api.get_competition_files(self.competition.id)
                .done(data => {
                    self.files = data
                    console.table(self.files)
                    self.update()
                    if (e) {
                        // Only display toast if activated from button, not CODALAB.event
                        toastr.success('Table Updated')
                    }
                })
                .fail(response => {
                    toastr.error('Error Retrieving Competition Files')
                })
        }
    </script>

</comp-tabs>