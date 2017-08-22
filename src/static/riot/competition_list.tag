<competition-list>
    <h1>List of comps yo</h1>

    <ul>
        <li each={ competitions }>
            { title }
        </li>
    </ul>

    <script>
        var self = this

        self.on('mount', function() {
            $.get('http://localhost:8000/api/competitions/')
                .done(function(competitions){
                    self.update({competitions: competitions})
                })
        })
    </script>
</competition-list>