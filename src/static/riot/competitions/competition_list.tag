<competition-list>
    <div class="ui vertical stripe segment">
        <div class="ui middle aligned stackable grid container centered">
            <div class="row">
                <div class="fourteen wide column">
                    <div class="ui fluid secondary pointing tabular menu">
                        <a class="active item" data-tab="running">Organizing</a>
                        <a class="item" data-tab="participating">Participating</a>
                        <div class="right menu">
                            <div class="item">
                                <help_button href="https://docs.codabench.org/latest/Organizers/Running_a_benchmark/Competition-Management-%26-List/"></help_button>
                            </div>
                        </div>
                    </div>
                    <div class="ui active tab" data-tab="running">
                        <table class="ui celled compact table participation">
                            <thead>
                            <tr>
                                <th>Name</th>
                                <th width="100">Type</th>
                                <th width="125">Uploaded</th>
                                <th width="50px">Publish</th>
                                <th width="50px">Edit</th>
                                <th width="50px">Delete</th>
                            </tr>
                            </thead>
                            <tbody>
                            <tr each="{ competition in organizing_competitions.results }" no-reorder>
                                <td><a href="{ URLS.COMPETITION_DETAIL(competition.id) }">{ competition.title }</a></td>
                                <td class="center aligned">{ competition.competition_type }</td>
                                <td>{ timeSince(Date.parse(competition.created_when)) } ago</td>
                                <td class="center aligned">
                                    <!--<button class="mini ui button green icon" show="{ !competition.published }" onclick="{ publish_competition.bind(this, competition) }">
                                        <i class="icon external alternate"></i>
                                    </button>-->
                                    <button class="mini ui button published icon { grey: !competition.published, green: competition.published }"
                                            onclick="{ toggle_competition_publish.bind(this, competition) }">
                                        <i class="icon file"></i>
                                    </button>
                                </td>
                                <td class="center aligned">
                                    <a href="{ URLS.COMPETITION_EDIT(competition.id) }"
                                       class="mini ui button blue icon">
                                        <i class="icon edit"></i>
                                    </a>
                                </td>
                                <td class="center aligned">
                                    <button class="mini ui button red icon"
                                            show="{ competition.created_by === CODALAB.state.user.username }"
                                            onclick="{ delete_competition.bind(this, competition) }">
                                        <i class="icon delete"></i>
                                    </button>
                                </td>
                            </tr>
                            </tbody>
                            <tfoot>
                            </tfoot>
                        </table>
                        <div class="pagination-nav" if="{organizing_competitions.next || organizing_competitions.previous}">
                            <button show="{organizing_competitions.previous}" onclick="{change_page.bind(this, 'organizing', -1)}" class="float-left ui inline button active">Back</button>
                            <button hide="{organizing_competitions.previous}" disabled="disabled" class="float-left ui inline button disabled">Back</button>
                            { organizing_page } of { Math.ceil(organizing_competitions.count / organizing_competitions.page_size) }
                            <button show="{organizing_competitions.next}" onclick="{change_page.bind(this, 'organizing', 1)}" class="float-right ui inline button active">Next</button>
                            <button hide="{organizing_competitions.next}" disabled="disabled" class="float-right ui inline button disabled">Next</button>
                        </div>
                    </div>
                    <div class="ui tab" data-tab="participating">
                        <table class="ui celled compact table">
                            <thead>
                            <tr>
                                <th>Name</th>
                                <th width="125px">Uploaded</th>
                            </tr>
                            </thead>
                            <tbody>
                            <tr each="{ competition in participating_in_competitions.results }" style="height: 42px;">
                                <td><a href="{ URLS.COMPETITION_DETAIL(competition.id) }">{ competition.title }</a></td>
                                <td>{ timeSince(Date.parse(competition.created_when)) } ago</td>
                            </tr>
                            </tbody>
                            <tfoot>
                            </tfoot>
                        </table>
                        <div class="pagination-nav" if="{participating_in_competitions.next || participating_in_competitions.previous}">
                            <button show="{participating_in_competitions.previous}" onclick="{change_page.bind(this, 'participating', -1)}" class="float-left ui inline button active">Back</button>
                            <button hide="{participating_in_competitions.previous}" disabled="disabled" class="float-left ui inline button disabled">Back</button>
                            { participating_page } of { Math.ceil(participating_in_competitions.count / participating_in_competitions.page_size) }
                            <button show="{participating_in_competitions.next}" onclick="{change_page.bind(this, 'participating', 1)}" class="float-right ui inline button active">Next</button>
                            <button hide="{participating_in_competitions.next}" disabled="disabled" class="float-right ui inline button disabled">Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Delete Competition Modal -->
    <div class="ui modal delete-competition" ref="delete_modal">
        <div class="header">Delete "{ competition_to_delete.title }"</div>
        <div class="scrolling content">
            <div class="ui active centered inline loader" if="{ !delete_preview }"></div>
            <!-- "ui form" makes checkbox labels white inside the red (inverted) section headers -->
            <div class="ui form" if="{ delete_preview }">
                <div class="ui negative message">
                    <strong>Deleting a competition is a permanent action which cannot be undone. Make sure that you check carefully all the details below.</strong>
                </div>

                <!-- Ticking this checkbox is required to enable the delete button -->
                <!-- A checked section's header turns red -->
                <div class="ui top attached { 'inverted red': delete_competition_data_checked, secondary: !delete_competition_data_checked } segment">
                    <div class="ui checkbox">
                        <input type="checkbox" ref="delete_competition_data" onchange="{ update_delete_checkboxes }">
                        <label><strong>Delete competition data</strong></label>
                    </div>
                </div>
                <div class="ui bottom attached segment">
                    <div class="ui relaxed list">
                        <div class="item">
                            <i class="file alternate outline icon"></i>
                            <div class="content">
                                <div class="header">Submissions</div>
                                <div class="description">
                                    { delete_preview.auto_delete.submissions.parent_count } submissions
                                    <virtual if="{ delete_preview.auto_delete.submissions.child_count }">
                                        with { delete_preview.auto_delete.submissions.child_count } child submissions (one per task)
                                    </virtual>,
                                    with their scores, prediction, scoring and detailed results, logs and submitted zips
                                    ({ delete_preview.auto_delete.submissions.file_count } files,
                                    { pretty_bytes(delete_preview.auto_delete.submissions.total_size) })
                                </div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="trophy icon"></i>
                            <div class="content">
                                <div class="header">Leaderboards and their columns</div>
                                <div class="description" each="{ leaderboard in delete_preview.auto_delete.leaderboards }">
                                    { leaderboard.title } (columns: { leaderboard.columns.join(', ') })
                                </div>
                                <div class="description" if="{ !delete_preview.auto_delete.leaderboards.length }">None</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="calendar alternate outline icon"></i>
                            <div class="content">
                                <div class="header">Phases</div>
                                <div class="description">{ delete_preview.auto_delete.phases.join(', ') || 'None' }</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="file alternate icon"></i>
                            <div class="content">
                                <div class="header">Pages</div>
                                <div class="description">{ delete_preview.auto_delete.pages.join(', ') || 'None' }</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="image icon"></i>
                            <div class="content">
                                <div class="header">Logo</div>
                                <div class="description">{ delete_preview.auto_delete.logo.join(', ') || 'None' }</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="archive icon"></i>
                            <div class="content">
                                <div class="header">Competition bundle</div>
                                <div class="description" each="{ data in delete_preview.auto_delete.bundle }">
                                    { data.file_name } ({ pretty_bytes(data.file_size) })
                                </div>
                                <div class="description" if="{ !delete_preview.auto_delete.bundle.length }">None</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="download icon"></i>
                            <div class="content">
                                <div class="header">Competition dumps</div>
                                <div class="description" each="{ data in delete_preview.auto_delete.dumps }">
                                    { data.file_name } ({ pretty_bytes(data.file_size) })
                                </div>
                                <div class="description" if="{ !delete_preview.auto_delete.dumps.length }">None</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="users icon"></i>
                            <div class="content">
                                <div class="header">Participants</div>
                                <div class="description">{ delete_preview.auto_delete.participants_count } participants</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="users cog icon"></i>
                            <div class="content">
                                <div class="header">Participant groups</div>
                                <div class="description" each="{ group in delete_preview.auto_delete.participant_groups }">
                                    { group.name } ({ group.members_count } members)
                                </div>
                                <div class="description" if="{ !delete_preview.auto_delete.participant_groups.length }">None</div>
                            </div>
                        </div>
                        <div class="item">
                            <i class="comments icon"></i>
                            <div class="content">
                                <div class="header">Forum</div>
                                <div class="description">
                                    { delete_preview.auto_delete.forum_threads_count } threads,
                                    { delete_preview.auto_delete.forum_posts_count } posts
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Items that cannot be deleted are disabled (muted) and wrapped in a secondary segment with a note -->
                <div class="ui top attached { 'inverted red': delete_tasks_checked, secondary: !delete_tasks_checked } segment">
                    <div class="ui checkbox">
                        <input type="checkbox" ref="delete_tasks" disabled="{ !delete_preview.tasks.length }" onchange="{ update_delete_checkboxes }">
                        <label><strong>Delete competition tasks</strong> with their datasets (ingestion program, scoring program, input data, reference data) and solutions</label>
                    </div>
                </div>
                <div class="ui bottom attached segment">
                    <div class="ui relaxed list">
                        <div class="item" each="{ task in delete_preview.tasks }">
                            <!-- Task used by another competition: the whole task is disabled, with the note on top -->
                            <div class="ui secondary segment" if="{ !task.can_delete }">
                                <p><i class="info circle icon"></i>This task and its dataset cannot be deleted because the task is being used by another competition.</p>
                                <div class="ui list">
                                    <div class="disabled item">
                                        <strong>{ task.name }</strong>
                                        <div class="list">
                                            <div class="item" each="{ data in task.datasets }">
                                                { data.type }: { data.file_name } ({ pretty_bytes(data.file_size) })
                                            </div>
                                            <div class="item" each="{ solution in task.solutions }">
                                                Solution: { solution.name }{ solution.dataset ? ' - ' + solution.dataset.file_name + ' (' + pretty_bytes(solution.dataset.file_size) + ')' : '' }
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- Task that can be deleted: only its datasets or solutions used elsewhere are disabled -->
                            <virtual if="{ task.can_delete }">
                                <strong>{ task.name }</strong>
                                <div class="list">
                                    <div class="item" each="{ data in task.datasets }">
                                        <div class="ui secondary segment" if="{ !data.can_delete }">
                                            <p><i class="info circle icon"></i>This dataset cannot be deleted because another task or competition uses it.</p>
                                            <div class="ui list">
                                                <div class="disabled item">{ data.type }: { data.file_name } ({ pretty_bytes(data.file_size) })</div>
                                            </div>
                                        </div>
                                        <virtual if="{ data.can_delete }">{ data.type }: { data.file_name } ({ pretty_bytes(data.file_size) })</virtual>
                                    </div>
                                    <div class="item" each="{ solution in task.solutions }">
                                        <div class="ui secondary segment" if="{ !solution.can_delete }">
                                            <p><i class="info circle icon"></i>This solution cannot be deleted because it is linked to another task.</p>
                                            <div class="ui list">
                                                <div class="disabled item">
                                                    Solution: { solution.name }{ solution.dataset ? ' - ' + solution.dataset.file_name + ' (' + pretty_bytes(solution.dataset.file_size) + ')' : '' }
                                                </div>
                                            </div>
                                        </div>
                                        <virtual if="{ solution.can_delete }">
                                            Solution: { solution.name }{ solution.dataset ? ' - ' + solution.dataset.file_name + ' (' + pretty_bytes(solution.dataset.file_size) + ')' : '' }
                                        </virtual>
                                    </div>
                                </div>
                            </virtual>
                        </div>
                        <div class="item" if="{ !delete_preview.tasks.length }">No tasks</div>
                    </div>
                </div>

                <div class="ui top attached { 'inverted red': delete_phase_datasets_checked, secondary: !delete_phase_datasets_checked } segment">
                    <div class="ui checkbox">
                        <input type="checkbox" ref="delete_phase_datasets" disabled="{ !delete_preview.phase_datasets.length }" onchange="{ update_delete_checkboxes }">
                        <label><strong>Delete phase datasets</strong> (starting kits and public data)</label>
                    </div>
                </div>
                <div class="ui bottom attached segment">
                    <div class="ui relaxed list">
                        <div class="item" each="{ data in delete_preview.phase_datasets }">
                            <div class="ui secondary segment" if="{ !data.can_delete }">
                                <p><i class="info circle icon"></i>This dataset cannot be deleted because a phase of another competition uses it.</p>
                                <div class="ui list">
                                    <div class="disabled item">{ data.type }: { data.file_name } ({ pretty_bytes(data.file_size) })</div>
                                </div>
                            </div>
                            <virtual if="{ data.can_delete }">{ data.type }: { data.file_name } ({ pretty_bytes(data.file_size) })</virtual>
                        </div>
                        <div class="item" if="{ !delete_preview.phase_datasets.length }">No phase datasets</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="actions">
            <button class="ui button" onclick="{ close_delete_modal }">Cancel</button>
            <button class="ui red button { loading: deleting }" disabled="{ !delete_preview || !delete_competition_data_checked || deleting }"
                    onclick="{ confirm_delete_competition }">
                <i class="trash icon"></i> Delete competition
            </button>
        </div>
    </div>
    <script>
        var self = this

        self.organizing_competitions = {}
        self.participating_in_competitions = {}
        self.organizing_page = 1
        self.participating_page = 1

        self.one("mount", function () {
            self.update_competitions()
            $('.tabular.menu .item').tab();
        })

        self.update_competitions = function () {
            self.get_participating_in_competitions()
            self.get_organizing_competitions()
        }

        self.get_competitions_wrapper = function (query_params) {
            return CODALAB.api.get_competitions(query_params)
                .fail(function (response) {
                    toastr.error("Could not load competition list")
                })
        }

        self.get_participating_in_competitions = function () {
            self.get_competitions_wrapper({participating_in: true, page: self.participating_page})
                .done(function (data) {
                    self.participating_in_competitions = data
                    self.update()
                })
        }

        self.get_organizing_competitions = function () {
            self.get_competitions_wrapper({
                mine: true,
                type: 'any',
                page: self.organizing_page,
            })
                .done(function (data) {
                    self.organizing_competitions = data
                    self.update()
                })
        }

        self.change_page = function (tab, direction) {
            if (tab === 'organizing') {
                self.organizing_page += direction
                self.get_organizing_competitions()
            } else {
                self.participating_page += direction
                self.get_participating_in_competitions()
            }
        }

        self.competition_to_delete = {}
        self.delete_preview = null
        self.delete_competition_data_checked = false
        self.delete_tasks_checked = false
        self.delete_phase_datasets_checked = false
        self.deleting = false

        self.delete_competition = function (competition) {
            self.competition_to_delete = competition
            self.delete_preview = null
            self.delete_competition_data_checked = false
            self.delete_tasks_checked = false
            self.delete_phase_datasets_checked = false
            self.update()
            // Only the Cancel button closes the modal, not a click outside it or the Escape key
            $(self.refs.delete_modal).modal({closable: false}).modal('show')
            CODALAB.api.get_competition_delete_preview(competition.id)
                .done(function (data) {
                    self.delete_preview = data
                    self.update()
                    // Reset the checkboxes from a previous delete
                    self.refs.delete_competition_data.checked = false
                    self.refs.delete_tasks.checked = false
                    self.refs.delete_phase_datasets.checked = false
                    $(self.refs.delete_modal).find('.ui.checkbox').checkbox()
                    $(self.refs.delete_modal).modal('refresh')
                })
                .fail(function () {
                    self.close_delete_modal()
                    toastr.error("Could not load what will be deleted")
                })
        }

        // Keeps track of the checkboxes: a checked section is shown in red,
        // and the delete button is enabled only when "Delete competition data" is checked
        self.update_delete_checkboxes = function () {
            self.delete_competition_data_checked = self.refs.delete_competition_data.checked
            self.delete_tasks_checked = self.refs.delete_tasks.checked
            self.delete_phase_datasets_checked = self.refs.delete_phase_datasets.checked
        }

        self.confirm_delete_competition = function () {
            self.deleting = true
            self.update()
            CODALAB.api.delete_competition(self.competition_to_delete.id, {
                delete_tasks: self.refs.delete_tasks.checked,
                delete_phase_datasets: self.refs.delete_phase_datasets.checked,
            })
                .done(function () {
                    self.close_delete_modal()
                    self.update_competitions()
                    toastr.success("Competition deleted successfully")
                })
                .fail(function () {
                    toastr.error("Competition could not be deleted")
                })
                .always(function () {
                    self.deleting = false
                    self.update()
                })
        }

        self.close_delete_modal = function () {
            $(self.refs.delete_modal).modal('hide')
        }

        self.toggle_competition_publish = function (competition) {
            CODALAB.api.toggle_competition_publish(competition.id)
                .done(function (data) {
                    var published_state = data.published ? "published" : "unpublished"
                    toastr.success(`Competition has been ${published_state} successfully`)
                    self.get_organizing_competitions()
                })
        }


    </script>
    <style type="text/stylus">
        .table.participation
            .published.icon.grey
                opacity 0.65
                transition 0.25s all ease-in-out

                &:hover
                    background-color #21ba45

    </style>
</competition-list>
