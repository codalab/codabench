<quota-management>
   
    <div class="ui segment p-4">
        <!--  Title  -->
        <h2>Quota and Cleanup</h2>

        <!--  Table  -->
        <table class="ui celled compact table">
            <tbody>
                <!--  Quota  -->
                <!--  <tr>
                    <td width="40%">Quota (25% used) </td>
                    <td>
                        <div class="w-full bg-neutral-200">
                            <div class="h-5 w-full bg-neutral-200">
                                <div class="h-5 bg-red-500" style="width: 25%"></div>
                            </div>
                    </td>
                </tr>  -->
                <!--  Orphan Tasks  -->
                <tr>
                    <td>Unused Tasks <span show="{unused_tasks > 0}">(<b>{unused_tasks}</b>)</span></td>
                    <td>
                    <button class="ui red right floated labeled icon button {disabled: unused_tasks === 0}" onclick="{delete_unused_tasks}">
                        <i class="icon trash"></i>
                        Delete unused tasks
                    </button>
                    </td>
                </tr>
                <!--  Orphan Datasets  -->
                <tr>
                    <td>Unused Datasets and Programs <span show="{unused_datasets_programs > 0}">(<b>{unused_datasets_programs}</b>)</span></td>
                    <td>
                    <button class="ui red right floated labeled icon button {disabled: unused_datasets_programs === 0}" onclick="{delete_unused_datasets}">
                        <i class="icon trash"></i>
                        Delete unused datasets/programs
                    </button>
                    </td>
                </tr>
                <!--  Orphan Submissions  -->
                <tr>
                    <td>Unused Submissions <span show="{unused_submissions > 0}">(<b>{unused_submissions}</b>)</span></td>
                    <td>
                        <button class="ui red right floated labeled icon button {disabled: unused_submissions === 0}" onclick="{delete_unused_submissions}">
                        <i class="icon trash"></i>
                        Delete unused submissions
                    </button>
                    </td>
                </tr>
                <!--  Failed Submissions  -->
                <tr>
                    <td>Failed Submissions <span show="{failed_submissions > 0}">(<b>{failed_submissions}</b>)</span></td>
                    <td>
                        <button class="ui red right floated labeled icon button {disabled: failed_submissions === 0}" onclick="{delete_failed_submissions}">
                        <i class="icon trash"></i>
                        Delete failed submissions
                    </button>
                    </td>
                </tr>
            </tbody>
            
        </table>
    </div>

    <script>
        // Initialize variables
        let self = this
        self.unused_tasks = 0
        self.unused_datasets_programs = 0
        self.unused_submissions = 0
        self.failed_submissions = 0

        // get cleanup details on mount
        self.on('mount', () => {
            self.update()
            self.get_cleanup()
        })

        
        self.get_cleanup = function () {
            CODALAB.api.get_user_quota_cleanup()
                .done(function (data) {
                    self.unused_tasks = data.unused_tasks
                    self.unused_datasets_programs = data.unused_datasets_programs
                    self.unused_submissions = data.unused_submissions
                    self.failed_submissions = data.failed_submissions
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load cleanup data")
                })
        }

        /*
        Delete Functions
        */

        // Delete unused tasks
        self.delete_unused_tasks = function(){
            console.log("Delete Tasks")
        }

        // Delete unused tasks
        self.delete_unused_datasets = function(){
            console.log("Delete Datasets")
        }
        // Delete unused tasks
        self.delete_unused_submissions = function(){
            console.log("Delete Submissions")
        }
        // Delete unused tasks
        self.delete_failed_submissions = function(){
            console.log("Delete Failed Submissions")
        }
    </script>

</quota-management>
