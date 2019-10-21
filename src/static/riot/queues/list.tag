<queues-list>
    <div class="ui icon input">
        <input type="text" placeholder="Search by name..." ref="search" onkeyup="{filter.bind(this, undefined)}">
        <i class="search icon"></i>
    </div>
    <div class="ui checkbox" onclick="{ filter.bind(this, undefined) }">
        <label>Show Public Queues</label>
        <input type="checkbox" ref="public">
    </div>
    <div class="ui green right floated labeled icon button" onclick="{ switch_to_form }"><i class="add circle icon"></i>
        Create Queue
    </div>
    <table class="ui {selectable: queues.length > 0} celled compact table">
        <thead>
        <tr>
            <th>Name</th>
            <th width="125px">Uploaded...</th>
            <th width="125px">Organizers Count</th>
            <th width="50px">Public</th>
            <th width="50px">Copy Broker URL</th>
            <th width="50px">Edit?</th>
            <th width="50px">Delete?</th>
        </tr>
        </thead>
        <tbody>
        <!--<tr each="{ queue in queues }" onclick="{show_detail_modal.bind(this, queue)}" class="queue-row">-->
        <tr each="{ queue in queues }" class="queue-row">
            <td>{ queue.name }</td>
            <td>{ timeSince(Date.parse(queue.created_when)) } ago</td>
            <td>{ queue.organizers.length }</td>
            <td class="center aligned">
                <i class="checkmark box icon green" if="{ queue.is_public }"></i>
            </td>
            <td class="center aligned">
                <button class="mini ui button green icon" if="{ !!queue.broker_url }" onclick="{ copy_queue_url.bind(this, queue) }">
                    <i class="icon edit"></i>
                </button>
            </td>
            <td class="center aligned">
                <button class="mini ui button blue icon" if="{ queue.is_owner }" onclick="{ edit_queue.bind(this, queue) }">
                    <i class="icon edit"></i>
                </button>
            </td>
            <td class="center aligned">
                <button class="mini ui button red icon" if="{ queue.is_owner }" onclick="{ delete_queue.bind(this, queue) }">
                    <i class="icon delete"></i>
                </button>
            </td>
        </tr>

        <tr if="{queues.length === 0}">
            <td class="center aligned" colspan="4">
                <em>No Queues Yet!</em>
            </td>
        </tr>
        </tbody>
        <tfoot>
        <!-------------------------------------
                  Pagination
        ------------------------------------->
        <tr if="{queues.length > 0}">
            <th colspan="7">
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

    <script>
        var self = this
        self.queues = []
        self.selected_queue = {}
        self.page = 1

        self.one("mount", function () {
            self.update_queues()
            $(".ui.checkbox", self.root).checkbox()
        })

        self.switch_to_form = () => {
            window.location = '/queues/form/'
        }

        self.update_queues = function (filters) {
            filters = filters || {}
            let show_public_queues = $(self.refs.public).prop('checked')
            if (show_public_queues) {
                filters.public = true
            }
            CODALAB.api.get_queues(filters)
                .done(function (data) {
                    self.queues = data.results
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

        self.delete_queue = function (queue) {
            if (confirm("Are you sure you want to delete '" + queue.name + "'?")) {
                CODALAB.api.delete_task(queue.id)
                    .done(function () {
                        self.update_queues()
                        toastr.success("Queue deleted successfully!")
                    })
                    .fail(function () {
                        toastr.error("Could not delete queue!")
                    })
            }
            event.stopPropagation()
        }

        self.copy_queue_url = function (queue) {
            navigator.clipboard.writeText(queue.broker_url).then(function () {
                /* clipboard successfully set */
                toastr.success("Successfully copied broker url to clipboard!")
            }, function () {
                /* clipboard write failed */
                toastr.error("Failed to copy broker url to clipboard!")
            });
        }

        self.edit_queue = function (queue) {
            window.location = '/queues/form/' + queue.id
            event.stopPropagation()
        }
    </script>
    <style>

    </style>
</queues-list>