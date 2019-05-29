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
        <table class="ui celled striped table">
            <thead>
            <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Status</th>
                <th class="center aligned">Actions</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{participants}">
                <td>{username}</td>
                <td>{email}</td>
                <td>{_.startCase(status)}</td>
                <td class="right aligned">
                    <button class="mini ui red button icon" show="{status !== 'denied'}"
                            onclick="{ revoke_permission.bind(this, id) }"
                            data-tooltip="Revoke"
                            data-inverted=""
                            data-position="bottom center">
                        <i class="close icon"></i>
                    </button>
                    <button class="mini ui green button icon" show="{status !== 'approved'}"
                            onclick="{ approve_permission.bind(this, id) }"
                            data-tooltip="Approve"
                            data-inverted=""
                            data-position="bottom center">
                            <i class="checkmark icon"></i>
                    </button>
                    <button class="mini ui blue button icon"
                            data-tooltip="Send Message"
                            data-inverted=""
                            data-position="bottom center"
                            onclick="">
                        <i class="envelope icon"></i>
                    </button>
                </td>
            </tr>
            </tbody>
        </table>
    </div>


    <script>
        let self = this


        self.on('mount', () => {
            self.update_participants()
            $(self.refs.participant_status).dropdown()
        })

        self.update_participants = filters => {
            filters = filters || {}
            filters.competition = opts.competition_id
            let status = self.refs.participant_status.value
            if (status && status !== '-') {
                filters.status = status
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
            CODALAB.api.update_status(id, {status: status})
                .done(() => {
                    toastr.success('success')
                    self.update_participants()
                })
        }

        self.revoke_permission = id => {
            if (confirm("Are you sure you want to revoke this user's permissions?")) {
                self._update_status(id, 'denied')
            }
        }

        self.approve_permission = id => {
            self._update_status(id, 'approved')
        }

        self.search_participants = () => {
            let filter = self.refs.participant_search.value
            delay(() => self.update_participants({search: filter}), 100)
        }

    </script>
</participant-manager>