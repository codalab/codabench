<comp-detail-header>
    <div class="ui relaxed grid">
        <div class="row">
            <div class="three wide column">
                <img class="ui medium circular image competition-image"
                     alt="Competition Logo"
                     src="{ competition.logo }">
            </div>
            <div class="ten wide column">
                <div class="ui grid">
                    <div class="row">
                        <div class="column">
                            <div class="competition-name underline">
                                {competition.title}
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="reward-container" if="{competition.reward}">
                            <img class="reward-icon" src="/static/img/trophy.png">
                            <div class="reward-text">{competition.reward}</div>
                        </div>
                    </div>
                    <div if="{competition.admin}">
                        <a href="{URLS.COMPETITION_EDIT(competition.id)}" class="ui button">Edit</a>
                        <button class="ui small button" onclick="{show_modal.bind(this, '.manage-participants.modal')}">
                            Participants
                        </button>
                        <button class="ui small button" onclick="{show_modal.bind(this, '.manage-submissions.modal')}">
                            Submissions
                        </button>
                        <button class="ui small button" onclick="{show_modal.bind(this, '.manage-competition.modal')}">
                            Dumps
                        </button>
                        <button class="ui small button" onclick="{show_modal.bind(this, '.migration.modal')}">
                            Migrate
                        </button>
                    </div>
                    <div class="row">
                        <div class="column">
                            <!-- Main information -->
                            <div>
                                <span class="detail-label">Organized by:</span>
                                <span class="detail-item"><a href="/profiles/user/{competition.created_by}" target="_BLANK">{competition.owner_display_name}</a></span>
                                <span if="{competition.contact_email}">(<span class="contact-email">{competition.contact_email}</span>)</span>
                            </div>
                            <div>
                                <span class="detail-label">{has_current_phase(competition) ? 'Current Phase Ends' : 'Current Active Phase'}:</span>
                                <span class="detail-item">{get_end_date(competition)}</span>
                            </div>
                            <div>
                                <span class="detail-label">Current server time:</span>
                                <span class="detail-item" id="server_time">{pretty_date(CURRENT_DATE_TIME)}</span>
                            </div>
                            <!-- Docker image -->
                            <div class="competition-secret-key">
                                <span class="docker-label">Docker image:</span>
                                <span id="docker-image">{ competition.docker_image }</span>
                                <span onclick="{copy_docker_url}" class="ui send-pop-docker" data-content="Copied!">
                                    <i class="ui copy icon"></i>
                                </span>
                            </div>
                            <!-- Secret URL -->
                            <div class="competition-secret-key" if="{ competition.admin }">
                                <span class="secret-label">Secret url:</span>
                                <span id="secret-url">https://{ URLS.SECRET_KEY_URL(competition.id, competition.secret_key) }</span>
                                <span onclick="{copy_secret_url}" class="ui send-pop-secret" data-content="Copied!">
                                    <i class="ui copy icon"></i>
                                </span>
                            </div>
                            <!-- Competition Report -->
                            <div class="competition-secret-key" if="{competition.report}">
                                <span class="report-label">Competition Report:</span>
                                <span id="report-url">{ competition.report }</span>
                                <span onclick="{copy_report_url}" class="ui send-pop-report" data-content="Copied!">
                                    <i class="ui copy icon"></i>
                                </span>

                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="three wide column">
                <div class="stat-buttons">
                    <!--todo: turn cursor: pointer and hover off on these buttons since they are not clickable-->
                    <div class="ui tiny left labeled fluid button">
                        <a class="ui tiny basic red label">{competition.participants_count}</a>
                        <div class="ui tiny red button">Participants</div>
                    </div>
                    <div class="ui tiny left labeled fluid button">
                        <a class="ui tiny basic teal label">{competition.submissions_count}</a>
                        <div class="ui tiny teal button">Submissions</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- Manage Competition Modal -->
    <div class="ui manage-competition modal" ref="files_modal">
        <div class="content">
            <div class="ui dropdown button">
                <i class="download icon"></i>
                <div class="text">Create Competition Dump</div>
                <div class="menu">
                    <div class="parent-modal item"
                        onclick="{create_dump.bind(this, true)}"> 
                        <!--  true for keys  -->
                        Dump with keys
                    </div>
                    <div class="parent-modal item"
                    
                        onclick="{create_dump.bind(this, false)}">
                        <!--  false for files  -->
                        Dump with files
                    </div>
                </div>
            </div>

            <!--  <button class="ui icon button" onclick="{create_dump}">
                <i class="download icon"></i> Create Competition Dump
            </button>  -->
            <button class="ui icon button" onclick="{update_files}">
                <i class="sync alternate icon"></i> Refresh Table
            </button>
            <table class="ui table">
                <thead>
                <tr>
                    <th>Files</th>
                </tr>
                </thead>
                <tbody>
                <tr show="{files.bundle}">
                    <td class="selectable">
                        <a href="{files.bundle ? files.bundle.url : ''}">
                            <i class="file archive outline icon"></i>
                            Bundle: {files.bundle ? files.bundle.name : ''}
                        </a>
                    </td>
                </tr>
                <tr each="{file in files.dumps}" show="{files.dumps}">
                    <td class="selectable">
                        <a href="{file.url}">
                            <i class="file archive outline icon"></i>
                            Dump: {file.name}
                        </a>
                    </td>
                </tr>
                <tr>
                    <td show="{!files.dumps && !files.bundle}">
                        <em>No Files Yet</em>
                    </td>
                </tr>
                <tr>
                    <td class="center aligned" if="{tr_show}">Generating Dump, Please Refresh</td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
    <!-- Manage Submissions Modal -->
    <div class="ui manage-submissions large modal" ref="sub_modal">
        <div class="content">
            <submission-manager admin="{competition.admin}" competition="{ competition }"></submission-manager>
        </div>
    </div>

    <!-- Manage Participants Modal -->
    <div class="ui manage-participants modal" ref="participant_modal">
        <div class="content">
            <participant-manager></participant-manager>
        </div>
    </div>

    <!-- Manual Migration Modal -->
    <div class="ui migration modal" ref="migration_modal">
        <div class="content">
            <table class="ui table">
                <thead>
                <tr>
                    <th colspan="100%">
                        Please Choose a phase to migrate
                    </th>
                </tr>
                </thead>
                <tbody>
                <tr each="{phase, index in competition.phases}">
                    <td>{phase.name}</td>
                    <td class="collapsing">
                        <button if="{index !== competition.phases.length - 1}"
                                class="ui button"
                                onclick="{migrate_phase.bind(this, phase.id)}">
                            Migrate
                        </button>
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
    <script>
        let self = this

        self.competition = {}
        self.files = []

        self.tr_show = false

        CODALAB.events.on('competition_loaded', function (competition) {
            competition.admin = CODALAB.state.user.has_competition_admin_privileges(competition)
            self.competition = competition
            self.update()
            if (self.competition.admin) {
                self.update_files()
            }
            $('.dropdown', self.root).dropdown()
        })

        self.close_modal = selector => $(selector).modal('hide')
        self.show_modal = selector => $(selector).modal('show')

        self.create_dump = (keys_instead_of_files) => {
            CODALAB.api.create_competition_dump(self.competition.id, keys_instead_of_files)
                .done(data => {
                    self.tr_show = true
                    toastr.success("Success! Your competition dump is being created.")
                    self.update()
                })
                .fail(response => {
                    toastr.error("Error trying to create competition dump.")
                })
        }

        self.update_files = (e) => {
            CODALAB.api.get_competition_files(self.competition.id)
                .done(data => {
                    self.files = data
                    self.tr_show = false
                    self.update()
                })
                .fail(response => {
                    toastr.error('Error Retrieving Competition Files')
                })
        }


        self.copy_secret_url = function () {
            let range = document.createRange();
            range.selectNode(document.getElementById("secret-url"));
            window.getSelection().removeAllRanges(); // clear current selection
            window.getSelection().addRange(range); // to select text
            document.execCommand("copy");
            window.getSelection().removeAllRanges();// to deselect
            $('.send-pop-secret').popup('toggle')
        }

        self.copy_docker_url = function () {
            let range = document.createRange();
            range.selectNode(document.getElementById("docker-image"));
            window.getSelection().removeAllRanges(); // clear current selection
            window.getSelection().addRange(range); // to select text
            document.execCommand("copy");
            window.getSelection().removeAllRanges();// to deselect
            $('.send-pop-docker').popup('toggle')
        }

        self.copy_report_url = function () {
            let range = document.createRange();
            range.selectNode(document.getElementById("report-url"));
            window.getSelection().removeAllRanges(); // clear current selection
            window.getSelection().addRange(range); // to select text
            document.execCommand("copy");
            window.getSelection().removeAllRanges();// to deselect
            $('.send-pop-report').popup('toggle')
        }

        self.has_current_phase = function (competition) {
            let current_phase = _.find(competition.phases, {status: 'Current'})
            return current_phase ? true : false
        }

        self.get_end_date = function (competition) {
            if(self.has_current_phase(competition)){
                let end_date = _.get(_.find(competition.phases, {status: 'Current'}), 'end')
                return end_date ? pretty_date(end_date) : 'Never'
            }else{
                return 'None'
            }
            
        }

        self.migrate_phase = function (phase_id) {
            CODALAB.api.manual_migration(phase_id)
                .done(data => {
                    toastr.success("Migration of this phase to the next should begin soon.")
                    self.close_modal(self.refs.migration_modal)
                })
                .fail(error => {
                    toastr.error('Something went wrong trying to migrate this phase.')
                })
        }

    </script>

    <style type="text/stylus">
        $blue = #2c3f4c
        $teal = #00bbbb
        $lightblue = #f2faff
        $red = #DB2828

        .detail-label
            font-size 1.25em
            text-transform uppercase
            color $teal
            font-family 'Overpass Mono', monospace

        .detail-item
            font-size 1.25em
            color $blue
            text-transform capitalize
            font-family 'Overpass Mono', monospace

        .competition-secret-key
            font-size 13px

        .contact-email
            font-size 1em
            color $teal
            font-family 'Overpass Mono', monospace

        .secret-label
            color $red

        .docker-label
            color $teal

        .report-label
            color $teal

        .secret-url
            color $blue

        .competition-name
            color $blue
            font-size 3em
            height auto
            line-height 1.1em
            text-transform uppercase
            font-weight 800

        .copy.icon
            cursor pointer

        .competition-image
            box-shadow 3px 3px 5px darkgrey

        .underline
            border-bottom 1px solid $teal
            display inline-block
            line-height 0.9em

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

        .reward-container
            background linear-gradient(to right, #ff9966, #ff5e62)
            color #fff
            border 1px solid #E6E9EB
            border-radius 5px
            padding 10px
            display flex
            align-items center
            margin-left 1rem

        .reward-icon
            width 40px
            height 40px
            margin-right 10px

        .reward-text
            font-size 24px
            font-weight 900
            display inline-block
    </style>
</comp-detail-header>
