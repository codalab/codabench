<competition-management>
    <h1>Competition Management</h1>

    <h3>Todo:</h3>
    <ol>
        <li><s>Actually filter this list by who owns it</s></li>
        <li>Create</li>
        <li>Edit</li>
        <li>Delete</li>
    </ol>

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