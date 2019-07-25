<management>
    <div class="ui tabular menu">
        <div class="active item" data-tab="datasets">Datasets</div>
        <div class="item" data-tab="tasks">Tasks</div>
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