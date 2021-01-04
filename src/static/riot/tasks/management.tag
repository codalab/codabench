<task-management>
    <div class="ui icon input">
        <input type="text" placeholder="Search by name..." ref="search" onkeyup="{filter.bind(this, undefined)}">
        <i class="search icon"></i>
    </div>
    <div class="ui checkbox" onclick="{ filter.bind(this, undefined) }">
        <label>Show Public Tasks</label>
        <input type="checkbox" ref="public">
    </div>
    <div selenium="create-task" class="ui green right floated labeled icon button" onclick="{ show_modal }"><i class="add circle icon"></i>
        Create Task
    </div>
    <button class="ui red right floated labeled icon button {disabled: marked_tasks.length === 0}" onclick="{delete_tasks}">
        <i class="icon delete"></i>
        Delete Selected Tasks
    </button>

    <table class="ui {selectable: tasks.length > 0} celled compact table">
        <thead>
        <tr>
            <th>Name</th>
            <th class="benchmark-row">Benchmarks</th>
            <th width="125px">Uploaded...</th>
            <th width="50px">Public</th>
            <th width="50px">Delete?</th>
            <th width="25px"></th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ task in tasks }" onclick="{show_detail_modal.bind(this, task)}" class="task-row">
            <td>{ task.name }</td>
            <td class="benchmark-row">{ task.competitions.join(', ') }</td>
            <td>{ timeSince(Date.parse(task.created_when)) } ago</td>
            <td class="center aligned">
                <i class="checkmark box icon green" show="{ task.is_public }"></i>
            </td>
            <td class="center aligned">
                <button class="mini ui button red icon" onclick="{ delete_task.bind(this, task) }">
                    <i class="icon delete"></i>
                </button>
            </td>
            <td class="center aligned">
                <div class="ui fitted checkbox">
                    <input type="checkbox" name="delete_checkbox" onclick="{ mark_task_for_deletion.bind(this, task) }">
                    <label></label>
                </div>
            </td>
        </tr>

        <tr if="{tasks.length === 0}">
            <td class="center aligned" colspan="4">
                <em>No Tasks Yet!</em>
            </td>
        </tr>
        </tbody>
        <tfoot>
        <!-------------------------------------
                  Pagination
        ------------------------------------->
        <tr if="{tasks.length > 0}">
            <th colspan="6">
                <div class="ui right floated pagination menu" if="{tasks.length > 0}">
                    <a show="{!!_.get(pagination, 'previous')}" class="icon item" onclick="{previous_page}">
                        <i class="left chevron icon"></i>
                    </a>
                    <div class="item">
                        <label>{page}</label>
                    </div>
                    <a show="{!!_.get(pagination, 'next')}" class="icon item" onclick="{next_page}">
                        <i class="right chevron icon"></i>
                    </a>
                </div>
            </th>
        </tr>
        </tfoot>
    </table>

    <div class="ui modal" ref="detail_modal">
        <div class="header">
            {selected_task.name}
        </div>
        <div class="content">
            <h4>{selected_task.description}</h4>
            <div class="ui divider" show="{selected_task.description}"></div>
            <div><strong>Created By:</strong> {selected_task.created_by}</div>
            <div><strong>Key:</strong> {selected_task.key}</div>
            <div><strong>Has Been Validated
                <span data-tooltip="A task has been validated once one of its solutions has successfully been run against it">
                    <i class="question circle icon"></i>
                </span>:</strong> {selected_task.validated ? "Yes" : "No"}</div>
            <div><strong>Is Public:</strong> {selected_task.is_public ? "Yes" : "No"}</div>
            <div if="{selected_task.validated}"
                 class="ui right floated small green icon button"
                 onclick="{toggle_task_is_public}">
                <i class="share icon"></i> {selected_task.is_public ? 'Make Private' : 'Make Public'}
            </div>
            <div class="ui secondary pointing green two item tabular menu">
                <div class="active item" data-tab="files">Files</div>
                <div class="item" data-tab="solutions">Solutions</div>
            </div>
            <div class="ui active tab" data-tab="files">
                <table class="ui table">
                    <thead>
                    <tr>
                        <th>Type</th>
                        <th>Name</th>
                        <th></th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr each="{file in file_types}" if="{selected_task[file]}">
                        <td>{selected_task[file].type}</td>
                        <td>{selected_task[file].name}</td>
                        <td class="collapsing">
                            <span data-tooltip="Download this dataset">
                                <a href="{URLS.DATASET_DOWNLOAD(selected_task[file].key)}">
                                    <i class="download green icon"></i>
                                </a>
                            </span>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
            <div class="ui tab" data-tab="solutions">
                <table class="ui table">
                    <thead>
                    <tr>
                        <th>Solutions</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr each="{solution in selected_task.solutions}">
                        <td><a href="{URLS.DATASET_DOWNLOAD(solution.data)}">{solution.name}</a></td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="actions">
            <button class="ui cancel button">Close</button>
        </div>
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
                        <input selenium="name2" name="name" placeholder="Name" ref="name" onkeyup="{ form_updated }">
                    </div>
                    <div class="required field">
                        <label>Description</label>
                        <textarea selenium="task-desc" rows="4" name="description" placeholder="Description" ref="description"
                                  onkeyup="{ form_updated }"></textarea>
                    </div>
                </div>
                <div class="ui tab" data-tab="data">
                    <div>
                        <div class="two fields" data-no-js>
                            <div class="field {required: file_field === 'scoring_program'}"
                                 each="{file_field in ['scoring_program', 'ingestion_program']}">
                                <label>
                                    {_.startCase(file_field)}
                                </label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="{file_field}">
                                    <i class="search icon"></i>
                                    <input  type="text" class="prompt" id="{file_field}">
                                    <div selenium="scoring-program" class="results"></div>
                                </div>
                            </div>
                        </div>

                        <div class="two fields" data-no-js>
                            <div class="field" each="{file_field in ['reference_data', 'input_data']}">
                                <label>
                                    {_.startCase(file_field)}
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
            <div selenium="save-task" class="ui primary button {disabled: !modal_is_valid}" onclick="{ create_task }">Create</div>
            <div class="ui basic red cancel button">Cancel</div>
        </div>
    </div>

    <script>

        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/

        self.marked_tasks = []
        self.tasks = []
        self.form_datasets = {}
        self.selected_task = {}
        self.page = 1
        self.file_types = [
            'input_data',
            'reference_data',
            'scoring_program',
            'ingestion_program'
        ]


        self.one("mount", function () {
            self.update_tasks()
            $(".ui.checkbox", self.root).checkbox()
            $('.ui.search.dataset', self.root).each(function (i, item) {
                $(item)
                    .search({
                        apiSettings: {
                            url: URLS.API + 'datasets/?search={query}&type=' + (item.dataset.name || ""),
                            onResponse: function (data) {
                                let results = _.map(data.results, result => {
                                    result.description = result.description || ''
                                    return result
                                })

                                return {results: results}
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
                    self.update_tasks()
                })
                .fail((response) => {
                    toastr.error('Error Creating Task')
                })
        }

        self.toggle_task_is_public = () => {
            let message = self.selected_task.is_public
                ? 'Are you sure you want to make this task private? It will no longer be available to other users.'
                : 'Are you sure you want to make this task public? It will become visible to everyone'
            if (confirm(message)) {
                CODALAB.api.update_task(self.selected_task.id, {id: self.selected_task.id, is_public: !self.selected_task.is_public})
                    .done(data => {
                        toastr.success('Task updated')
                        self.selected_task = data
                        self.update()
                    })
                    .fail(resp => {
                        toastr.error(resp.responseJSON['is_public'])
                    })
            }
        }

        self.form_updated = () => {
            self.modal_is_valid = $(self.refs.name).val() && $(self.refs.description).val() && self.form_datasets.scoring_program
            self.update()
        }

        self.show_detail_modal = (task, e) => {
            // Return here so the detail modal doesn't pop up when a checkbox is clicked
            if (e.target.type === 'checkbox') {
                return
            }
            CODALAB.api.get_task(task.id)
                .done((data) => {
                    self.selected_task = data
                    self.update()
                })
            $(self.refs.detail_modal).modal('show')
        }

        /*---------------------------------------------------------------------
         Table Methods
        ---------------------------------------------------------------------*/

        self.filter = function (filters) {
            filters = filters || {}
            _.defaults(filters, {
                search: $(self.refs.search).val(),
                page: 1,
            })
            self.page = filters.page
            self.update_tasks(filters)
        }

        self.next_page = function () {
            if (!!self.pagination.next) {
                self.page += 1
                self.filter({page: self.page})
            } else {
                alert("No valid page to go to!")
            }
        }
        self.previous_page = function () {
            if (!!self.pagination.previous) {
                self.page -= 1
                self.filter({page: self.page})
            } else {
                alert("No valid page to go to!")
            }
        }


        self.update_tasks = function (filters) {
            filters = filters || {}
            let show_public_tasks = $(self.refs.public).prop('checked')
            if (show_public_tasks) {
                filters.public = true
            }
            CODALAB.api.get_tasks(filters)
                .done(function (data) {
                    self.tasks = data.results
                    self.pagination = {
                        "count": data.count,
                        "next": data.next,
                        "previous": data.previous
                    }
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load tasks")
                })
        }

        self.search_tasks = function () {
            var filter = self.refs.search.value

            delay(() => self.update_tasks({search: filter}), 100)
        }

        self.delete_task = function (task) {
            if (confirm("Are you sure you want to delete '" + task.name + "'?")) {
                CODALAB.api.delete_task(task.id)
                    .done(function () {
                        self.update_tasks()
                        toastr.success("Task deleted successfully!")
                    })
                    .fail(function (response) {
                        toastr.error(response.responseJSON['error'])
                    })
            }
            event.stopPropagation()
        }

        self.delete_tasks = function () {
            if (confirm(`Are you sure you want to delete multiple tasks?`)) {
                CODALAB.api.delete_tasks(self.marked_tasks)
                    .done(function () {
                        self.update_tasks()
                        toastr.success("Tasks deleted successfully!")
                        self.marked_tasks = []
                    })
                    .fail(function (response) {
                        for (e in response.responseJSON) {
                            toastr.error(`${e}: '${response.responseJSON[e]}'`)
                        }
                    })
            }
            event.stopPropagation()
        }

        self.mark_task_for_deletion = function(task, e) {
            if (e.target.checked) {
                self.marked_tasks.push(task.id)
            }
            else {
                self.marked_tasks.splice(self.marked_tasks.indexOf(task.id), 1)
            }
        }
    </script>
    <style type="text/stylus">
        .task-row
            height 42px
            cursor pointer
        .benchmark-row
            overflow: hidden
            white-space: nowrap
            text-overflow: ellipsis
            max-width: 100px
    </style>
</task-management>
