<leaderboard-widget>

    <column-metric-modal></column-metric-modal>

    <div class="ui form">
        <div class="ui grid">
            <div class="ui row">
                <table class="ui celled stackable inverted table table-bordered">
                    <thead>
                        <th align="center" each="{column, i in leaderboard_column_list }">
                            <select id="column_{i}">
                                <option selected>
                                    ------
                                </option>
                                <option each="{ column_list }" value="{pk}">{name}</option>
                            </select>
                        </th>
                        <th align="center">
                            <button align="center" class="ui tiny blue icon button" onclick="{ add_column }">
                                <i class="add square icon"></i>
                            </button>
                        </th>
                    </thead>
                    <tbody>
                        <tr align="center">
                            <td align="center" each="{ leaderboard_column_list }">
                                <input align="center" name="main_column" type="radio" id="{ pk }" value="{ pk }">
                            </td>
                            <td align="center">Primary Column?</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Initialize
        var self = this
        self.leaderboard_column_list = []
        self.leaderboard_selected_column_list = []

        self.one('mount', function () {
            self.update_metrics()
            self.update_columns()
        });

        self.update_metrics = function () {
            CODALAB.api.get_metrics()
                .done(function (data) {
                    self.update({metric_list: data})
                })
                .fail(function (data) {
                    toastr.error("Error fetching metric list: " + error.statusText)
                })
        };

        self.update_columns = function () {
            CODALAB.api.get_columns()
                .done(function (data) {
                    self.update({column_list: data})
                    console.log(self.column_list)
                })
                .fail(function (data) {
                    toastr.error("Error fetching column list: " + error.statusText)
                })
        };

        self.add_column = function () {
            if (self.leaderboard_column_list.length < 8) {
                self.leaderboard_column_list.push({name: "default"})
                self.update()
            }
        }


    </script>
</leaderboard-widget>