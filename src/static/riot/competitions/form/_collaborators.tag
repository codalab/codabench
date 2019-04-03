<competition-collaborators>
    <button class="ui primary button modal-button" ref="modal_button">
        <i class="add circle icon"></i> Add collaborator
    </button>

    <div show="{collabs.length > 0}">
        <div class="ui horizontal divider"></div>
        <table class="ui celled table">
            <thead>
            <tr>
                <th>Collaborator Name</th>
                <th style="width: 150px !important;">Actions</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{collab, index in collabs}">
                <td>{collab.name}</td>
                <td class="center aligned">
                    <button class="ui button red" onclick="{ remove_collaborator.bind(this, index, collab.name) }">Remove</button>
                </td>
            </tr>
            </tbody>
        </table>
    </div>

    <div class="ui container center aligned grid" show="{ collabs.length === 0 }">
        <div class="row">
            <div class="four wide column">
                <em>No collaborators yet!</em>
            </div>
        </div>
    </div>

    <div class="ui mini modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Add collaborator
        </div>
        <div class="content">
            <div class="ui message error" if="{errors != null}">
                { errors }
            </div>
            <div class="ui form">
                <div class="field required">
                    <label>
                        Username
                    </label>
                    <div class="ui fluid left icon labeled input search dataset" data-name="{file_field}">
                        <i class="search icon"></i>
                        <input type="text" class="prompt" ref="email">
                        <div class="results"></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="actions">
            <div class="ui button cancel">Cancel</div>
            <div class="ui button primary" onclick="{ add_collaborator }">Add</div>
        </div>
    </div>

    <script>
        var self = this
        self.collabs = []
        self.errors = null
        /*---------------------------------------------------------------------
            Init
        ---------------------------------------------------------------------*/
        self.one("mount", function () {
            // modals
            $(self.refs.modal_button).click(function () {
                $(self.refs.modal).modal('show')
            })
            $('.ui.search', self.root)
                .search({
                    apiSettings: {
                        url: `${URLS.API}user_lookup/?q={query}`,
                    },
                    preserveHTML: false,
                    minCharacters: 2,
                    fields: {
                        title: 'name',
                    },
                    cache: false,
                    maxResults: 5,
                    onSelect: (result, response) => {
                        self.new_collab = result
                    }
                })
        })
        /*---------------------------------------------------------------------
            Methods
        ---------------------------------------------------------------------*/
        self.remove_collaborator = (index, name) => {
            if (confirm(`Remove ${name} as a collaborator`)) {
                self.collabs.splice(index,1)
                self.update()
            }
        }
        self.add_collaborator = () => {
            if (self.new_collab) {
                if (self.new_collab.id === CODALAB.state.user.id) {
                    self.errors = "You cannot add yourself as a collaborator"
                } else if (self.new_collab.username === self.created_by) {
                    self.errors = "You cannot add the competition creator as a collaborator"
                } else if (_.filter(self.collabs, collab => collab.id === self.new_collab.id).length === 0) {
                    self.collabs.push(self.new_collab)
                    self.new_collab = {}
                    $(self.refs.modal).modal('hide')
                    $(self.refs.email).val('')
                    self.errors = null
                } else {
                    self.errors = `${self.new_collab.name} is already a collaborator`
                }
            } else {
                self.errors = ['Username field cannot be blank']
            }
            self.update()
        }
        /*---------------------------------------------------------------------
            Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_loaded', function (competition) {
            self.collabs = competition.collaborators
            self.created_by = competition.created_by
            self.update()
        })
    </script>
</competition-collaborators>