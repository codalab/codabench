<task-detail>
    <div class="ui segment">
        <h1>{task.name}</h1>
        <div class="ui container">
            <div style="font-size: 18px;">{task.description}</div>
            <div class="ui divider"></div>
            <div><strong>Created By:</strong> {task.created_by}</div>
            <div if="{task.created_by === CODALAB.state.user.username}">
                <!-- TODO: add is_superuser to this later -->
                <button class="ui blue right floated button" onclick="{edit_task}">
                    <i class="edit icon"></i>Edit
                </button>
            </div>
            <div><strong>Key:</strong> {task.key}</div>
            <div><strong>Is Public:</strong>
                <span show="{task.is_public}">Yes</span>
                <span show="{!task.is_public}">No</span>
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
    <div class="ui modal" ref="modal">
        <div class="header">
            Edit
        </div>
        <div class="content">
            <form class="ui form" ref="form">
                <div class="required field">
                    <label>Name</label>
                    <input type="text" value="{task.name}" name="name">
                </div>
                <div class="required field">
                    <label>Description</label>
                    <input type="text" value="{task.description}" name="description">
                </div>
                <div class="field">
                    <div class="ui checkbox">
                        <input type="checkbox" name="is_public" checked="{task.is_public}">
                        <label>Public</label>
                    </div>
                </div>
                <button type="submit" class="ui blue button" onclick="{submit_edit}">Save</button>
            </form>
        </div>
    </div>


    <script>
        var self = this

        self.task = {}

        self.on('mount', function () {
            $('.tabular.menu .item', self.root).tab()
            self.update_task()
        })

        self.update_task = function () {
            CODALAB.api.get_task(self.opts.task_pk)
                .done((data) => {
                    self.task = data
                    self.update()
                })
        }

        self.edit_task = function (event) {
            event.preventDefault()
            $(self.refs.modal).modal('show')
        }

        self.submit_edit = function (event) {
            event.preventDefault()
            let data = get_form_data(self.refs.form)
            data.is_public = $('[name="is_public"]', self.refs.form).is(':checked')
            // ^ used to actually get correct checkbox data
            CODALAB.api.update_task(self.task.id, data)
                .done(() => {
                    toastr.success('Changes Saved')
                    $(self.refs.modal).modal('hide')
                    self.update_task()
                })
                .fail((response) => {
                    toastr.error('Error saving changes')
                })
        }
    </script>
</task-detail>
