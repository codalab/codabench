<front-page-competitions>
    <div class="ui two column grid">
        <div class="eight wide column">
            <div class="ui large header">
                Popular Benchmarks
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
            <a class="show-more" href="/competitions/public/?ordering=popular">Show more</a>
        </div>

        <div class="eight wide column">
            <div class="ui large header">
                Recent Benchmarks
            </div>
            <div class="loader-container popular">
                <div class="lds-ring">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
            </div>
            <competition-tile each="{recent_competitions}"></competition-tile>
            <a class="show-more" href="/competitions/public/?ordering=recent">Show more</a>
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
                    self.recent_competitions = data["recent_comps"]
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

        .show-more {
            display: block;
            width: fit-content;
            margin: 20px auto;
            padding: 10px 20px;
            background-color: #4a6778;
            color: white;
            text-align: center;
            border-radius: 5px;
            font-size: 1.1em;
            text-decoration: none;
            transition: background-color 0.3s, transform 0.3s;
        }

        .show-more:hover {
            background-color: #467799;
            transform: scale(1.05);
            text-decoration: none;
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
