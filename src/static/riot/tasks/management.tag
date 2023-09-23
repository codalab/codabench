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

    <table id="tasksTable" class="ui {selectable: tasks.length > 0} celled compact sortable table">
        <thead>
        <tr>
            <th>Name</th>
            <th class="benchmark-row">Benchmarks</th>
            <th width="125px">Shared With</th>
            <th width="125px">Uploaded...</th>
            <th width="50px" class="no-sort">Public</th>
            <th width="100px" class="no-sort">Actions</th>
            <th width="25px" class="no-sort"></th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ task in tasks }" class="task-row">
            <td onclick="{show_detail_modal.bind(this, task)}">{ task.name }</td>
            <td class="benchmark-row">
                <div show="{task.competitions.length > 0}" class="ui list">
                    <div class="item" each="{comp in task.competitions}">
                        <a href="{URLS.COMPETITION_DETAIL(comp.id)}" target="_blank">{comp.title}</a>
                    </div>
                </div>
            
            
            </td>
            <td>{ task.shared_with.join(', ') }</td>
            <td>{ timeSince(Date.parse(task.created_when)) } ago</td>
            <td class="center aligned">
                <i class="checkmark box icon green" show="{ task.is_public }"></i>
            </td>
            <td>
                <div if="{ task.created_by == CODALAB.state.user.id }">
                    <button class="mini ui button blue icon" onclick="{show_edit_modal.bind(this, task)}">
                        <i class="icon pencil"></i>
                    </button>
                    <button class="mini ui button red icon" onclick="{ delete_task.bind(this, task) }">
                        <i class="icon trash"></i>
                    </button>
                </div>
            </td>
            <td class="center aligned">
                <div class="ui fitted checkbox" if="{ task.created_by == CODALAB.state.user.id }">
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
        -------------------------------------->
        <tr if="{tasks.length > 0}">
            <th colspan="7">
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
    <!--  Task Detail Modal  -->
    <div class="ui modal" ref="detail_modal">
        <div class="header">
            {selected_task.name}
            <button class="ui right floated primary button" onclick="{ open_share_modal.bind(this) }">
                Share Task
                <i class="share square icon right"></i>
            </button>
        </div>
        <div class="content">
            <h4>{selected_task.description}</h4>
            <div class="ui divider" show="{selected_task.description}"></div>
            <div><strong>Created By:</strong> <a href="/profiles/user/{selected_task.created_by}/" target=_blank>{selected_task.created_by}</a></div>
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

    <!-- Create Task Modal  -->
    <div class="ui modal" ref="modal">
        <div class="header">
            Create Task
        </div>
        <div class="content">
            <div class="ui pointing menu">
                <div class="active item modal-item" data-tab="details">Details</div>
                <div class="item modal-item" data-tab="data">Datasets and programs</div>
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


        <div class="ui modal" ref="share_modal">
            <div class="ui header">Share</div>
            <div class="content">
                <select class="ui fluid search multiple selection dropdown" multiple id="share_search">
                    <i class="dropdown icon"></i>
                    <div class="default text">Select a User to Share with</div>
                    <div class="menu">
                    </div>
                </select>
            </div>
            <div class="actions">
                <div class="ui positive button">Share</div>
                <div class="ui cancel button">Cancel</div>
            </div>
        </div>
        <div class="actions">
            <div selenium="save-task" class="ui primary button {disabled: !modal_is_valid}" onclick="{ create_task }">Create</div>
            <div class="ui basic red cancel button">Cancel</div>
        </div>
    </div>

    <!-- Edit Task Modal  -->
    <div class="ui modal" ref="edit_modal">
        <!--  Modal title  -->
        <div class="header">
            Update Task
        </div>
        <div class="content">
            <!--  Modal Tabs  -->
            <div class="ui pointing menu">
                <div class="active item modal-item" data-tab="edit_details">Details</div>
                <div class="item modal-item" data-tab="edit_data">Datasets and programs</div>
            </div>
            <!--  Modal Form  -->
            <form class="ui form" ref="edit_form">
                <!--  Task Detail Tab  -->
                <div class="ui active tab" data-tab="edit_details">
                    <!--  Task Name  -->
                    <div class="required field">
                        <label>Name</label>
                        <input name="edit_name" placeholder="Name" ref="edit_name" value="{selected_task.name}" onkeyup="{ edit_form_updated }">
                    </div>
                    <!--  Task Description  -->
                    <div class="required field">
                        <label>Description</label>
                        <textarea rows="4" name="edit_description" placeholder="Description" ref="edit_description"
                                  value="{selected_task.description}" onkeyup="{ edit_form_updated }"></textarea>
                    </div>
                </div>
                <!--  Task Datasets Tab  -->
                <div class="ui tab" data-tab="edit_data">
                    <div>
                        <div class="two fields" data-no-js>
                            <!--  Scoring Program  -->
                            <div class="field required">
                                <label>Scoring Program</label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="scoring_program">
                                    <i class="search icon"></i>
                                    <input type="text" class="prompt" id="editscoring_program" value="{selected_task.scoring_program?.name  || ''}">
                                    <div class="results"></div>
                                </div>
                            </div>
                            <!--  Ingestion Program  -->
                            <div class="field">
                                <label>Ingestion Program</label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="ingestion_program">
                                    <i class="search icon"></i>
                                    <input  type="text" class="prompt" id="edit_ingestion_program" value="{selected_task.ingestion_program?.name  || ''}">
                                    <div class="results"></div>
                                </div>
                            </div>
                        </div>
                        <div class="two fields" data-no-js>
                            <!-- Reference Data   -->
                            <div class="field">
                                <label>Reference Data</label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="reference_data">
                                    <i class="search icon"></i>
                                    <input  type="text" class="prompt" id="edit_reference_data" value="{selected_task.reference_data?.name || ''}">
                                    <div class="results"></div>
                                </div>
                            </div>
                            <!--  Input Data  -->
                            <div class="field">
                                <label>Input Data</label>
                                <div class="ui fluid left icon labeled input search dataset" data-name="input_data">
                                    <i class="search icon"></i>
                                    <input  type="text" class="prompt" id="edit_input_data" value="{selected_task.input_data?.name  || ''}">
                                    <div class="results"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </div>
        <!--  Warning message  -->
        <div class="content">
            <div class="ui yellow message">
                Note: It is the organizer's responsibility to rerun submissions on the updated task if needed.
            </div>
        </div>
        <div class="actions">
            <div class="ui primary button {disabled: !edit_modal_is_valid}" onclick="{ update_task }">Update</div>
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
            $('#tasksTable').tablesort()
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

            $('#share_search').dropdown({
                apiSettings: {
                    url: `${URLS.API}user_lookup/?q={query}`,
                },
                clearable: true,
                preserveHTML: false,
                fields: {
                    title: 'name',
                    value: 'id',
                },
                cache: false,
                maxResults: 5,
            })

            $(self.refs.share_modal).modal({
                onApprove: function () {
                    let users = $('#share_search').dropdown('get value')
                    CODALAB.api.share_task(self.selected_task.id, {shared_with: users})
                        .done((data) => {
                            toastr.success('Task Shared')
                            $('#share_search').dropdown('clear')
                            CODALAB.api.get_task(self.selected_task.id)
                                .done((data) => {
                                    _.forEach(self.tasks, (task) => {
                                        if (task.id === self.selected_task.id) {
                                            task.shared_with = data.shared_with
                                            self.update()
                                            return false
                                        }
                                    })
                                })
                        })
                        .fail((response) => {
                            toastr.error('An error has occurred')
                            $('#share_search').dropdown('clear')
                            return true
                        })
                }

            })
        })

        /*---------------------------------------------------------------------
         Modal Methods
        ---------------------------------------------------------------------*/
        self.show_modal = () => {
            $('.menu .item', self.root).tab('change tab', 'details')
            self.form_datasets = {}
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
                    CODALAB.events.trigger('reload_quota_cleanup')
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
         Update Task Methods
        ---------------------------------------------------------------------*/

        self.show_edit_modal = (task, e) => {
            // Get Task from API
            CODALAB.api.get_task(task.id)
                .done((data) => {
                    self.selected_task = data
                    self.update()

                    // empty form datasets
                    // and insert avaiable datasets (keys) from the task
                    self.form_datasets = {}
                    if(self.selected_task.ingestion_program !== null){
                        self.form_datasets['ingestion_program'] = self.selected_task.ingestion_program.key
                    }
                    if(self.selected_task.scoring_program !== null){
                        self.form_datasets['scoring_program'] = self.selected_task.scoring_program.key
                    }
                    if(self.selected_task.reference_data !== null){
                        self.form_datasets['reference_data'] = self.selected_task.reference_data.key
                    }
                    if(self.selected_task.input_data !== null){
                        self.form_datasets['input_data'] = self.selected_task.input_data.key
                    }

                    // call edit form updated to enable/disable task update button
                    self.edit_form_updated()

                    // show edit task modal
                    $(self.refs.edit_modal).modal('show')

                })
        }

        self.close_edit_modal = () => {
            $(self.refs.edit_modal).modal('hide')
            self.clear_edit_form()
        }

        self.edit_form_updated = () => {
            self.edit_modal_is_valid = $(self.refs.edit_name).val() && $(self.refs.edit_description).val() && self.form_datasets.scoring_program
            self.update()
        }

        self.clear_edit_form = () => {
            $(':input', self.refs.edit_form)
                .not('[type="file"]')
                .not('button')
                .not('[readonly]').each(function (i, field) {
                $(field).val('')
            })
            self.form_datasets = {}
            self.edit_modal_is_valid = false
        }
        self.update_task = () => {
            let data = get_form_data($(self.refs.edit_form))
            
            // replace property names in the data object
            data.name = data.edit_name;
            data.description = data.edit_description;

            // delete the old property names
            delete data.edit_name
            delete data.edit_description
            
            _.assign(data, self.form_datasets)
            task_id = self.selected_task.id
            CODALAB.api.update_task(task_id, data)
                .done((response) => {
                    toastr.success('Task Updated')
                    self.close_edit_modal()
                    self.update_tasks()
                    CODALAB.events.trigger('reload_quota_cleanup')
                })
                .fail((response) => {
                    toastr.error('Error Updating Task')
                })
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
                        CODALAB.events.trigger('reload_quota_cleanup')
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
                        CODALAB.events.trigger('reload_quota_cleanup')
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

        self.open_share_modal = () => {
            $(self.refs.share_modal)
                .modal('show')
        }

        // Update tasks on unused tasks delete
        CODALAB.events.on('reload_tasks', self.update_tasks)

    </script>
    <style type="text/stylus">
        .task-row
            height 42px
            cursor pointer
        .benchmark-row
            overflow: hidden
            white-space: nowrap
            text-overflow: ellipsis
            max-width: 125px
    </style>
</task-management>
