<participant-manager>
    <div show="{participants}">
        <div class="ui icon input">
            <input type="text" placeholder="Search..." ref="participant_search" onkeyup="{ search_participants }">
            <i class="search icon"></i>
        </div>
        <select ref="participant_status" class="ui dropdown" onchange="{ filters_changed }">
            <option value="">Status</option>
            <option value="-">----</option>
            <option value="approved">Approved</option>
            <option value="pending">Pending</option>
            <option value="denied">Denied</option>
            <option value="unknown">Unknown</option>
        </select>
        <div class="ui checkbox">
            <input type="checkbox" ref="participant_show_deleted" onchange="{ filters_changed }">
            <label>Show deleted accounts</label>
        </div>
        <div style="margin-top: 1em;">
            <!--  Email all participants button  -->
            <div class="ui blue icon button" onclick="{show_email_modal.bind(this, undefined)}">
                <i class="envelope icon"></i> Email all participants
            </div>
            <!--  Download all participants button  -->
            <div class="ui blue icon button" onclick="{download_participants_csv}">
                <i class="download icon"></i> Download all participants
            </div>
        </div>
        <table class="ui celled striped sortable table">
            <thead>
            <tr>
                <th class="{ sort_class('user__username') }" onclick="{ sort_by.bind(this, 'user__username') }">Username</th>
                <th class="{ sort_class('user__email') }" onclick="{ sort_by.bind(this, 'user__email') }">Email</th>
                <th class="{ sort_class('organization_sort') }" onclick="{ sort_by.bind(this, 'organization_sort') }">Organization</th>
                <th if="{ has_routing_groups }" class="{ sort_class('routing_groups_sort') }" onclick="{ sort_by.bind(this, 'routing_groups_sort') }">Routing groups</th>
                <th class="{ sort_class('status') }" onclick="{ sort_by.bind(this, 'status') }">Status</th>
                <th class="center aligned" style="cursor: default;">Actions</th>
            </tr>
            </thead>
            <tbody>
            <tr each="{participants}">
                <td><a href="/profiles/user/{username}" target="_BLANK">{username}</a></td>
                <td>{email}</td>
                <td>{ organizations.join(', ') }</td>
                <td if="{ parent.has_routing_groups }">{ routing_groups.join(', ') }</td>
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

        <div class="ui pagination menu" style="display:flex; align-items:center; justify-content:space-between; margin-top: 12px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <button class="ui button" onclick="{ go_to_page.bind(this, page - 1) }" disabled="{ page <= 1 }">
                    <i class="icon chevron left"></i> Previous
                </button>

                <div style="display:flex; align-items:center; gap:6px;">
                    <span>Page</span>
                    <input type="number" min="1" value="{ page }" onkeydown="{ handle_page_enter }" style="width:70px; text-align:center;" />
                    <span> / { total_pages }</span>
                </div>

                <button class="ui button" onclick="{ go_to_page.bind(this, page + 1) }" disabled="{ !next }">
                    Next <i class="icon chevron right"></i>
                </button>
            </div>

            <div style="display:flex; align-items:center; gap:8px;">
                <label>Per page</label>
                <select class="ui dropdown" value="{ page_size }" onchange="{ change_page_size }">
                    <option value="50">50</option>
                    <option value="100">100</option>
                    <option value="500">500</option>
                    <option value="all">1000</option>
                </select>

                <div style="margin-right: 10px; color: #8c8c8c;">
                    <small>{ total_count } total</small>
                </div>
            </div>
        </div>
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
        self.has_routing_groups = false

        // Pagination & sorting (server side, see DynamicChoicePagination)
        self.page = 1
        self.page_size = 50
        self.total_pages = 1
        self.total_count = 0
        self.next = null
        self.ordering = 'user__username'  // DRF ordering field, '-' prefix for descending

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

        self.build_filters = () => {
            let filters = {competition: self.competition_id}
            let status = self.refs.participant_status.value
            if (status && status !== '-') {
                filters.status = status
            }

            let show_deleted_users = self.refs.participant_show_deleted.checked
            if (show_deleted_users !== null && show_deleted_users === false) {
                filters.user__is_deleted = show_deleted_users
            }

            let search = self.refs.participant_search.value
            if (search) {
                filters.search = search
            }

            // Username as tie-breaker so rows don't jump between pages
            filters.ordering = self.ordering.endsWith('user__username') ? self.ordering : `${self.ordering},user__username`
            return filters
        }

        self.update_participants = () => {
            if (!CODALAB.state.user.logged_in) {
                return
            }
            let filters = Object.assign(self.build_filters(), {page: self.page, page_size: self.page_size})

            CODALAB.api.get_participants(filters)
                .done(data => {
                    self.participants = data.results
                    self.has_routing_groups = data.has_routing_groups
                    self.next = data.next
                    self.total_count = data.count
                    let effective_page_size = self.page_size === 'all' ? 1000 : self.page_size
                    self.total_pages = Math.max(1, Math.ceil(data.count / effective_page_size))
                    self.update()
                })
                .fail(resp => {
                    // Current page no longer exists (e.g. rows left the filter after an approve/revoke)
                    if (resp.status === 404 && self.page > 1) {
                        self.page = 1
                        self.update_participants()
                        return
                    }
                    toastr.error('Error returning competition participants')
                })
        }

        // Filters changed: go back to first page
        self.filters_changed = () => {
            self.page = 1
            self.update_participants()
        }

        self.sort_by = field => {
            self.ordering = self.ordering === field ? `-${field}` : field
            self.filters_changed()
        }

        // Semantic UI "sortable table" header classes
        self.sort_class = field => {
            if (self.ordering === field) return 'sorted ascending'
            if (self.ordering === `-${field}`) return 'sorted descending'
            return ''
        }

        self.go_to_page = p => {
            let new_page = parseInt(p, 10)
            if (isNaN(new_page) || new_page < 1) new_page = 1
            if (new_page > self.total_pages) new_page = self.total_pages
            if (new_page === self.page) return
            self.page = new_page
            self.update_participants()
        }

        self.handle_page_enter = ev => {
            if (ev.key === 'Enter') {
                self.go_to_page(ev.target.value)
            }
        }

        self.change_page_size = e => {
            let raw = String(e.target.value).toLowerCase()
            self.page_size = raw === 'all' ? 'all' : parseInt(raw, 10)
            self.filters_changed()
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
            delay(() => self.filters_changed(), 100)
        }

        self.show_email_modal = (participant_pk) => {
            self.selected_participant = participant_pk
            $(self.refs.email_modal).modal('show')
        }

        self.close_email_modal = () => {
            $(self.refs.email_modal).modal('hide')
        }

        // Function to download participants in csv file
        // The table is paginated, so fetch every page (with current filters & sorting)
        self.fetch_all_participants = (page = 1, acc = []) => {
            let filters = Object.assign(self.build_filters(), {page: page, page_size: 'all'})
            return CODALAB.api.get_participants(filters).then(data => {
                acc.push(...data.results)
                return data.next ? self.fetch_all_participants(page + 1, acc) : acc
            })
        }

        self.download_participants_csv = () => {
            self.fetch_all_participants()
                .done(participants => self._download_participants_csv(participants))
                .fail(() => toastr.error('Error returning competition participants'))
        }

        self._download_participants_csv = participants => {
            // Show warning when there is no participant
            if (!participants || participants.length === 0) {
                toastr.warning('No participants to download')
                return
            }

            // prepare csv header
            const headers = ['ID', 'Username', 'Email', 'Organization', 'Status'];
            if (self.has_routing_groups) headers.splice(4, 0, 'Routing groups')
            // prepare csv rows
            const rows = participants.map(p => {
                const row = [p.id, p.username, p.email, p.organizations.join(', '), p.status]
                if (self.has_routing_groups) row.splice(4, 0, p.routing_groups.join(', '))
                return row
            });

            // prepare csv content using header and rows
            const csvContent = [headers, ...rows]
                .map(e => e.map(v => `"${(v ?? '').toString().replace(/"/g, '""')}"`).join(','))
                .join('\n')

            // Download prepared csv as `participants.csv`
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
            const url = URL.createObjectURL(blob)
            const link = document.createElement("a")
            link.setAttribute("href", url)
            link.setAttribute("download", "participants.csv")
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        }

    </script>
</participant-manager>
