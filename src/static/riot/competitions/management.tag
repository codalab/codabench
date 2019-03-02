<competition-management>
    <div class="ui center aligned grid">
        <div class="fourteen wide column">
            <h1 style="float: left; display: inline-block;">Competition Management</h1>
            <a class="ui right floated green button" href="{ URLS.COMPETITION_UPLOAD }">
                <i class="upload icon"></i> Upload
            </a>
            <a class="ui right floated green button" href="{ URLS.COMPETITION_ADD }">
                <i class="add square icon"></i> Create
            </a>
        </div>
    </div>
    <!-- <competition-list competitions="{ competitions }"></competition-list> -->
    <competition-list></competition-list>

    <script>
        var self = this

        /*self.one("mount", function() {
            CODALAB.api.get_competitions("?mine=true")
                .done(function(data){
                    self.update({competitions: data})
                })
                .fail(function(response){
                    toastr.error("Could not load competition list....")
                })
        })*/
    </script>

    <style>

    </style>
</competition-management>