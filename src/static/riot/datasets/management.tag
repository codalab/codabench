<data-management>
    <h1>Dataset Management</h1>

    <div class="ui divider"></div>

    <div class="ui two column grid">
        <div class="five wide column form-empty">
            <div class="ui segment">
                <h3>Form</h3>

                <div class="ui message error" show="{ Object.keys(errors).length > 0 }">
                    <div class="header">
                        Error(s) creating dataset
                    </div>
                    <ul class="list">
                        <li each="{ error, field in errors }">
                            <strong>{field}:</strong> {error}
                        </li>
                    </ul>
                </div>

                <form class="ui form {error: errors}" ref="form" onsubmit="{ save }">
                    <!--<div class="field">
                        <input type="text" name="name" placeholder="Name">
                    </div>-->
                    <input-text name="name" ref="name" error="{errors.name}" placeholder="Name"></input-text>

                    <div class="field {error: errors.type}">
                        <select name="type" ref="type" class="ui dropdown">
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

                    <input-file name="data_file" error="{errors.data_file}" accept=".zip"></input-file>

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

                <div class="ui indicating progress" style="margin: 0; height: 0; -ms-flex: 1 0 auto; flex: 1 0 auto; overflow: hidden;" ref="progress">
                    <div class="bar" style="height: 24px;">
                        <div class="progress">{ upload_progress }%</div>
                    </div>
                </div>
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
                        <i class="checkmark box icon green" show="{ dataset.is_public }"></i>
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
        self.errors = []
        self.datasets = [
            /*{name: "Scoring Program", type: "Scoring Program", created_when: "Jan 21, 2018", public: true},
            {name: "Starting Kit", type: "Starting Kit", created_when: "Jan 1, 2018", public: true},
            {name: "Reference Data", type: "Reference Data", created_when: "Mar 21, 2017", public: true},
            {name: "Ingestion Program", type: "Ingestion Program", created_when: "Sep 24, 1988", public: true},*/
        ]
        // Clone of original
        self.filtered_datasets = self.datasets.slice(0)
        self.upload_progress = undefined

        self.one("mount", function () {
            // Make semantic elements work
            $(".ui.dropdown").dropdown()
            $(".ui.checkbox").checkbox()

            // init
            self.update_datasets()


            /*var percent = 0;
            var loopy = function () {
                percent += .1
                if (percent > 1) {
                    self.clear_form()
                    return
                }
                self.file_upload_progress_handler(percent)
                window.setTimeout(loopy, 250)
            }
            loopy()

            setTimeout(function () {
                $('form input[name="name"]').val('awefjk' + (Math.floor(Math.random() * 20)))
                $('form select[name="type"]').dropdown('set selected', 'Ingestion Program')
            }, 100)*/
            //self.refs.progress.style.height = '24px'


        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.show_progress_bar = function() {
            // The transition delays are for timing the animations, so they're one after the other
            self.refs.form.style.transitionDelay = '0s'
            self.refs.form.style.maxHeight = 0
            self.refs.form.style.overflow = 'hidden'

            self.refs.progress.style.transitionDelay = '1s'
            self.refs.progress.style.height = '24px'
        }

        self.hide_progress_bar = function() {
            // The transition delays are for timing the animations, so they're one after the other
            self.refs.progress.style.transitionDelay = '0s'
            self.refs.progress.style.height = 0

            self.refs.form.style.transitionDelay = '.1s'
            self.refs.form.style.maxHeight = '1000px'
            setTimeout(function() {
                // Do this after transition has been totally completed
                self.refs.form.style.overflow = 'visible'
            }, 1000)
        }

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

        self.file_upload_progress_handler = function (upload_progress) {
            if(self.upload_progress === undefined) {
                // First iteration of this upload, nice transitions
                self.show_progress_bar()
            }

            self.upload_progress = upload_progress * 100;
            $(self.refs.progress).progress({percent: self.upload_progress})
            self.update();
        }

        self.clear_form = function () {
            // Clear form
            $(':input', self.refs.form)
                .not(':button, :submit, :reset, :hidden')
                .val('')
                .removeAttr('checked')
                .removeAttr('selected');

            $('.dropdown', self.refs.form).dropdown('restore defaults')

            self.upload_progress = undefined

            self.errors = {}
            self.update()
        }

        self.save = function (event) {
            if (event) {
                event.preventDefault()
            }

            // We don't want to send "" as a type and get a weird error, so clear that if empty
            if (self.refs.type.value === "") {
                self.refs.type.value = undefined
            }

            // Have to get the "FormData" to get the file in a special way
            // jquery likes to work with
            var data = new FormData(self.refs.form)

            CODALAB.api.create_dataset(data, self.file_upload_progress_handler)
                .done(function (data) {
                    //data = xml_to_json(data);
                    //success_callback(data);
                    toastr.success("Dataset successfully uploaded!")
                    self.update_datasets()
                    self.clear_form()
                    self.hide_progress_bar()
                })
                .fail(function (response) {
                    if (response) {
                        var errors = JSON.parse(response.responseText);

                        // Clean up errors to not be arrays but plain text
                        Object.keys(errors).map(function (key, index) {
                            errors[key] = errors[key].join('; ')
                        })

                        console.log(errors)

                        self.update({errors: errors})
                    }
                    toastr.error("Creation failed, error occurred");
                });
        }
    </script>

    <style>
        .dataset-row:hover {
            background-color: rgba(46, 91, 183, 0.05);
        }

        *, div {

        }

        .progress {
            -webkit-transition: all .1s ease-in-out;
            -moz-transition: all .1s ease-in-out;
            -o-transition: all .1s ease-in-out;
            transition: all .1s ease-in-out;
        }

        form {
            max-height: 1000px;  /* a max height we'll never hit, useful for CSS transitions */

            -webkit-transition: all 1s ease-in-out;
            -moz-transition: all 1s ease-in-out;
            -o-transition: all 1s ease-in-out;
            transition: all 1s ease-in-out;
        }
    </style>
</data-management>