<management>
    <div class="ui tabular menu">
        <div class="active item" data-tab="datasets">Dataset Management</div>
        <div class="item" data-tab="tasks">Task Management</div>
    </div>
    <div class="ui active tab" data-tab="datasets">
        <data-management></data-management>
    </div>
    <div class="ui tab" data-tab="tasks">
        <task-management></task-management>
    </div>

    <script>
        let self = this

        self.on('mount', () => {
            $('.ui.menu .item', self.root).tab()
        })
    </script>

</management>