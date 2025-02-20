<participant-manager>
    <div show="{participants}">
        <div class="ui icon input">
            <input type="text" placeholder="Search..." ref="participant_search" onkeyup="{ search_participants }">
            <i class="search icon"></i>
        </div>
        <select ref="participant_status" class="ui dropdown" onchange="{ update_participants.bind(this, undefined) }">
            <option value="">Status</option>
            <option value="-">----</option>
            <option value="approved">Approved</option>
            <option value="pending">Pending</option>
            <option value="denied">Denied</option>
            <option value="unknown">Unknown</option>
        </select>
        <div class="ui checkbox">
            <input type="checkbox" ref="participant_show_deleted" onchange="{ update_participants.bind(this, undefined) }">
            <label>Show deleted accounts</label>
        </div>
        <div class="ui blue icon button" onclick="{show_email_modal.bind(this, undefined)}"><i class="envelope icon"></i> Email all participants</div>
        <table class="ui celled striped table">
            <thead>
            <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Is Bot?</th>
                <th>Status</th>
                <th class="center aligned">Actions</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{participants}">
                <td><a href="/profiles/user/{username}" target="_BLANK">{username}</a></td>
                <td>{email}</td>
                <td>{is_bot}</td>
                <td>{is_deleted ? "account deleted" : _.startCase(status)}</td>
                <td class="right aligned">
                    <button class="mini ui red button icon"
                            show="{status !== 'denied'}"
                            onclick="{ revoke_permission.bind(this, id) }"
                            data-tooltip="Revoke"
                            data-inverted=""
                            data-position="bottom center"
                            disabled="{is_deleted}">
                        <i class="close icon"></i>
                    </button>
                    <button class="mini ui green button icon"
                            show="{status !== 'approved'}"
                            onclick="{ approve_permission.bind(this, id) }"
                            data-tooltip="Approve"
                            data-inverted=""
                            data-position="bottom center"
                            disabled="{is_deleted}"
                            >
                            <i class="checkmark icon"></i>
                    </button>
                    <button class="mini ui blue button icon"
                            data-tooltip="Send Message"
                            data-inverted=""
                            data-position="bottom center"
                            onclick="{show_email_modal.bind(this, id)}"
                            disabled="{is_deleted}"
                            >
                        <i class="envelope icon"></i>
                    </button>
                </td>
            </tr>
            </tbody>
        </table>
    </div>

    <div class="ui modal" ref="email_modal">
        <div class="header">
            Send Email
        </div>
        <div class="content">
            <div class="ui form">
                <div class="field">
                    <label>Subject</label>
                    <input type="text" value="A message from the admins of {competition_title}" disabled>
                </div>
                <div class="field">
                    <label>Content</label>
                    <textarea class="markdown-editor" ref="email_content" name="content"></textarea>
                </div>
            </div>
        </div>
        <div class="actions">
            <div class="ui cancel icon red small button"><i class="trash alternate icon"></i></div>
            <div class="ui icon small button" onclick="{send_email}"><i class="paper plane icon"></i></div>
        </div>
    </div>

    <script>
        let self = this
        self.competition_id = undefined
        self.selected_participant = undefined
        self.competition_title = undefined

        self.on('mount', () => {
            $(self.refs.participant_status).dropdown()
            self.markdown_editor = create_easyMDE(self.refs.email_content)
            $(self.refs.email_modal).modal({
                onHidden: self.clear_form,
                onShow: () => {
                    _.delay(() => {self.markdown_editor.codemirror.refresh()}, 5)
                }
            })
        })

        self.clear_form = function () {
            self.markdown_editor.value('')
            self.update()
        }

        CODALAB.events.on('competition_loaded', function(competition) {
            self.competition_title = competition.title
            self.competition_id = competition.id
            self.update_participants()
        })

        self.send_email = function () {
            let content = render_markdown(self.refs.email_content.value)
            let func = self.selected_participant
                ? _.partial(CODALAB.api.email_participant, self.selected_participant)
                : _.partial(CODALAB.api.email_all_participants, self.competition_id)
            func(content)
                .done(() => {
                    toastr.success('Sent')
                    self.close_email_modal()
                })
                .fail((resp) => {
                    toastr.error('Error sending email')
                })
        }

        self.update_participants = filters => {
            if (!CODALAB.state.user.logged_in) {
                return
            }
            filters = filters || {}
            filters.competition = self.competition_id
            let status = self.refs.participant_status.value
            if (status && status !== '-') {
                filters.status = status
            }

            let show_deleted_users = self.refs.participant_show_deleted.checked
            if (show_deleted_users !== null && show_deleted_users === false) {
                filters.user__is_deleted = show_deleted_users
            }

            CODALAB.api.get_participants(filters)
                .done(participants => {
                    self.participants = participants
                    self.update()
                })
                .fail(() => {
                    toastr.error('Error returning competition participants')
                })
        }

        self._update_status = (id, status) => {
            CODALAB.api.update_participant_status(id, {status: status})
                .done(() => {
                    if(status === 'denied'){
                        toastr.success('Revoked successfully')
                    }else{
                        toastr.success('Approved successfully')
                    }
                    self.update_participants()
                })
                .fail((resp) => {
                    let errorMessage = 'An error occurred while updating the status.'
                    if (resp.responseJSON && resp.responseJSON.error) {
                        errorMessage = resp.responseJSON.error
                    }
                    toastr.error(errorMessage)
                })
        }

        self.revoke_permission = id => {
            if (confirm("Are you sure you want to revoke this user's permissions?")) {
                self._update_status(id, 'denied')
            }
        }

        self.approve_permission = id => {
            if (confirm("Are you sure you want to accept this user's participation request?")) {
                self._update_status(id, 'approved')
            }
        }

        self.search_participants = () => {
            let filter = self.refs.participant_search.value
            delay(() => self.update_participants({search: filter}), 100)
        }

        self.show_email_modal = (participant_pk) => {
            self.selected_participant = participant_pk
            $(self.refs.email_modal).modal('show')
        }

        self.close_email_modal = () => {
            $(self.refs.email_modal).modal('hide')
        }

    </script>
</participant-manager>
