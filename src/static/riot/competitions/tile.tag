<competition-list>
    <div class="ui vertical stripe segment">
        <div class="ui middle aligned stackable grid container centered">
            <div class="row">
                <div class="twelve wide column">
                    <div class="ui divided items" if="{opts.competitions}">
                        <competition-tile each="{competition in opts.competitions}"></competition-tile>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this

        self.one("mount", function() {
            if(!self.opts.competitions) {
                console.log("Hatsa matsa")
                // If no competitions specified, get ALL competitions
                CODALAB.api.get_competitions()
                    .done(function (data) {
                        self.opts.competitions = data
                        self.update()
                    })
                    .fail(function (response) {
                        toastr.error("Could not load competition list....")
                    })
            }
            console.log("Hatsa matsa2")
        })
    </script>
</competition-list>

<competition-tile class="ui item">
        <div class="image">
            <img src="https://semantic-ui.com/images/wireframe/image.png">
        </div>
        <div class="content">
            <a class="header">{ competition.title }</a>
            <div class="meta">
                <span>created by { competition.created_by }</span>
            </div>
            <div class="description">
                <p>{ competition.description }</p>
            </div>
            <div class="extra">
                <div class="ui right floated primary button">
                    View more
                    <i class="right chevron icon"></i>
                </div>
                <div class="ui label">Active</div>
            </div>
        </div>
    </div>
    <script>
        var self = this
    </script>

    <style>
        :scope {
            display: block;
        }
    </style>
</competition-tile>
