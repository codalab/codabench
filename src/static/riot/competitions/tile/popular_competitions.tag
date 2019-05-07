<popular-competitions>
    <competition-tile each="{popular_competitions}"></competition-tile>

    <script>
        var self = this

        self.one("mount", function () {
            self.update_competitions()
        })

        self.get_competitions_wrapper = function (query_params) {
            return CODALAB.api.get_competitions(query_params)
                .fail(function (response) {
                    toastr.error("Could not load competition list")
                })
        }

        self.update_competitions = function () {
            self.get_popular_competitions()
        }

        self.get_popular_competitions = function () {
            self.get_competitions_wrapper()
                .done(function (data) {
                    self.popular_competitions = data
                    self.update()
                })
        }
    </script>
</popular-competitions>
