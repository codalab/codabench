<task-management>
    <div class="ui tabular menu">
        <div class="active item" data-tab="my_tasks">My Tasks</div>
        <div class="item" data-tab="public_tasks">Public Tasks</div>
    </div>
    <div class="ui active tab" data-tab="my_tasks">
        <div class="ui icon input">
            <input type="text" placeholder="Search by name..." ref="search_mine" onkeyup="{ search_my_tasks }">
            <i class="search icon"></i>
        </div>
        <div class="ui green right floated labeled icon button" onclick="{ show_modal }"><i class="add circle icon"></i> Create Task</div>
        <table class="ui celled compact table">
            <thead>
            <tr>
                <th>Name</th>
                <th width="125px">Uploaded...</th>
                <th width="50px">Public</th>
                <th width="50px">Delete?</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{ task in my_tasks }" class="task-row">
                <td><a href="{URLS.TASK_DETAIL(task.id)}">{ task.name }</a></td>
                <td>{ timeSince(Date.parse(task.created_when)) } ago</td>
                <td class="center aligned">
                    <i class="checkmark box icon green" show="{ task.is_public }"></i>
                </td>
                <td class="center aligned">
                    <button class="mini ui button red icon" onclick="{ delete_task.bind(this, task) }">
                        <i class="icon delete"></i>
                    </button>
                </td>
            </tr>
            </tbody>
            <tfoot>
            <!-- Pagination that we may want later...
            <tr>
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
            </tr>
            -->
            </tfoot>
        </table>
    </div>
    <div class="ui tab" data-tab="public_tasks">
        <div class="ui icon input">
            <input type="text" placeholder="Search by name..." ref="search_public" onkeyup="{ search_public_tasks }">
            <i class="search icon"></i>
        </div>
        <table class="ui celled compact table">
            <thead>
            <tr>
                <th>Name</th>
                <th width="125px">Uploaded...</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{ task in public_tasks }" class="task-row">
                <td><a href="{URLS.TASK_DETAIL(task.id)}">{ task.name }</a></td>
                <td>{ timeSince(Date.parse(task.created_when)) } ago</td>
            </tr>
            </tbody>
            <tfoot>
            <!-- Pagination that we may want later...
            <tr>
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
            </tr>
            -->
            </tfoot>
        </table>
    </div>

    <div class="ui modal" ref="modal">
        <div class="header">
            Create Task
        </div>
        <div class="content">
            <div class="ui pointing menu">
                <div class="active item modal-item" data-tab="details">Details</div>
                <div class="item modal-item" data-tab="data">Datasets</div>
            </div>
            <form class="ui form" ref="form">
                <div class="ui active tab" data-tab="details">
                    <div class="required field">
                        <label>Name</label>
                        <input name="name" placeholder="Name" ref="name" onkeyup="{ form_updated }">
                    </div>
                    <div class="required field">
                        <label>Description</label>
                        <textarea rows="4" name="description" placeholder="Description" ref="description" onkeyup="{ form_updated }"></textarea>
                    </div>
                </div>
                <div class="ui tab" data-tab="data">
                    <div>
                        <div class="two fields" data-no-js>
                            <div class="field {required: file_field === 'scoring_program'}"
                                 each="{file_field in ['scoring_program', 'ingestion_program']}">
                                <label>
                                    {_.startCase(file_field)}
                                    <span data-tooltip="Something useful to know...!" data-inverted=""
                                          data-position="bottom center"><i class=" grey help icon circle"></i></span>
                                </label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="{file_field}">
                                    <i class="search icon"></i>
                                    <input type="text" class="prompt">
                                    <div class="results"></div>
                                </div>
                            </div>
                        </div>

                        <div class="two fields" data-no-js>
                            <div class="field" each="{file_field in ['reference_data', 'input_data']}">
                                <label>
                                    {_.startCase(file_field)}
                                    <span data-tooltip="Something useful to know...!" data-inverted=""
                                          data-position="bottom center"><i class="grey help icon circle"></i></span>
                                </label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="{file_field}">
                                    <i class="search icon"></i>
                                    <input type="text" class="prompt">
                                    <div class="results"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </div>
        <div class="actions">
            <div class="ui primary button {disabled: !modal_is_valid}" onclick="{ create_task }">Create</div>
            <div class="ui cancel button">Cancel</div>
        </div>
    </div>

    <script>

        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/

        self.my_tasks = []
        self.public_tasks = []
        self.form_datasets = {}

        self.one("mount", function () {
            self.update_tasks()
            $('.ui.menu .item', self.root).tab()
            $('.ui.search.dataset', self.root).each(function (i, item) {
                $(item)
                    .search({
                        apiSettings: {
                            url: URLS.API + 'datasets/?search={query}&type=' + (item.dataset.name || ""),
                            onResponse: function (data) {
                                // Put results in array to use maxResults setting
                                var data_in_array = []

                                Object.keys(data).forEach(key => {
                                    // Get rid of "null" in semantic UI search results
                                    data[key].description = data[key].description || ''
                                    data_in_array.push(data[key])
                                })
                                return {results: data_in_array}
                            }
                        },
                        preserveHTML: false,
                        minCharacters: 2,
                        fields: {
                            title: 'name'
                        },
                        cache: false,
                        maxResults: 4,
                        onSelect: function (result, response) {
                            // It's hard to store the dataset information (hidden fields suck), so let's just put it here temporarily
                            // and grab it back on save
                            self.form_datasets[item.dataset.name] = result.key
                            self.form_updated()
                        }
                    })
            })
        })

        /*---------------------------------------------------------------------
         Modal Methods
        ---------------------------------------------------------------------*/
        self.show_modal = () => {
            $('.menu .item', self.root).tab('change tab', 'details')
            $(self.refs.modal).modal('show')

        }

        self.close_modal = () => {
            $(self.refs.modal).modal('hide')
            self.clear_form()
        }

        self.clear_form = () => {
            $(':input', self.refs.form)
                .not('[type="file"]')
                .not('button')
                .not('[readonly]').each(function (i, field) {
                $(field).val('')
            })
            self.form_datasets = {}
            self.modal_is_valid = false
        }

        self.create_task = () => {
            let data = get_form_data($(self.refs.form))
            _.assign(data, self.form_datasets)
            data.created_by = CODALAB.state.user.id
            CODALAB.api.create_task(data)
                .done((response) => {
                    toastr.success('Task Created')
                    self.close_modal()
                    self.update_my_tasks()
                })
                .fail((response) => {
                    toastr.error('Error Creating Task')
                })
        }

        self.form_updated = () => {
            self.modal_is_valid = $(self.refs.name).val() && $(self.refs.description).val() && self.form_datasets.scoring_program
            self.update()
        }

        /*---------------------------------------------------------------------
         Table Methods
        ---------------------------------------------------------------------*/
        self.update_tasks = function () {
            self.update_my_tasks()
            self.update_public_tasks()
        }

        self.update_my_tasks = function (filters) {
            filters = filters || {}
            filters.created_by = CODALAB.state.user.id
            CODALAB.api.get_tasks(filters)
                .done(function (data) {
                    self.my_tasks = data
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load tasks")
                })
        }

        self.update_public_tasks = function (filters) {
            filters = filters || {}
            filters.is_public = true
            CODALAB.api.get_tasks(filters)
                .done(function (data) {
                    self.public_tasks = data
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load tasks")
                })
        }

        self.search_my_tasks = function () {
            var filter = self.refs.search_mine.value

            delay(() => self.update_my_tasks({search: filter}), 100)
        }

        self.search_public_tasks = function () {
            var filter = self.refs.search_public.value

            delay(() => self.update_public_tasks({search: filter}), 100)
        }

        self.delete_task = function (task) {
            console.log(task)
            if (confirm("Are you sure you want to delete '" + task.name + "'?")) {
                CODALAB.api.delete_task(task.id)
                    .done(function () {
                        self.update_tasks()
                        toastr.success("Task deleted successfully!")
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete task!")
                    })
            }
        }
    </script>
    <style type="text/stylus">
        .task-row
            height: 42px;
    </style>
</task-management>
