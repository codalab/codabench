<delete-account>
    <!-- Delete account section -->
    <div id="delete-account">
        <!-- Same box as the critical announcements on the home page -->
        <div class="announcement announcement-critical settings-notice">
            <i class="announcement-icon exclamation circle icon"></i>
            <div class="announcement-content">
                <div class="announcement-title">Warning</div>
                <div class="announcement-body">Deleting your account is permanent and cannot be undone. All your personal data, settings, and content will be permanently erased, and you will lose access to all services linked to your account. Please make sure to back up any important information before proceeding.</div>
            </div>
        </div>
        <button type="button" class="settings-button settings-button-danger" onclick="{open_modal}">Permanently delete my account</button>
    </div>

    <!-- Delete account modal. A click on the dark background closes it -->
    <div if="{modal_open}" class="delete-modal-backdrop" onclick="{on_backdrop_click}">
        <div class="delete-modal" role="dialog" aria-modal="true" aria-labelledby="delete-modal-title">
            <div class="delete-modal-header">
                <h2 id="delete-modal-title" class="delete-modal-title">Delete your account?</h2>
                <button type="button" class="delete-modal-close" aria-label="Close" onclick="{close_modal}"><i class="bi bi-x-lg"></i></button>
            </div>

            <div class="announcement announcement-critical settings-notice">
                <i class="announcement-icon exclamation circle icon"></i>
                <div class="announcement-content">
                    <div class="announcement-title">This is extremely important.</div>
                    <div class="announcement-body">If you just want to change your username, contact us instead at <b>{contact_email}</b></div>
                </div>
            </div>

            <ul class="delete-modal-list">
                <li>By clicking <b>Delete my account</b> you will receive a confirmation email to proceed with your account deletion.</li>
                <li>This action is irreversible: all personal data will be permanently deleted or anonymized, <b>except for competitions and submissions</b> retained under the platform's user agreement.</li>
                <li>If you wish to delete your submissions or competitions, please do so before deleting your account.</li>
                <li>You will also no longer be eligible for any cash prizes in competitions you are participating in.</li>
                <li class="settings-danger-text"><b>You will not be able to re-create an account using the same email address for 30 days.</b></li>
            </ul>

            <form class="ui form" id="delete-account-form" onsubmit="{submit_delete_request}">
                <div class="required field">
                    <label for="username">Your username</label>
                    <input type="text" id="username" name="username" required oninput="{check_fields}" />
                </div>

                <div class="required field">
                    <label for="confirmation">Type <span class="delete-modal-phrase">{confirmation_phrase}</span> below to confirm</label>
                    <input type="text" id="confirmation" name="confirmation" placeholder="{confirmation_phrase}" autocomplete="off" required oninput="{check_fields}" />
                </div>

                <div class="required field">
                    <label for="password">Confirm your password</label>
                    <input type="password" id="password" name="password" required />
                </div>

                <div class="delete-modal-buttons">
                    <button type="button" class="settings-button settings-button-secondary" onclick="{close_modal}">Cancel</button>
                    <button type="submit" class="settings-button settings-button-danger" disabled="{is_submit_disabled}">Delete my account</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        var self = this;
        self.username = username;
        self.contact_email = contact_email;
        self.modal_open = false;
        self.is_submit_disabled = true;
        self.confirmation_phrase = "DELETE MY ACCOUNT";

        self.open_modal = function() {
            self.modal_open = true;
            self.is_submit_disabled = true;
            // Stops the page behind the modal from scrolling
            $('html').addClass('delete-modal-open');
            self.update();
        }

        self.close_modal = function() {
            self.modal_open = false;
            $('html').removeClass('delete-modal-open');
            self.update();
        }

        // Why the check: a click inside the modal also reaches the background
        self.on_backdrop_click = function(event) {
            if (event.target === event.currentTarget) {
                self.close_modal();
            }
        }

        self.get_form_values = function() {
            return Object.fromEntries(new FormData(document.getElementById('delete-account-form')));
        }

        // The button stays disabled until the username and the sentence are typed correctly
        self.check_fields = function() {
            const form_values = self.get_form_values();
            self.is_submit_disabled = !(form_values.username === self.username && form_values.confirmation === self.confirmation_phrase);
            self.update();
        }

        self.submit_delete_request = function(event) {
            event.preventDefault();

            CODALAB.api.request_delete_account(self.get_form_values())
                .done(function (response) {
                    if (response.success) {
                        toastr.success(response.message);
                        self.close_modal();
                    } else {
                        toastr.error(response.error);
                    }
                })
                .fail(function () {
                    toastr.error("An error occured. Please contact administrators");
                })
        }

        // The Escape key closes the modal
        $(document).on('keydown', function (event) {
            if (event.key === 'Escape' && self.modal_open) {
                self.close_modal();
            }
        })
    </script>

    <!-- Why these rules stay: Riot styles apply to every page, and other pages use these class names.
         The new styles of this page are in stylus/components/settings.styl -->
    <style type="text/stylus">
        .title {
            font-size: 24px;
            font-weight: 600;
            color: #24292f;
        }
        .danger {
            color: #db2828;
        }
    </style>
</delete-account>
