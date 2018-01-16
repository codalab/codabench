<competition-collaborators>
    <button class="ui primary button modal-button" ref="modal_button">
        <i class="add circle icon"></i> Add new collaborator
    </button>

    <h2>Collaborators</h2>
    <table class="ui celled table">
        <thead>
        <tr>

            <th>Name</th>
            <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr>
            <td>Eric Carmichael</td>
            <td class="right aligned collapsing">
                <button class="ui button red">Remove</button>
            </td>
        </tr>
        </tbody>
    </table>
    <div class="ui mini modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Edit collaborator
        </div>
        <div class="content">

            <div class="ui form">
                <div class="field required">
                    <label>Collaborator email</label>
                    <input/>
                </div>
            </div>
        </div>
        <div class="actions">
            <div class="ui button">Cancel</div>
            <div class="ui button primary">Add</div>
        </div>
    </div>

    <script>
        var self = this

        self.has_initialized_calendars = false

        self.one("mount", function () {
            // modals
            $(self.refs.modal_button).click(function () {
                $(self.refs.modal).modal('show')
            })
        })
    </script>
</competition-collaborators>