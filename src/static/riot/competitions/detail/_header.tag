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
                            <div>
                                <span class="detail-label">Organized by:</span>
                                <span class="detail-item">{competition.created_by}</span>
                            </div>
                            <div>
                                <span class="detail-label">Current phase ends:</span>
                                <span class="detail-item">{get_end_date(competition)}</span>
                            </div>
                            <div class="competition-secret-key" if="{ competition.admin }">
                                <span class="secret-label">Secret url:</span>
                                <span id="secret-url">https://{ URLS.SECRET_KEY_URL(competition.id, competition.secret_key) }</span>
                                <span onclick="{copy_secret_url}" class="ui send-pop" data-content="Copied!">
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
                        <a class="ui tiny basic red label">{competition.participant_count}</a>
                        <div class="ui tiny red button">Participants</div>
                    </div>
                    <div class="ui tiny left labeled fluid button">
                        <a class="ui tiny basic teal label">{competition.submission_count}</a>
                        <div class="ui tiny teal button">Submissions</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- Manage Competition Modal -->
    <div class="ui manage-competition modal" ref="files_modal">
        <div class="content">
            <button class="ui icon button" onclick="{create_dump}">
                <i class="download icon"></i> Create Competition Dump
            </button>
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
                </tbody>
            </table>
        </div>
    </div>
    <!-- Manage Submissions Modal -->
    <div class="ui manage-submissions modal" ref="sub_modal">
        <div class="content">
            <submission-manager admin="{competition.admin}" competition="{ competition }"></submission-manager>
        </div>
    </div>

    <!-- Manage Participants Modal -->
    <!--
    <div class="ui manage-participants modal" ref="participant_modal">
        <div class="content">
            <participant-manager></participant-manager>
        </div>
    </div>

    <div class="ui basic modal" ref="dump_modal">
        <div class="header">
            Creating Competition Dump
        </div>
        <div class="content">
            Success! Your competition dump is being created. This may take some time.
            If the files table does not update with the new dump, try refreshing the table.
        </div>
        <div class="actions">
            <div class="ui primary inverted ok button">Dismiss</div>
        </div>
    </div>
    -->

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

        self.create_dump = () => {
            CODALAB.api.create_dump(self.competition.id)
                .done(data => {
                    toastr.success("Success! Your competition dump is being created.")
                    //$(self.refs.dump_modal).modal('show')
                    //setTimeout(self.update_files, 2000)
                })
                .fail(response => {
                    toastr.error("Error trying to create competition dump.")
                })
        }

        self.update_files = (e) => {
            CODALAB.api.get_competition_files(self.competition.id)
                .done(data => {
                    self.files = data
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


        self.copy_secret_url = function () {
            let range = document.createRange();
            range.selectNode(document.getElementById("secret-url"));
            window.getSelection().removeAllRanges(); // clear current selection
            window.getSelection().addRange(range); // to select text
            document.execCommand("copy");
            window.getSelection().removeAllRanges();// to deselect
            $('.send-pop').popup('toggle')
        }

        self.get_end_date = function (competition) {
            let end_date = _.get(_.find(competition.phases, {status: 'Current'}), 'end')
            return end_date ? pretty_date(end_date) : 'Never'
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

        .secret-label
            color #DB2828

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
    </style>
</comp-detail-header>
