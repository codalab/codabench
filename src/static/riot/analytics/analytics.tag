<analytics>


    <div>
        <h1>Analytics Tag Update</h1>
    </div>

    <div each="{year, y in users}">
        <h3>{y}</h3>
        <table>
            <tr>
                <th each="{month_count, month in year}">{month}</th>
            </tr>
            <tr>
                <td each="{month_count, month in year}">{month_count}</th>
            </tr>
        </table>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []


        self.one("mount", function () {
            console.log("analytics mounted")
            // Make semantic elements work
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()

            // init
            self.update_analytics()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/

        self.update_analytics= function () {
            CODALAB.api.get_analytics()
                .done(function (data) {
                    console.log(data)
                    self.update({users: data.monthly_total_users_joined, competitions: data.competition_count})
                })
                .fail(function (response) {
                    toastr.error("Could not load analytics data...")
                })
        }

    </script>
    <styles>
    </styles>

</analytics>
