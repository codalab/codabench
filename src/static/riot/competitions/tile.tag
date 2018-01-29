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

        self.one("mount", function () {
            if (!self.opts.competitions) {
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
            <a class="ui right floated button" href="{ URLS.COMPETITION_DETAIL(competition.id) }">
                View
                <i class="right chevron icon"></i>
            </a>

            <div class="ui right floated buttons">
                <div class="ui negative button">
                    <i class="delete icon"></i>
                    Delete
                </div>
                <div class="ui button">
                    <i class="pencil icon"></i>
                    Edit
                </div>
            </div>

            <div class="ui label">Active</div>
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
