<queues-list>
    <div class="ui horizontal list">
        <div class="item">
            <div class="ui icon input">
                <input type="text"
                       placeholder="Search by name..."
                       ref="search"
                       onkeyup="{filter.bind(this, undefined)}">
                <i class="search icon"></i>
            </div>
        </div>
        <div class="item">
            <div class="ui checkbox" onclick="{ filter.bind(this, undefined) }">
                <label>Show Public Queues</label>
                <input type="checkbox" ref="public">
            </div>
        </div>
        <div class="item">
            <help_button href="https://docs.codabench.org/latest/Organizers/Running_a_benchmark/Queue-Management/"
                         tooltip_position="right center">
            </help_button>
        </div>
    </div>

    <div class="ui green right floated labeled icon button" onclick="{ show_modal.bind(this, undefined) }">
        <i class="add circle icon"></i> Create Queue
    </div>

    <table class="ui {selectable: queues.length > 0} celled compact table">
        <thead>
        <tr>
            <th>Name</th>
            <th width="150px">Owner</th>
            <th width="125px">Created</th>
            <th width="50px">Public</th>
            <th class="right aligned" width="150px">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ queue in queues }" class="queue-row">
            <td>{ queue.name }</td>
            <td>{ queue.owner }</td>
            <td>{ timeSince(Date.parse(queue.created_when)) } ago</td>
            <td class="center aligned">
                <i class="checkmark box icon green" if="{ queue.is_public }"></i>
            </td>
            <td class="right aligned">
                <span data-tooltip="View Queue Details">
                    <i class="grey icon eye popup-button" if="{ !!queue.broker_url }" onclick="{ show_broker_modal.bind(this, queue) }"></i>
                </span>
                <span data-tooltip="Copy Broker URL">
                    <i class="icon copy outline popup-button" if="{ !!queue.broker_url }"
                       onclick="{ copy_queue_url.bind(this, queue) }"></i>
                </span>
                <span data-tooltip="Edit Queue">
                    <i class="blue icon edit popup-button" if="{ queue.is_owner && !!queue.broker_url }" onclick="{ show_modal.bind(this, queue) }"></i>
                </span>
                <span data-tooltip="Delete Queue">
                    <i class="red icon trash alternate outline popup-button" if="{ queue.is_owner && !!queue.broker_url }"
                       onclick="{ delete_queue.bind(this, queue) }"></i>
                </span>
            </td>
        </tr>

        <tr if="{queues.length === 0}">
            <td class="center aligned" colspan="5">
                <em>No Queues Yet!</em>
            </td>
        </tr>
        </tbody>
        <tfoot>

        <!-- Pagination -->
        <tr if="{queues.length > 0 && ( _.get(pagination, 'next') || _.get(pagination, 'previous') ) }">
            <th colspan="5">
                <div class="ui right floated pagination menu" if="{queues.length > 0}">
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

    <!--  Server status page button  -->
    <a href="/server_status" target="_blank">
        <div class="ui blue right floated button">Open Server status page</div>
    </a>

    <div class="ui modal" ref="modal">
        <div class="header">
            Queue Form
        </div>
        <div class="content">
            <form class="ui form" ref="form">
                <div class="required field">
                    <label>Name</label>
                    <input name="name" placeholder="Name" ref="queue_name">
                </div>
                <div class="field">
                    <div class="ui checkbox">
                        <label>Make Public?</label>
                        <input type="checkbox" ref="queue_public">
                    </div>
                </div>
                <div class="field">
                    <label>Collaborators</label>
                    <select name="collaborators" class="ui fluid search multiple selection dropdown" multiple ref="collab_search">
                        <i class="dropdown icon"></i>
                        <div class="default text">Select Collaborator</div>
                        <div class="menu">
                        </div>
                    </select>
                </div>
            </form>
        </div>
        <div class="actions">
            <div class="ui primary button" onclick="{ handle_queue }">Submit</div>
            <div class="ui basic red cancel button" onclick="{ close_modal }">Cancel</div>
        </div>
    </div>

    <div class="ui modal" ref="broker_modal">
        <div class="header">
            Queue Details
        </div>
        <div class="content">
            <h4>Broker URL:</h4>
            <span>{selected_queue.broker_url}</span>

            <h4>Vhost:</h4>
            <span>{selected_queue.vhost}</span>

            <!--  Competitions using this queue  -->
            <h4 if="{ _.get(selected_queue, 'competitions.length', 0) }">Competitions using this queue:</h4>
            <ul if="{ _.get(selected_queue, 'competitions.length', 0) }">
                <li each="{ comp in selected_queue.competitions }">

                <a class="link-no-deco" target="_blank" href="../competitions/{ comp.id }">{comp.title}</a>
                </li>
            </ul>

        </div>
        <div class="actions">
            <div class="ui cancel button" onclick="{ close_broker_modal }">Close</div>
        </div>
    </div>

    <script>
        var self = this
        self.queues = []
        self.selected_queue = {}
        self.page = 1

        self.one("mount", function () {
            self.update_queues()
            $(".ui.checkbox", self.root).checkbox()
            $(self.refs.collab_search).dropdown({
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
            $(self.refs.modal).modal({
                onHidden: () => {
                    self.clear_form()
                }
            })
            $(self.refs.broker_modal).modal({
                onHidden: () => {
                    self.selected_queue = {}
                    self.update()
                }
            })
        })

        self.update_queues = function (filters) {
            filters = filters || {}
            let show_public_queues = $(self.refs.public).prop('checked')
            if (show_public_queues) {
                filters.public = true
            }
            CODALAB.api.get_queues(filters)
                .done(function (data) {
                    self.queues = _.orderBy(data.results, queue => !queue.is_owner);
                    self.pagination = {
                        "count": data.count,
                        "next": data.next,
                        "previous": data.previous
                    }
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load queues")
                })
        }

        /*---------------------------------------------------------------------
        Modal Methods
        ----------------------------------------------------------------------*/
        self.show_modal = (queue) => {
            if (queue !== undefined && queue !== null) {
                self.set_selected_queue(queue)
            }
            $(self.refs.modal).modal('show')
        }

        self.close_modal = () => {
            $(self.refs.modal).modal('hide')
        }

        self.close_broker_modal = () => {
            $(self.refs.broker_modal).modal('hide')
        }

        self.clear_form = function() {
            $(self.refs.collab_search).dropdown('clear')
            self.refs.queue_name.value = null
            self.selected_queue = {}
            self.refs.queue_public.checked = false
        }

        self.show_broker_modal = (queue) => {
            self.selected_queue = queue
            self.update()
            $(self.refs.broker_modal).modal('show')
        }

        self.set_selected_queue = function (queue) {
            self.selected_queue = queue
            self.refs.queue_name.value = queue.name
            $(self.refs.collab_search)
                .dropdown('setup menu',
                {
                    values: _.map(queue.organizers, function(o) {
                        return {id: o.id, name: o.username}
                    })
                })
                .dropdown('set selected', _.map(queue.organizers, o => o.id.toString()))

            if (queue.is_public) {
                self.refs.queue_public.checked = true
            }
        }

        self.handle_queue = function () {
            let data = {
                name: self.refs.queue_name.value,
                is_public: self.refs.queue_public.checked,
                organizers: $(self.refs.collab_search).dropdown('get value')
            }
            let endpoint = !_.isEmpty(self.selected_queue)
                ? CODALAB.api.update_queue
                : CODALAB.api.create_queue
            endpoint(data, _.get(self.selected_queue, 'id'))
                .done(function (response) {
                    toastr.success("Success!")
                    self.close_modal()
                    // Todo: Handle this better
                    // Necessary to reset page to 1, because we re-grab our results regardless of page after update/create.
                    self.page = 1
                    self.update_queues()
                })
                .fail(function (response) {
                    toastr.error("An error occurred!")
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
            self.update_queues(filters)
        }

        self.next_page = function () {
            if (!!self.pagination.next) {
                self.page += 1
                self.filter({page: self.page})
            }
        }
        self.previous_page = function () {
            if (!!self.pagination.previous) {
                self.page -= 1
                self.filter({page: self.page})
            }
        }

        self.delete_queue = function (queue) {
            if (confirm(`Are you sure you want to delete the queue: "${queue.name}"?`)) {
                CODALAB.api.delete_queue(queue.id)
                    .done(function () {
                        self.update_queues()
                        toastr.success("Queue deleted successfully!")
                    })
                    .fail(function () {
                        toastr.error("Could not delete queue!")
                    })
            }
        }

        self.copy_queue_url = function (queue) {
            navigator.clipboard.writeText(queue.broker_url).then(function () {
                // clipboard successfully set
                toastr.success("Successfully copied broker url to clipboard!")
            }, function () {
                // clipboard write failed
                toastr.error("Failed to copy broker url to clipboard!")
            });
        }
    </script>
    <style type="text/stylus">
        .popup-button
            cursor pointer
    </style>
</queues-list>
