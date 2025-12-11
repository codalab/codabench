<management>
    <!--Todo: ultimately decide whether this belongs on tasks:management or dataset:management
            Is currently at both locations-->
    <div class="ui top attached tabular menu">
        <div class="active item" data-tab="submissions">Submissions</div>
        <div class="item" data-tab="datasets">Datasets and programs</div>
        <div class="item" data-tab="tasks">Tasks</div>
        <div class="item" data-tab="bundles">Competition Bundles</div>
        <div class="right menu">
            <div class="item">
                <help_button href="https://docs.codabench.org/latest/Organizers/Running_a_benchmark/Resource-Management/"
                             tooltip_position="left center">
                </help_button>
            </div>
        </div>
    </div>
    <div class="ui active bottom attached tab segment" data-tab="submissions">
        <submission-management></submission-management>
    </div>
    <div class="ui bottom attached tab segment" data-tab="datasets">
        <data-management></data-management>
    </div>
    <div class="ui bottom attached tab segment" data-tab="tasks">
        <task-management></task-management>
    </div>
    <div class="ui bottom attached tab segment" data-tab="bundles">
        <bundle-management></bundle-management>
    </div>

    <script>
        let self = this

        self.on('mount', () => {
            $('.ui.menu .item', self.root).tab()
        })
    </script>

</management>
