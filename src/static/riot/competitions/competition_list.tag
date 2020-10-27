<competition-list>
    <div class="ui vertical stripe segment">
        <div class="ui middle aligned stackable grid container centered">
            <div class="row">
                <div class="fourteen wide column">
                    <div class="ui fluid secondary pointing tabular menu">
                        <a class="active item" data-tab="running">Competitions I'm Running</a>
                        <a class="item" data-tab="participating">Competitions I'm In</a>
                        <div class="right menu">
                            <div class="item">
                                <help_button href="https://github.com/codalab/competitions-v2/wiki/Competition-Management-&-List"></help_button>
                            </div>
                        </div>
                    </div>
                    <div class="ui active tab" data-tab="running">
                        <table class="ui celled compact table participation">
                            <thead>
                            <tr>
                                <th>Name</th>
                                <th width="100">Type</th>
                                <th width="125">Uploaded...</th>
                                <th width="50px">Publish</th>
                                <th width="50px">Edit</th>
                                <th width="50px">Delete</th>
                            </tr>
                            </thead>
                            <tbody>
                            <tr each="{ competition in running_competitions.results }" no-reorder>
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
                        <button if="{ running_competitions.previous }" onclick="{ change_page.bind(self, 'running', running_competitions.previous) }">PREV</button>
                        <button if="{ running_competitions.next }" onclick="{ change_page.bind(self, 'running', running_competitions.next) }">NEXT</button>
                    </div>
                    <div class="ui tab" data-tab="participating">
                        <table class="ui celled compact table">
                            <thead>
                            <tr>
                                <th>Name</th>
                                <th width="125px">Uploaded...</th>
                            </tr>
                            </thead>
                            <tbody>
                            <tr each="{ competition in participating_competitions.results }" style="height: 42px;">
                                <td><a href="{ URLS.COMPETITION_DETAIL(competition.id) }">{ competition.title }</a></td>
                                <td>{ timeSince(Date.parse(competition.created_when)) } ago</td>
                            </tr>
                            </tbody>
                            <tfoot>
                            </tfoot>
                        </table>
                        <button if="{ participating_competitions.previous }" onclick="{ change_page.bind(self, 'participating', participating_competitions.previous) }">PREV</button>
                        <button if="{ participating_competitions.next }" onclick="{ change_page.bind(self, 'participating', participating_competitions.next) }">NEXT</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this

        self.one("mount", function () {
            self.update_competitions()
            $('.tabular.menu .item').tab();
        })

        self.update_competitions = function () {
            self.get_participating_in_competitions()
            self.get_running_competitions()
        }

        self.get_competitions_wrapper = function (query_params) {
            return CODALAB.api.get_competitions(query_params)
                .fail(function (response) {
                    toastr.error("Could not load competition list")
                })
        }

        self.get_participating_in_competitions = function () {
            self.get_competitions_wrapper({participating_in: true})
                .done(function (data) {
                    self.participating_competitions = data
                    console.log("Participating Comps", self.participating_competitions)
                    self.update()
                })
        }

        self.get_running_competitions = function () {
            self.get_competitions_wrapper({
                mine: true,
                type: 'any',
            })
                .done(function (data) {
                    self.running_competitions = data
                    console.log("Running Competitions", self.running_competitions)
                    self.update()
                })
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

        self.change_page = function (page, url) {
            resp = $.ajax({
                type: 'get',
                url: url,
                contentType: "application/json",
                dataType: 'json'
            }).done(function (){
                console.log("RESP parsed JSON", JSON.parse(JSON.stringify(resp["responseJSON"])))
                self.update()
                if(page === "running"){
                    self.running_competitions = resp.responseJSON
                }
                else if(page === "participating"){
                    self.participating_competitions = resp.responseJSON
                }
                self.update()
            })
        }

        self.toggle_competition_publish = function (competition) {
            CODALAB.api.toggle_competition_publish(competition.id)
                .done(function (data) {
                    var published_state = data.published ? "published" : "unpublished"
                    toastr.success(`Competition has been ${published_state} successfully`)
                    self.get_running_competitions()
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
