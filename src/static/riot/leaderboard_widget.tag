<leaderboard-widget>

    <column-metric-modal></column-metric-modal>

    <div align="center" class="ui form">
        <div align="center" class="ui grid">
            <div align="center" class="ui centered row">
                <form id="leaderboard_form" class="ui form error" onsubmit="{ save_leaderboard }">
                    <table class="ui celled stackable table table-bordered">
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
                            <button class="ui tiny blue icon centered button" onclick="{ add_column }">
                                <i class="add square icon"></i>
                            </button>
                        </th>
                        </thead>
                        <tbody>
                        <tr align="center">
                            <td align="center" each="{ leaderboard_column_list }">
                                <input ref="main_column" name="main_column" align="center" type="radio" id="{ pk }"
                                       value="{ pk }">
                            </td>
                            <td align="center">Primary Column?</td>
                        </tr>
                        </tbody>
                    </table>
                </form>
                <h4 class="ui horizontal divider header">
                    <p>Leaderboard Form</p>
                </h4>
                <div align="center" class="ui centered segment leaderboard_actions">
                    <div align="center" class="ui centered buttons" show={ edit_mode }>
                        <input type="submit" class="ui large button" form="leaderboard_form" value="Save"/>
                        <div class="ui cancel button">Cancel</div>
                    </div>
                    <div align="center" hide={ edit_mode }>
                        <button class="ui large blue icon centered button"
                                onclick="{ edit_leaderboard.bind(this, selected_leaderboard) }">
                            Edit
                            <i class="setting icon"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize
        var self = this
        self.leaderboard_column_list = []
        self.leaderboard_selected_column_list = []
        self.selected_leaderboard = {}
        self.edit_mode = false

        self.one('mount', function () {
            self.update_metrics()
            self.update_columns()
        });

        self.update_form = function () {
            if (self.edit_mode){
                $("#leaderboard_form")[0].unlock()
            }
            else {
                $("#leaderboard_form")[0].lock()
            }
        }

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

        self.update_leaderboards = function () {
            CODALAB.api.get_leaderboards()
                .done(function (data) {
                    self.update({leaderboard_list: data})
                    console.log(self.leaderboard_list)
                })
                .fail(function (data) {
                    toastr.error("Error fetching leaderboard list: " + error.statusText)
                })
        };

        self.add_column = function () {
            if (self.leaderboard_column_list.length < 8) {
                self.leaderboard_column_list.push({name: "default"})
                self.update()
            }
        }

        /*         API            */

        self.edit_leaderboard = function (leaderboard) {
            self.selected_leaderboard = leaderboard

            self.refs.main_column.value = leaderboard.main_column

            self.update()
        }

        self.save_leaderboard = function (save_event) {
            // Stop the form from propagating
            save_event.preventDefault()

            self.update()

            var data = $("#leaderboard_form").serializeObject()
            var endpoint = undefined  // we'll pick form create OR update for the endpoint

            if (!self.selected_leaderboard.id) {
                endpoint = CODALAB.api.create_leaderboard(data)
            } else {
                endpoint = CODALAB.api.update_leaderboard(self.selected_leaderboard.id, data)

                self.selected_leaderboard = {}
            }

            endpoint
                .done(function (data) {
                    toastr.success("Successfully saved column")
                    var col_list = []

                    console.log(data)

                    self.update_leaderboards()

                    for (i = 0; i < 8; i++) {
                        var temp_element = document.getElementById("column_" + i);
                        if (temp_element) {
                            col_list.push(temp_element.value)
                        }
                    }
                    for (i = 0; i < col_list; i++) {
                        id = col_list[i]
                        for (j = 0; j < column_list.length; j++) {
                            temp_column_obj = column_list[i]
                            if (temp_column_obj.id === id) {
                                col_list[i] = temp_column_obj
                            }
                        }
                    }
                    console.log(col_list)
                    $("#leaderboard_form")[0].reset();
                })
                .fail(function (response) {
                    if (response) {
                        var errors = JSON.parse(response.responseText);

                        // Clean up errors to not be arrays but plain text
                        Object.keys(errors).map(function (key, index) {
                            errors[key] = errors[key].join('; ')
                        })

                        self.update({errors: errors})
                    }
                })
        }

        self.delete_leaderboard = function (leaderboard) {
            if (confirm("Are you sure you want to delete this?")) {
                CODALAB.api.delete_leaderboard(leaderboard.id)
                    .done(function () {
                        toastr.success("Deleted!")
                        self.update_leaderboards()
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete.\n\n" + response.responseText)
                    })
            }
        }


    </script>
</leaderboard-widget>