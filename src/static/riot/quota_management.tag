<quota-management>
   
    <div class="ui segment p-4">
        <div class="ui" style="display: flex; flex-direction: row; align-items: center;">
            <!--  Title  -->
            <h2 style="margin-bottom: 0;">Quota and Cleanup</h2>

            <!--  Quota  -->
            <div style="flex: 0 0 auto; margin-left: auto;">
                Quota: {pretty_bytes(storage_used)} / {quota} GB
            </div>
        </div>

        <!--  Table  -->
        <table class="ui celled compact table">
            <tbody>
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
        self.quota = 0
        self.storage_used = 0

        // get cleanup details on mount
        self.on('mount', () => {
            self.update()
            self.get_cleanup()
            self.get_quota()
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

        self.get_quota = function () {
            CODALAB.api.get_user_quota()
                .done(function (data) {
                    self.quota = data.quota
                    self.storage_used = data.storage_used
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load quota")
                })
        }

        /*
        Delete Functions
        */

        // Delete unused tasks
        self.delete_unused_tasks = function(){
            if (confirm(`Are you sure you want to permanently delete all unused tasks?`)) {

                CODALAB.api.delete_unused_tasks()
                    .done(function (data) {
                        if(data.success){
                            self.unused_tasks = 0
                            toastr.success(data.message)
                            self.update()
                            CODALAB.events.trigger('reload_tasks')
                            CODALAB.events.trigger('reload_datasets')
                            self.get_cleanup()
                        }else{
                            toastr.error(data.message)
                        }
                    })
                    .fail(function (response) {
                        toastr.error("Unsed tasks deletion failed!")
                    })
            }
        }

        // Delete unused datasets
        self.delete_unused_datasets = function(){
            if (confirm(`Are you sure you want to permanently delete all unused datasets and programs?`)) {

                CODALAB.api.delete_unused_datasets()
                    .done(function (data) {
                        if(data.success){
                            self.unused_datasets_programs = 0
                            toastr.success(data.message)
                            self.update()
                            CODALAB.events.trigger('reload_datasets')
                        }else{
                            toastr.error(data.message)
                        }
                    })
                    .fail(function (response) {
                        toastr.error("Unused datasets and programs deletion failed!")
                    })
            }
        }

        // Delete unused submissions
        self.delete_unused_submissions = function(){
            if (confirm(`Are you sure you want to permanently delete all unused submissions?`)) {

                CODALAB.api.delete_unused_submissions()
                    .done(function (data) {
                        if(data.success){
                            self.unused_submissions = 0
                            toastr.success(data.message)
                            self.update()
                            CODALAB.events.trigger('reload_submissions')
                        }else{
                            toastr.error(data.message)
                        }
                    })
                    .fail(function (response) {
                        toastr.error("Unused submissions deletion failed!")
                    })
            }
        }

        // Delete failed submissions
        self.delete_failed_submissions = function(){
            if (confirm(`Are you sure you want to permanently delete all failed submissions?`)) {

                CODALAB.api.delete_failed_submissions()
                    .done(function (data) {
                        if(data.success){
                            self.failed_submissions = 0
                            toastr.success(data.message)
                            self.update()
                            CODALAB.events.trigger('reload_submissions')
                        }else{
                            toastr.error(data.message)
                        }
                    })
                    .fail(function (response) {
                        toastr.error("Failed submissions deletion failed!")
                    })
            }
        }

        CODALAB.events.on('reload_quota_cleanup', self.get_cleanup)

    </script>

</quota-management>
