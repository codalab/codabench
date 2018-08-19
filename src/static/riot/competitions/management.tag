<competition-management>
    <h1>Competition Management</h1>

    <h3>Todo:</h3>
    <ol>
        <li><s>Actually filter this list by who owns it</s></li>
        <li>Create</li>
        <li>Edit</li>
        <li>Delete</li>
    </ol>

    <div class="ui right aligned grid">
        <div class="sixteen wide column">
            <a class="ui green button" href="{ URLS.COMPETITION_UPLOAD }">
                <i class="upload icon"></i> Upload
            </a>
            <a class="ui green button" href="{ URLS.COMPETITION_ADD }">
                <i class="add square icon"></i> Create
            </a>
        </div>
    </div>

    <competition-list competitions="{ competitions }"></competition-list>

    <script>
        var self = this

        self.one("mount", function() {
            CODALAB.api.get_competitions("?mine=true")
                .done(function(data){
                    self.update({competitions: data})
                })
                .fail(function(response){
                    toastr.error("Could not load competition list....")
                })
        })
    </script>

    <style>

    </style>
</competition-management>