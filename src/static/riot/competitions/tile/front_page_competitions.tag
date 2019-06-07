<front-page-competitions>
    <div hide="{CODALAB.state.user.logged_in}" class="vert-wrap">
        <div class="segment-container ui segment">
            <div class="ui header">
                Popular Competitions
            </div>
            <div class="container-content">
                <div class="loader-container popular">
                    <div class="lds-ring">
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>
                    </div>
                </div>
                <competition-tile each="{popular_competitions}"></competition-tile>
            </div>
        </div>

        <div class="segment-container ui segment">
            <div class="ui header">
                Featured Competitions
            </div>
            <div class="container-content">
                <div class="loader-container popular">
                    <div class="lds-ring">
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>
                    </div>
                </div>
                <competition-tile each="{featured_competitions}"></competition-tile>
            </div>
        </div>
    </div>

    <div show={CODALAB.state.user.logged_in} class="vert-wrap logged-in">
        <div class="segment-container ui segment">
            <div class="ui header">
                Popular Competitions
            </div>
            <div class="container-content">
                <div class="loader-container popular">
                    <div class="lds-ring">
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>
                    </div>
                </div>
                <competition-tile each="{popular_competitions}"></competition-tile>
            </div>
        </div>
        <div class="segment-container ui segment">
            <div class="ui header">
                Featured Competitions
            </div>
            <div class="container-content">
                <div class="loader-container popular">
                    <div class="lds-ring">
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>
                    </div>
                </div>
                <competition-tile each="{featured_competitions}"></competition-tile>
            </div>
        </div>
    </div>

    <script>
        var self = this

        self.one("mount", function () {
            self.get_frontpage_competitions()
        })

        self.get_frontpage_competitions = function (data) {
            return CODALAB.api.get_front_page_competitions(data)
                .fail(function (response) {
                    toastr.error("Could not load competition list")
                })
                .done(function (data) {
                    self.featured_competitions = data["featured_comps"]
                    self.popular_competitions = data["popular_comps"]
                    self.update()
                    $('.loader-container').hide()
                })
        }
    </script>
</front-page-competitions>