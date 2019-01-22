<competition-list>
    <div class="ui vertical stripe segment">
        <div class="ui middle aligned stackable grid container centered">
            <div class="row">
                <div class="fourteen wide column">
                    <!-- <div class="ui divided items">
                        <competition-tile each="{competition in competitions}"></competition-tile>
                    </div> -->
                    <table class="ui celled compact table">
                        <thead>
                        <tr>
                            <th>Name</th>
                            <!--<th width="175px">Type</th>-->
                            <th width="125px">Uploaded...</th>
                            <th width="50px">Publish</th>
                            <th width="50px">Edit</th>
                            <th width="50px">Delete</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr each="{ competition in competitions }">
                            <td><a href="{ URLS.COMPETITION_DETAIL(competition.id) }">{ competition.title }</a></td>
                            <td>{ timeSince(Date.parse(competition.created_when)) } ago</td>
                            <td class="center aligned">
                                <button class="mini ui button green icon" show="{ !competition.published }" onclick="{ publish_competition.bind(this, competition) }">
                                    <i class="icon external alternate"></i>
                                </button>
                                <button class="mini ui button grey icon" show="{ competition.published }" onclick="{ unpublish_competition.bind(this, competition) }">
                                    <i class="icon file alternate"></i>
                                </button>
                            </td>
                            <td class="center aligned">
                                <a href="{ URLS.COMPETITION_EDIT(competition.id) }" class="mini ui button blue icon"><i
                                        class="icon edit"></i> </a>
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

                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this

        self.one("mount", function () {
            self.update_competitions()
        })

        self.update_competitions = function () {
            CODALAB.api.get_competitions("?mine=true")
                .done(function (data) {
                    self.competitions = data
                    console.log(self.competitions)
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load competition list....")
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

        self.publish_competition = function (competition) {
            CODALAB.api.toggle_competition_publish(competition.id)
                .done(function () {
                    toastr.success('Competition has been publish successfully')
                    self.update_competitions()
                })
        }
        self.unpublish_competition = function (competition) {
            CODALAB.api.toggle_competition_publish(competition.id)
                .done(function () {
                    toastr.success('Competition has been unpublish successfully')
                    self.update_competitions()
                })
        }


    </script>
</competition-list>
