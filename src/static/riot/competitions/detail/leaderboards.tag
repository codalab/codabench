<leaderboards>
    <div class="ui left action input" style="margin-top: 32px; width: 33%">
        <button type="button" class="ui icon button" id="search-leaderboard-button">
            <i class="search icon"></i>
        </button>
        <input ref="leaderboardFilter" type="text" placeholder="Filter Leaderboard by Columns">
    </div>
    <a data-tooltip="Start typing to filter columns under 'Meta-data' or Tasks." data-position="right center">
        <i class="grey question circle icon"></i>
    </a>
    <table id="leaderboardTable" class="ui celled selectable sortable table">
        <thead>
        <tr>
            <th colspan="100%" class="center aligned">
                <p class="leaderboard-title">{ selected_leaderboard.title }</p>
                <div style="visibility:{show_download}" class="float-right">
                    <div class="ui compact menu">
                        <div class="ui simple dropdown item" style="padding: 0px 5px">
                            <i class="download icon" style="font-size: 1.5em; margin: 0;"></i>
                            <div style="padding-top: 8px; right: 0; left: auto;" class="menu">
                                <a href="{URLS.COMPETITION_GET_CSV(competition_id, selected_leaderboard.id)}" target="new" class="item">This CSV</a>
                                <a href="{URLS.COMPETITION_GET_JSON_BY_ID(competition_id, selected_leaderboard.id)}" target="new" class="item">This JSON</a>
                            </div>
                        </div>
                    </div>
                </div>
            </th>
        </tr>
        <tr class="task-row">
            <th>Task:</th>
            <th colspan=3></th>
            <th each="{ task in filtered_tasks }" class="center aligned" colspan="{ task.colWidth }">{ task.name }</th>
        </tr>
        <tr>
            <th class="center aligned">#</th>
            <th>Participant</th>
            <th>Date</th>
            <th>ID</th>
            <th each="{ column in filtered_columns }" colspan="1">{column.title}</th>
        </tr>
        </thead>
        <!--  Always show leaderboard  -->
        <tbody>
            <tr if="{_.isEmpty(paginated_submissions)}" class="center aligned">
                <td colspan="100%">
                    <em>No submissions have been added to this leaderboard yet!</em>
                </td>
            </tr>

            <tr each="{ submission, index in paginated_submissions}">
                <td class="collapsing index-column center aligned">
                    <gold-medal if="{get_row_number(index) === 1}"></gold-medal>
                    <silver-medal if="{get_row_number(index) === 2}"></silver-medal>
                    <bronze-medal if="{get_row_number(index) === 3}"></bronze-medal>
                    <fourth-place-medal if="{get_row_number(index) === 4}"></fourth-place-medal>
                    <fifth-place-medal if="{get_row_number(index) === 5}"></fifth-place-medal>
                    <virtual if="{get_row_number(index) > 5}">{get_row_number(index)}</virtual>
                </td>
                <td if="{submission.organization === null}"><a href="{submission.slug_url}">{ submission.owner }</a></td>
                <td if="{submission.organization !== null}"><a href="{submission.organization.url}">{ submission.organization.name }</a></td>
                <td data-sort="{ sort_date_value(submission.created_when) }"
                    data-sort-value="{ sort_date_value(submission.created_when) }">
                    { pretty_date(submission.created_when) }
                </td>
                <td>{submission.id}</td>
                <td each="{ column in filtered_columns }">
                    <a if="{column.title == 'Detailed Results'}" href="detailed_results/{get_detailed_result_submisison_id(column, submission)}" target="_blank" class="eye-icon-link">
                        <i class="icon grey eye eye-icon"></i>
                    </a>
                    <span if="{column.title != 'Detailed Results'}" class="{bold_class(column, submission)}">{get_score(column, submission)}</span>
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
                <span> / { total_pages || 1 }</span>
            </div>

            <button class="ui button" onclick="{ go_to_page.bind(this, page + 1) }" disabled="{ page >= total_pages }">
                Next <i class="icon chevron right"></i>
            </button>
        </div>

        <div style="display:flex; align-items:center; gap:8px;">
            <label>Per page</label>
            <select class="ui dropdown" value="{ page_size }" onchange="{ change_page_size.bind(this) }">
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="500">500</option>
                <option value="all">all</option>
            </select>

            <div style="margin-right: 10px; color: #8c8c8c;">
                <small>{ total_count || 0 } total</small>
            </div>
        </div>
    </div>


    <script>
        let self = this
        self.selected_leaderboard = {}
        self.filtered_tasks = []
        self.columns = []
        self.filtered_columns = []
        self.phase_id = null
        self.competition_id = null
        self.enable_detailed_results = false
        self.show_detailed_results_in_leaderboard = false

        self.page = 1
        self.page_size = 50
        self.total_count = 0
        self.total_pages = 1
        self.paginated_submissions = []

        self.get_page_size_value = function () {
            if (String(self.page_size).toLowerCase() === 'all') {
                return self.total_count || 1
            }

            var n = parseInt(self.page_size, 10)
            if (isNaN(n) || n <= 0) {
                return 50
            }

            return n
        }

        self.get_row_number = function (index) {
            if (String(self.page_size).toLowerCase() === 'all') {
                return index + 1
            }

            return ((self.page - 1) * self.get_page_size_value()) + index + 1
        }

        self.update_pagination = function () {
            var submissions = _.get(self.selected_leaderboard, 'submissions', [])

            self.total_count = parseInt(_.get(self.selected_leaderboard, 'count', submissions.length), 10) || submissions.length

            var raw_page_size = _.get(self.selected_leaderboard, 'page_size', self.page_size)

            if (String(raw_page_size).toLowerCase() === 'all') {
                self.page_size = 'all'
                self.total_pages = 1
                self.page = 1
            } else {
                var page_size_value = parseInt(raw_page_size, 10)
                if (isNaN(page_size_value) || page_size_value <= 0) {
                    page_size_value = self.get_page_size_value()
                }

                self.page_size = page_size_value
                self.total_pages = Math.max(1, Math.ceil(self.total_count / page_size_value))

                if (self.page > self.total_pages) {
                    self.page = self.total_pages
                }
            }

            self.paginated_submissions = submissions
        }

        self.go_to_page = function (p) {
            if (String(self.page_size).toLowerCase() === 'all') {
                return
            }

            var newPage = parseInt(p, 10)
            if (isNaN(newPage) || newPage < 1) newPage = 1
            if (newPage > self.total_pages) newPage = self.total_pages
            if (newPage === self.page) return

            self.page = newPage
            self.update_leaderboard()
        }

        self.handle_page_enter = function (e) {
            if (e.key !== 'Enter' && e.keyCode !== 13) {
                return
            }

            e.preventDefault()
            self.go_to_page(e.target.value)
        }

        self.change_page_size = function (e) {
            var raw = (e && e.target && typeof e.target.value !== 'undefined')
                ? String(e.target.value).toLowerCase()
                : String(self.page_size).toLowerCase()

            if (raw === 'all') {
                self.page_size = 'all'
            } else {
                var val = parseInt(raw, 10)
                if (isNaN(val) || val <= 0) return
                if ([50, 100, 500].indexOf(val) === -1) return
                self.page_size = val
            }

            self.page = 1
            self.update_leaderboard()
        }

        self.pretty_date = function (date_string) {
            if (!!date_string) {
                return luxon.DateTime.fromISO(date_string).toFormat('yyyy-MM-dd HH:mm')
            } else {
                return ''
            }
        }

        self.sort_date_value = function (date_string) {
            if (!date_string) return 0
            const dt = luxon.DateTime.fromISO(date_string)
            return dt.isValid ? dt.toMillis() : 0
        }

        self.bold_class = function(column, submission){
            return_class = ''
            if(column.task_id != -1){
                if(submission.scores.length > 1){
                    let column_index = _.get(column, 'index')
                    if(column_index === self.selected_leaderboard.primary_index){
                        return_class = 'text-bold'
                    }
                }
            }
            return return_class
        }

        self.get_score = function(column, submission) {
            if(column.task_id === -1){
                return _.get(submission, 'fact_sheet_answers[' + column.key + ']', 'n/a')
            } else {
                let score = _.get(_.find(submission.scores, {'task_id': column.task_id, 'column_key': column.key}), 'score')
                if (score) {
                    return score
                }
            }
            return 'n/a'
        }

        self.on("mount", function () {
            this.refs.leaderboardFilter.onkeyup = function (e) {
                self.filter_columns()
            }
            $('#search-leaderboard-button').click(function() {
                $(self.refs.leaderboardFilter).focus()
            })
            $('#leaderboardTable').tablesort()
        })

        self.filter_columns = () => {
            let search_key = self.refs.leaderboardFilter.value.toLowerCase()
            self.filtered_tasks = JSON.parse(JSON.stringify(self.selected_leaderboard.tasks || []))

            if (search_key) {
                self.filtered_columns = []
                for (const column of self.columns) {
                    let key = (column.key || '').toLowerCase()
                    let title = (column.title || '').toLowerCase()
                    if ((key.includes(search_key) || title.includes(search_key))) {
                        self.filtered_columns.push(column)
                    } else {
                        let task = _.find(self.filtered_tasks, {id: column.task_id})
                        if (task) task.colWidth -= 1
                    }
                }
                self.filtered_tasks = self.filtered_tasks.filter(task => task.colWidth > 0)
            } else {
                self.filtered_columns = self.columns
            }

            self.update()
        }

        self.update_leaderboard = () => {
            CODALAB.api.get_leaderboard_for_render(self.phase_id, {
                page: self.page,
                page_size: self.page_size
            })
            .done(responseData => {
                self.selected_leaderboard = responseData
                self.columns = []

                if (self.selected_leaderboard.fact_sheet_keys) {
                    let fake_metadata_task = {
                        id: -1,
                        colWidth: self.selected_leaderboard.fact_sheet_keys.length,
                        columns: [],
                        name: "Fact Sheet Answers"
                    }
                    for (question of self.selected_leaderboard.fact_sheet_keys) {
                        fake_metadata_task.columns.push({
                            key: question[0],
                            title: question[1],
                        })
                    }
                    self.selected_leaderboard.tasks.unshift(fake_metadata_task)
                }

                for (task of self.selected_leaderboard.tasks) {
                    for (column of task.columns) {
                        column.task_id = task.id
                        self.columns.push(column)
                    }
                    if (self.enable_detailed_results & self.show_detailed_results_in_leaderboard & task.id != -1) {
                        self.columns.push({
                            task_id: task.id,
                            title: "Detailed Results"
                        })
                        task.colWidth += 1
                    }
                }

                self.filter_columns()
                self.update_pagination()
                $('#leaderboardTable').tablesort()
                self.update()
            })
        }

        self.get_detailed_result_submisison_id = function(column, submisison){
            for (index in submisison.detailed_results) {
                if (column.task_id == submisison.detailed_results[index].task) {
                    return submisison.detailed_results[index].id
                }
            }
        }

        CODALAB.events.on('phase_selected', data => {
            self.phase_id = data.id
            self.page = 1
            self.update_leaderboard()
        })

        CODALAB.events.on('competition_loaded', (competition) => {
            self.competition_id = competition.id
            self.participant_status = competition.participant_status
            self.opts.is_admin ? self.show_download = "visible" : self.show_download = "hidden"
            self.enable_detailed_results = competition.enable_detailed_results
            self.show_detailed_results_in_leaderboard = competition.show_detailed_results_in_leaderboard
        })

        CODALAB.events.on('submission_changed_on_leaderboard', self.update_leaderboard)
    </script>
    
    <style type="text/stylus">
        :scope
            display: block
            width: 100%
            height: 100%
        .celled.table.selectable
            margin 1em 0

        table tbody .center.aligned td
            color #8c8c8c
        .index-column
            min-width 55px
        .leaderboard-title 
            position: absolute
            left: 50%
            transform: translate(-50%, -50%)
        .ui.table > thead > tr.task-row > th
            background-color: #e8f6ff !important
        .eye-icon-link
            position: relative
            display: block
        .eye-icon
            position: absolute
            top: 50%
            left: 50%
            transform: translate(-50%, -50%)
        .text-bold
            font-weight: bold
    </style>
</leaderboards>
