<task-detail>
    <div class="ui container">
        <h1>{task.name}</h1>
        <div class="ui segment">
            <div class="ui list">
                <div class="item"><div class="header"><em>{task.description}</em></div></div>

                <div class="item">
                    <div class="header">Created By</div>
                    {task.created_by}
                </div>

                <div class="item">
                    <div class="header">Key</div>
                    {task.key}
                </div>
            </div>
        </div>
        <div class="ui secondary pointing green two item tabular menu">
            <div class="active item" data-tab="files">Files</div>
            <div class="item" data-tab="solutions">Solutions</div>
        </div>
        <div class="ui active tab" data-tab="files">
            <table class="ui table">
                <thead>
                <tr>
                    <th>Files</th>
                </tr>
                </thead>
                <tbody>
                <tr each="{file in task.files}">
                    <td><a href="{file.file_path}">{file.name}</a></td>
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
                <tr each="{solution in task.solutions}">
                    <td><a href="{solution.file_path}">{solution.data}</a></td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        var self = this

        self.task = {}

        self.on('mount', function () {
            $('.tabular.menu .item', self.root).tab()
            CODALAB.api.get_task(self.opts.task_pk)
                .done((data) => {
                    self.task = data
                    console.log(data)
                    self.update()
                })
        })
    </script>
</task-detail>