<task-management>
    <div class="ui tabular menu">
        <div class="active item" data-tab="my_tasks">My Tasks</div>
        <div class="item" data-tab="public_tasks">Public Tasks</div>
    </div>
    <div class="ui active tab" data-tab="my_tasks">
        <h1>My Tasks</h1>
        <div class="ui divider"></div>
        <div class="ui icon input">
            <input type="text" placeholder="Search by name..." ref="search_mine" onkeyup="{ search_my_tasks }">
            <i class="search icon"></i>
        </div>
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
        <h1>Public Tasks</h1>
        <div class="ui divider"></div>
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

    <script>

        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/

        self.my_tasks = []
        self.public_tasks = []

        self.one("mount", function () {
            self.update_tasks()
            $('.tabular.menu .item', self.root).tab()
        })

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
