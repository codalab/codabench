<competition-management>
    <div class="ui center aligned grid">
        <div class="fourteen wide column">
            <h1 style="float: left; display: inline-block;">Benchmark Management</h1>
            <a if="{ CODALAB.state.user.can_create_competition }" class="ui right floated green button" href="{ URLS.COMPETITION_UPLOAD }">
                <i class="upload icon"></i> Upload
            </a>
            <a if="{ CODALAB.state.user.can_create_competition }" class="ui right floated green button" href="{ URLS.COMPETITION_ADD }">
                <i class="add square icon"></i> Create
            </a>
        </div>
    </div>
    <competition-list></competition-list>

    <script>
        var self = this

    </script>

    <style>

    </style>
</competition-management>
