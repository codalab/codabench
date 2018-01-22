<data-management>
    <h1>Dataset Management</h1>

    <div class="ui divider"></div>

    <div class="ui two column grid">
        <div class="five wide column form-empty">
            <div class="ui segment">
                <h3>Form</h3>

                <form class="ui form" ref="form" onsubmit="{ save }">
                    <div class="field">
                        <input type="text" name="name" placeholder="Name">
                    </div>

                    <div class="field">
                        <select name="type" class="ui dropdown">
                            <option value="">Type</option>
                            <option value="-">----</option>
                            <option>Ingestion Program</option>
                            <option>Input Data</option>
                            <option>Public Data</option>
                            <option>Reference Data</option>
                            <option>Scoring Program</option>
                            <option>Starting Kit</option>
                        </select>
                    </div>

                    <div class="field">
                        <!--<input type="file" name="last-name" placeholder="Name">-->
                        <file-input name="data_file" accept=".zip"></file-input>
                    </div>
                    <!--<div class="ui right floated compact basic segment stepper">
                        <button class="ui button" type="submit">Submit</button>
                    </div>-->

                    <div class="field">
                        <div class="ui checkbox">
                            <input type="checkbox" name="is_public" tabindex="0" class="hidden">
                            <label>Public?</label>
                        </div>
                    </div>

                    <div class="ui grid">
                        <div class="sixteen wide column right aligned">
                            <button class="ui button" type="submit">
                                <i class="add circle icon"></i> Add new dataset
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <div class="eleven wide column">
            <div class="ui icon input">
                <input type="text" placeholder="Filter by name..." ref="search" onkeyup="{ filter }">
                <i class="search icon"></i>
            </div>
            <select class="ui dropdown" ref="type_filter" onchange="{ filter }">
                <option value="">Type</option>
                <option value="-">----</option>
                <option>Ingestion Program</option>
                <option>Input Data</option>
                <option>Public Data</option>
                <option>Reference Data</option>
                <option>Scoring Program</option>
                <option>Starting Kit</option>
            </select>

            <table class="ui celled compact table">
                <thead>
                <tr>
                    <th>Name</th>
                    <th width="175px">Type</th>
                    <th width="125px">Uploaded...</th>
                    <th width="50px">Public</th>
                    <th width="50px">Delete?</th>
                </tr>
                </thead>
                <tbody>
                <tr class="dataset-row" each="{ dataset, index in filtered_datasets }">
                    <td>{ dataset.name }</td>
                    <td>{ dataset.type }</td>
                    <td>{ timeSince(Date.parse(dataset.created_when)) } ago</td>
                    <td class="center aligned">
                        <i class="checkmark box icon green" show="{ dataset.public }"></i>
                    </td>
                    <td class="center aligned">
                        <button class="mini ui button red icon" onclick="{ delete_dataset.bind(this, dataset) }">
                            <i class="icon delete"></i>
                        </button>
                    </td>
                </tr>
                </tbody>
                <tfoot>
                <!--<tr>
                    <th colspan="3">
                        <div class="ui right floated pagination menu">
                            <a class="icon item">
                                <i class="left chevron icon"></i>
                            </a>
                            <a class="item">1</a>
                            <a class="item">2</a>
                            <a class="item">3</a>
                            <a class="item">4</a>
                            <a class="icon item">
                                <i class="right chevron icon"></i>
                            </a>
                        </div>
                    </th>
                </tr>-->
                </tfoot>
            </table>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.datasets = [
            /*{name: "Scoring Program", type: "Scoring Program", created_when: "Jan 21, 2018", public: true},
            {name: "Starting Kit", type: "Starting Kit", created_when: "Jan 1, 2018", public: true},
            {name: "Reference Data", type: "Reference Data", created_when: "Mar 21, 2017", public: true},
            {name: "Ingestion Program", type: "Ingestion Program", created_when: "Sep 24, 1988", public: true},*/
        ]
        // Clone of original
        self.filtered_datasets = self.datasets.slice(0)

        self.one("mount", function () {
            // Make semantic elements work
            $(".ui.dropdown").dropdown()
            $(".ui.checkbox").checkbox()

            // init
            self.update_datasets()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.filter = function () {
            // Delay makes this batch filters and only send one out after 100ms of not
            // receiving a call to filter
            delay(function () {
                // Clone of original
                self.filtered_datasets = self.datasets.slice(0)

                // Filters
                var search = self.refs.search.value.toLowerCase()
                var type = self.refs.type_filter.value
                console.log(type)

                if (search) {
                    self.filtered_datasets = self.filtered_datasets.filter(function (dataset) {
                        return dataset.name.toLowerCase().indexOf(search) >= 0
                    })
                }

                // A dash is the "N/A" filter option
                if (type && type !== "-") {
                    self.filtered_datasets = self.filtered_datasets.filter(function (dataset) {
                        return dataset.type === type
                    })
                }

                self.update()
            }, 100)
        }

        self.update_datasets = function () {
            CODALAB.api.get_datasets()
                .done(function (data) {
                    self.datasets = data

                    // We need to filter to actually display the results!
                    self.filter()

                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load datasets...")
                })
        }

        self.delete_dataset = function (dataset) {
            if (confirm("Are you sure you want to delete '" + dataset.name + "'?")) {
                CODALAB.api.delete_dataset(dataset.id)
                    .done(function () {
                        self.update_datasets()
                        toastr.success("Dataset deleted successfully!")
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete dataset!")
                    })
            }
        }

        self.save = function (event) {
            if (event) {
                event.preventDefault()
            }

            var data = $(self.refs.form).serializeJSON()

            // TODO: Upload the file, note: files aren't included in JSON data above,
            // we need to send file with like FormData(form object) or something weird,
            // IIRC...
        }
    </script>

    <style>
        .dataset-row:hover {
            cursor: pointer;
            background-color: rgba(46, 91, 183, 0.05);
        }
    </style>
</data-management>