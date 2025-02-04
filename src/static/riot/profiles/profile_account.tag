<profile-account>
    <!-- Delete account section -->
    <div id="delete-account">
        <h2 class="title danger">Delete account</h2>
        <div class="ui divider"></div>
        <p><b>Warning:</b> Deleting your account is permanent and cannot be undone. All your personal data, settings, and content will be permanently erased, and you will lose access to all services linked to your account. Please make sure to back up any important information before proceeding.</p>
        <button type="button" class="ui button delete-button" ref="delete_button" onclick="{show_modal.bind(this, '.delete-account.modal')}">Permanently delete my account</button>
    </div>

    <!-- Delete account modal -->
    <div class="ui delete-account modal tiny" ref="delete_account_modal">
        <div class="header">Are you sure you want to do this ?</div>

        <div class="ui bottom attached negative message">
            <i class="exclamation triangle icon"></i>
            This is extremely important.
        </div>

        <div class="content">
            <p>By clicking <b>"Delete my account"</b> you will receive a confirmation email to proceed with your account deletion.
            <br><br>
            This action is irreversible: all personal data will be permanently deleted or anonymized, <b>except for competitions and submissions</b> retained under the platform's user agreement.
            <br><br>
            If you wish to delete your submissions or competitions, please do so before deleting your account.
            <br><br>
            You will also no longer be eligible for any cash prizes in competitions you are participating in.
            <br><br>
            You will not be able to re-create an account using the same email address for 30 days.
            </p>
            <div class="ui divider"></div>

            <form class="ui form" id="delete-account-form" onsubmit="{handleDeleteAccountSubmit}">
                <div class="required field">
                    <label for="username">Your username</label>
                    <input type="text" id="username" name="username" required oninput="{checkFields}" />
                </div>

                <div class="required field">
                    <label for="confirmation">Type <i>delete my account</i> to confirm</label>
                    <input type="text" id="confirmation" name="confirmation" required oninput="{checkFields}" />
                </div>

                <div class="required field">
                    <label for="password">Confirm your password</label>
                    <input type="password" id="password" name="password" required />
                </div>

                <button class="ui button fluid delete-button" type="submit" disabled="{isDeleteAccountSubmitButtonDisabled}" >Delete my account</button>
            </form>
        </div>
    </div>

    <script>
        self = this;
        self.user = user;

        self.isDeleteAccountSubmitButtonDisabled = true;

        self.show_modal = selector => $(selector).modal('show');
        self.hide_modal = selector => $(selector).modal('hide');

        self.checkFields = function() {
            const formValues = $('#delete-account-form').form('get values');
            const username = formValues.username;
            const confirmation = formValues.confirmation;

            if (username === self.user.username && confirmation === "delete my account") {
                self.isDeleteAccountSubmitButtonDisabled = false;
            } else {
                self.isDeleteAccountSubmitButtonDisabled = true;
            }

            self.update();
        }

        handleDeleteAccountSubmit = function(event) {
            event.preventDefault();

            const formValues = $('#delete-account-form').form('get values');

            CODALAB.api.request_delete_account(formValues)
                .done(function (response) {
                    const success = response.success;
                    if (success) {
                        toastr.success(response.message);
                        self.hide_modal('.delete-account.modal')
                    } else {
                        toastr.error(response.error);
                    }
                })
                .fail(function () {
                    toastr.error("An error occured. Please contact administrators");
                })
        }
    </script>

    <style type="text/stylus">
        .title {
            font-size: 24px;
            font-weight: 600;
            color: #24292f;
        }
        .danger {
            color: #db2828;
        }
        .delete-button {
            color: #db2828 !important;
        }
        .delete-button:hover {
            background-color: #db2828 !important;
            color: white !important;
        }
    </style>
</profile-account>