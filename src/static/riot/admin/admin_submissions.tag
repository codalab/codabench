<!-- Field class on initial definition to keep Semantic UI styling -->
<field class="field">
    <div class="field {error: opts.error}">
        <label>{opts.name}</label>
        <input type="text" name="{ opts.input_name }" ref="input">
    </div>
    <div class="ui error message" show="{ opts.error }">
        <p>{ opts.error }</p>
    </div>
    <style>
        /* Make this component "div like" */
        :scope {
            display: block;
        }
    </style>
</field>

<submission-management>
    <!-- Top buttons -->
    <div class="ui right aligned grid">
        <div class="sixteen wide column">
            <button class="ui green button" onclick="{ add }">
                <i class="add square icon"></i> Add new Submission
            </button>
        </div>
    </div>

    <!-- Table -->
    <table class="ui table stackable">
        <thead>
        <tr>
            <th>ID</th>
            <th>Description</th>
            <th>Owner</th>
            <th class="center aligned two wide">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr each="{ submission in submissions }">
            <td>{ submission.pk }</td>
            <td>{ submission.description }</td>
            <td><a href="#">{ submission.owner }</a></td>
            <td class="center aligned">
                <div class="ui small basic icon buttons">
                    <button class="ui button" onclick="{ edit.bind(this, submission) }"><i class="edit icon"></i></button>
                    <button class="ui button" onclick="{ delete.bind(this, submission) }"><i class="red delete icon"></i></button>
                </div>
            </td>
        </tr>
        </tbody>
    </table>

    <!-- Form modal -->
    <div id="submission_form_modal" class="ui modal">
        <div class="header">Submission form</div>
        <div class="content">
            <form id="submission_form" class="ui form error" onsubmit="{ save }">
                <!--<field name="Name" ref="name" input_name="name" error="{errors.name}"></field>-->
                <field name="Description" ref="description" input_name="description" error="{errors.description}"></field>
                <field name="Owner" ref="owner" input_name="owner" error="{errors.owner}"></field>
            </form>
        </div>
        <div class="actions">
            <input type="submit" class="ui button" form="submission_form" value="Save"/>
            <div class="ui cancel button">Cancel</div>
        </div>
    </div>

    <!-- New key modal -->
    <div id="submission_secret_key_modal" class="ui modal">
        <div class="header">Secret key</div>
        <div class="content">
            <div class="ui grid">
                <div class="column sixteen wide center aligned">
                    <h3 class="ui center aligned header">{secret_key}</h3>
                    <p class="ui center aligned">Send this key to the submission, it will not be revealed again.</p>
                </div>
            </div>
        </div>
        <div class="actions">
            <div class="ui cancel button">I've copied down this key</div>
        </div>
    </div>

    <script>
        // --------------------------------------------------------------------
        // Initializers
        var self = this
        self.comp_pk = 1
        self.submissions = {}
        self.selected_submission = {}
        self.errors = []

        // --------------------------------------------------------------------
        // Events
        self.one('mount', function () {
            self.update_submissions()
            // console.log(self.submissions)
        })

        // --------------------------------------------------------------------
        // Helpers
        self.update_submissions = function () {
            CODALAB.api.get_submissions()
                .done(function (data) {
                    // console.log(data)
                    // self.submissions = data
                    // console.log(self.submissions)
                    // self.update()
                    self.update({submissions: data})
                    console.log(self.submissions)
                })
                .fail(function (error) {
                    toastr.error("Error fetching submissions " + error.statusText)
                })
        }

        self.add = function () {
            $("#submission_form_modal").modal('show')

            // We want to unselect the existing producer, so when we save we don't try to update it
            self.selected_submission= {}
        }

        self.edit = function (submission) {
            self.selected_submission = submission

            // We have to use our references to the custom <fields> to get their references to
            // the inputs!
            // Example for name:
            // <field ref="name"> -> <input ref="input">
            // self.refs.name.refs.input.value = submission.name
            self.refs.description.refs.input.value = submission.description
            self.refs.owner.refs.input.value = submission.owner

            self.update()

            $("#submission_form_modal").modal('show')
        }

        self.save = function (save_event) {
            // Stop the form from propagating
            save_event.preventDefault()

            // var data = $("#submission_form").serializeObject()
            var my_temp_form_selector = $("#submission_form")
            var data = get_form_data(my_temp_form_selector)
            var endpoint = undefined  // we'll pick form create OR update for the endpoint

            if (!self.selected_submission.id) {
                endpoint = CODALAB.api.create_submission(data)
            } else {
                endpoint = CODALAB.api.update_submission(self.selected_submission.id, data)

                self.selected_submission = {}
            }

            endpoint
                .done(function (data) {
                    toastr.success("Successfully saved submission")

                    self.update_submissions()

                    $("#submission_form_modal").modal('hide')

                    $("#submission_form")[0].reset();

                    if (data.api_key) {
                        // We received a secret key, so we must have made a new producer. Show the
                        // key so it can be copied down
                        $("#submission_secret_key_modal").modal('show')
                        self.update({secret_key: data.api_key})
                    }
                })
                .fail(function (response) {
                    if (response) {
                        var errors = JSON.parse(response.responseText);

                        // Clean up errors to not be arrays but plain text
                        Object.keys(errors).map(function (key, index) {
                            errors[key] = errors[key].join('; ')
                        })

                        self.update({errors: errors})
                    }
                })
        }

        self.delete = function (producer) {
            if (confirm("Are you sure you want to delete this?")) {
                CODALAB.api.delete_submission(submission.id)
                    .done(function () {
                        toastr.success("Deleted!")
                        self.update_submissions()
                    })
                    .fail(function (response) {
                        toastr.error("Could not delete.\n\n" + response.responseText)
                    })
            }
        }
    </script>
</submission-management>