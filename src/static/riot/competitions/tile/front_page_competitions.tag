<front-page-competitions>
    <div class="ui two column grid">
        <div class="eight wide column">
            <div class="ui large header">
                <a href="/competitions/public/">Popular Benchmarks</a>
            </div>
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

        <div class="eight wide column">
            <div class="ui large header">
                <a href="/competitions/public/">Featured Benchmarks</a>
            </div>
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
        front-page-competitions {
            margin: 3em 1.5em;
        }

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
