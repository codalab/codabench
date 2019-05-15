<featured-competitions>
    <div class="loader-container">
        <div class="lds-ripple">
            <div></div>
            <div></div>
        </div>
    </div>
    <competition-tile each="{featured_competitions}"></competition-tile>
    <script>
        var self = this

        self.one("mount", function () {
            self.update_competitions()
        })

        self.update_competitions = function () {
            self.get_featured_competitions()
        }

        self.get_competitions_wrapper = function (data) {
            return CODALAB.api.get_front_page_competitions(data)
                .fail(function (response) {
                    toastr.error("Could not load competition list")
                })
        }

        self.get_featured_competitions = function () {
            self.get_competitions_wrapper()
                .done(function (data) {
                    self.featured_competitions = data["featured_comps"]
                    self.update()
                })
        }

    </script>
</featured-competitions>
