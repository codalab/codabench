<data-management>
    <h1>Dataset Management</h1>

    <div class="ui divider"></div>

    <div class="ui two column grid">
        <div class="column">
            <div class="ui icon input">
                <input type="text" placeholder="Filter by name..." ref="search" onkeyup="{ filter }">
                <i class="search icon"></i>
            </div>
            <select class="ui dropdown" ref="type" onchange="{ filter }">
                <option value="">Type</option>
                <option value="-">----</option>
                <option>Ingestion Program</option>
                <option>Input Data</option>
                <option>Public Data</option>
                <option>Reference Data</option>
                <option>Scoring Program</option>
                <option>Starting Kit</option>
            </select>

            <table class="ui celled table">
                <thead>
                <tr>
                    <th>Name</th>
                    <th width="175px">Type</th>
                    <th width="125px">Date added</th>
                    <th width="50px">Public</th>
                </tr>
                </thead>
                <tbody>
                <tr class="dataset-row" each="{ filtered_datasets }">
                    <td>{ name }</td>
                    <td>{ type }</td>
                    <td>{ created_when }</td>
                    <td class="center aligned">
                        <i class="checkmark box icon green" show="{ public }"></i>
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

        <div class="column form-empty">
            <div class="ui segment">
                <h3>Form</h3>

                <form class="ui form" onsubmit="{ save }">
                    <div class="field">
                        <input type="text" placeholder="Name">
                    </div>
                    <div class="field">
                        <!--<input type="file" name="last-name" placeholder="Name">-->
                        <file-input accept=".zip"></file-input>
                    </div>
                    <!--<div class="ui right floated compact basic segment stepper">
                        <button class="ui button" type="submit">Submit</button>
                    </div>-->

                    <div class="field">
                        <div class="ui checkbox">
                            <input type="checkbox" tabindex="0" class="hidden">
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
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.datasets = [
            {name: "Scoring Program", type: "Scoring Program", created_when: "Jan 21, 2018", public: true},
            {name: "Starting Kit", type: "Starting Kit", created_when: "Jan 1, 2018", public: true},
            {name: "Reference Data", type: "Reference Data", created_when: "Mar 21, 2017", public: true},
            {name: "Ingestion Program", type: "Ingestion Program", created_when: "Sep 24, 1988", public: true},
        ]
        // Clone of original
        self.filtered_datasets = self.datasets.slice(0)

        self.one("mount", function () {
            $(".ui.dropdown").dropdown()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.filter = function() {
            // Clone of original
            self.filtered_datasets = self.datasets.slice(0)

            // Filters
            var search = self.refs.search.value.toLowerCase()
            var type = self.refs.type.value
            console.log(type)

            if(search) {
                self.filtered_datasets = self.filtered_datasets.filter(function (dataset) {
                    return dataset.name.toLowerCase().indexOf(search) >= 0
                })
            }

            // A dash is the "N/A" filter option
            if(type && type !== "-") {
                self.filtered_datasets = self.filtered_datasets.filter(function (dataset) {
                    return dataset.type === type
                })
            }

            self.update()
        }

        self.save = function(event) {
            if(event) {
                event.preventDefault()
            }
        }
    </script>

    <style>
        .dataset-row:hover {
            cursor: pointer;
            background-color: rgba(46, 91, 183, 0.05);
        }
    </style>
</data-management>