<competition-management>
    <h1>Yo here are your stupid competitions you nerd</h1>

    <competition-list competitions="{ competitions }"></competition-list>
    <!--<competition-tile each="{competition in competitions}"></competition-tile>-->

    <script>
        var self = this

        self.one("mount", function() {
            CODALAB.api.my_competitions()
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