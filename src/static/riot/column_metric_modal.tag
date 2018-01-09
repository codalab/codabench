<column-metric-modal>
    <div class="ui grid">
        <div class="eight column row">
            <div class="ui center aligned inverted segment buttons">
                <button onclick="{ add_column }" class="ui large green labeled icon button">
                    <i class="columns icon"></i>
                    Add/Modify Columns
                </button>
                <button onclick="{ add_metric }" class="ui large blue labeled icon button">
                    <i class="legal icon"></i>
                    Add/Modify Metrics
                </button>
            </div>
        </div>
    </div>
    <h4 class="ui horizontal divider header">
        <p>Existing Leaderboard Objects</p>
    </h4>
    <!--- Begin Column Accordion -->
    <div class="ui styled fluid accordion">
        <div class="title">
            <i class="dropdown icon"></i>
            Columns:
        </div>
        <div class="content">
            <table class="ui celled inverted table table-bordered">
                <thead>
                <th>ID:</th>
                <th>Name:</th>
                <th>Metric ID:</th>
                <th>Delete:</th>
                <th>Edit:</th>
                </thead>
                <tbody>
                <tr each="{ column in column_list }">
                    <td>{ column.id }</td>
                    <td>{ column.name }</td>
                    <td>{ column.metric }</td>
                    <td>
                        <button class="ui tiny red icon button" onclick="{ delete_column.bind(this, column) }">
                            <i class="remove icon"></i>
                        </button>
                    </td>
                    <td>
                        <button class="ui tiny blue icon button" onclick="{ edit_column.bind(this, column) }">
                            <i class="setting icon"></i>
                        </button>
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
    <!--- End Column Accordion -->
    <h4 class="ui divider"></h4>
    <!--- Begin Metric Accordion -->
    <div class="ui styled fluid accordion">
        <div class="title">
            <i class="dropdown icon"></i>
            Metrics:
        </div>
        <div class="content">
            <table class="ui celled inverted table table-bordered">
                <thead>
                <th>ID:</th>
                <th>Name:</th>
                <th>Description:</th>
                <th>Key:</th>
                <th>Delete:</th>
                <th>Edit:</th>
                </thead>
                <tbody>
                <tr each="{ metric in metric_list }">
                    <td>{ metric.id }</td>
                    <td>{ metric.name }</td>
                    <td>{ metric.description }</td>
                    <td>{ metric.key }</td>
                    <td>
                        <button class="ui tiny red icon button" onclick="{ delete_metric.bind(this, metric) }">
                            <i class="remove icon"></i>
                        </button>
                    </td>
                    <td>
                        <button class="ui tiny blue icon button" onclick="{ edit_metric.bind(this, metric) }">
                            <i class="setting icon"></i>
                        </button>
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
    <!--- End Metric Accordion -->
    <h4 class="ui horizontal divider header">
        <p>Leaderboard Form</p>
    </h4>

    <!-- Form modal -->
    <div id="column_form_modal" class="ui modal">
        <div class="header">Column form</div>
        <div class="content">
            <form id="column_form" class="ui form error" onsubmit="{ save_column }">
                <div class="field">
                    <label for="name">Column Name:</label>
                    <input ref="name" name="name" placeholder="name">
                </div>

                <div class="field">
                    <label for="metric">Metric Object:</label>
                    <select ref="metric" name="metric" placeholder="metric">
                        <option each="{ metric in metric_list }" value="{ metric.pk }">{ metric.pk }-{ metric.name }</option>
                    </select>
                </div>

            </form>
        </div>
        <div class="actions">
            <input type="submit" class="ui button" form="column_form" value="Save"/>
            <div class="ui cancel button">Cancel</div>
        </div>
    </div>

    <!-- Form modal -->
    <div id="metric_form_modal" class="ui modal">
        <div class="header">Metric form</div>
        <div class="content">
            <form id="metric_form" class="ui form error" onsubmit="{ save_metric }">
                <div class="field">
                    <label for="name">Metric Name:</label>
                    <input ref="metric_name" name="name" placeholder="name">
                </div>

                <div class="field">
                    <label for="description">Description:</label>
                    <input ref="description" name="description" placeholder="description">
                </div>

                <div class="field">
                    <label for="key">Key:</label>
                    <input ref="key" name="key" placeholder="key">
                </div>

            </form>
        </div>
        <div class="actions">
            <input type="submit" class="ui button" form="metric_form" value="Save"/>
            <div class="ui cancel button">Cancel</div>
        </div>
    </div>

    <script>
        var self = this

        $(document).ready(function () {
            $('.ui.accordion').accordion();
        });

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
                })
                .fail(function (data) {
                    toastr.error("Error fetching column list: " + error.statusText)
                })
        };


        /*        Columns Javascript       */

        self.add_column = function () {
            $("#column_form_modal").modal('show')
            // We want to unselect the existing producer, so when we save we don't try to update it
            self.selected_column = {}
            self.update()
        }

        self.edit_column = function (column) {
            self.selected_column = column

            self.refs.name.value = column.name

            self.update()

            $("#column_form_modal").modal('show')
        }

        self.save_column = function (save_event) {
            // Stop the form from propagating
            save_event.preventDefault()

            self.update()

            var data = $("#column_form").serializeObject()
            var endpoint = undefined  // we'll pick form create OR update for the endpoint

            if (!self.selected_column.id) {
                endpoint = CODALAB.api.create_column(data)
            } else {
                endpoint = CODALAB.api.update_column(self.selected_column.id, data)

                self.selected_column= {}
            }

            endpoint
                .done(function (data) {
                    toastr.success("Successfully saved column")

                    self.update_columns()

                    $("#column_form_modal").modal('hide')

                    $("#column_form")[0].reset();
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

        self.delete_column = function (column) {
            if (confirm("Are you sure you want to delete this?")) {
                CODALAB.api.delete_column(column.id)
                    .done(function () {
                        toastr.success("Deleted!")
                        self.update_columns()
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete.\n\n" + response.responseText)
                    })
            }
        }




        /*          Metrics Javascript */



                self.add_metric = function () {
            $("#metric_form_modal").modal('show')
            // We want to unselect the existing producer, so when we save we don't try to update it
            self.selected_metric = {}
            self.update()
        }

        self.edit_metric = function (metric) {
            self.selected_metric = metric

            self.refs.metric_name.value = metric.name
            self.refs.description.value = metric.description
            self.refs.key.value = metric.key

            self.update()

            $("#metric_form_modal").modal('show')
        }

        self.save_metric = function (save_event) {
            console.log("I got called")
            // Stop the form from propagating
            save_event.preventDefault()

            self.update()

            var data = $("#metric_form").serializeObject()
            var endpoint = undefined  // we'll pick form create OR update for the endpoint

            if (!self.selected_metric.id) {
                endpoint = CODALAB.api.create_metric(data)
            } else {
                endpoint = CODALAB.api.update_metric(self.selected_metric.id, data)

                self.selected_metric= {}
            }

            endpoint
                .done(function (data) {
                    toastr.success("Successfully saved metric")

                    self.update_metrics()

                    $("#metric_form_modal").modal('hide')

                    $("#metric_form")[0].reset();
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

        self.delete_metric = function (metric) {
            if (confirm("Are you sure you want to delete this?")) {
                CODALAB.api.delete_metric(metric.id)
                    .done(function () {
                        toastr.success("Deleted!")
                        self.update_metrics()
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete.\n\n" + response.responseText)
                    })
            }
        }

    </script>
</column-metric-modal>