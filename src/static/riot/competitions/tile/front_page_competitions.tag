<front-page-competitions>
    <div class="vert-wrap {logged-in: CODALAB.state.user.logged_in}">
        <div class="segment-container ui segment">
            <div class="ui header">
                Popular Competitions
                <div class="sub-header-link">
                    <a href="#" class="view-all-comps">See more competitions</a>
                </div>
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
            <div class="sub-header-link">
                <a class="view-all-comps" href="#">See more competitions</a>
            </div>
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

    <style>
        .sub-header-link {
            line-height: 0.25em;
        }

        .view-all-comps {
            font-size: 0.5em;
            font-weight: 100;
        }

        .view-all-comps:hover {
            text-decoration: underline;
        }
    </style>
</front-page-competitions>