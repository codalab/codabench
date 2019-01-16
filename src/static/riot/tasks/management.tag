<task-management>
    <h1>Task Management</h1>

    <div class="ui divider"></div>

    <div>
        <div class="ui icon input">
            <input type="text" placeholder="Filter by name..." ref="search" onkeyup="{ search_tasks }">
            <i class="search icon"></i>
        </div>
        <table class="ui celled compact table">
            <thead>
            <tr>
                <th>Name</th>
                <!--<th width="175px">Type</th>-->
                <th width="125px">Uploaded...</th>
                <th width="50px">Public</th>
                <th width="50px">Delete?</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{ task in tasks }">
                <td><a href="#">{ task.name }</a></td>
                <!-- TODO make this link download task? or pull up modal for edit? -->
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

    <script>

        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/

        self.tasks = []

        self.one("mount", function () {

            self.update_tasks()

        })

        self.update_tasks = function () {
            CODALAB.api.get_tasks()
                .done(function (data) {
                    self.tasks = data
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load tasks")
                })
        }


        self.search_tasks = function () {
            var filter = self.refs.search.value

            if (filter !== "" && filter.length < 3) {

            } else {
                delay(function () {
                    var filters = {
                        search: filter
                    }
                    console.log(filters)
                    CODALAB.api.get_tasks(filters)
                        .done(function (data) {
                            self.tasks = data
                            self.update()
                        })
                }, 100)
            }
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
</task-management>