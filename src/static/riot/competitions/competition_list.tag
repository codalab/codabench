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

        self.delete_competition = function (competition) {
            if (confirm("Are you sure you want to delete '" + competition.title + "'?")) {
                CODALAB.api.delete_competition(competition.id)
                    .done(function () {
                        self.update_competitions()
                        toastr.success("Competition deleted successfully")
                    })
                    .fail(function () {
                        toastr.error("Competition could not be deleted")
                    })
            }
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
