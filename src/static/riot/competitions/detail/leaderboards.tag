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
            <th colspan=4></th>
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
        <!--  Show when particpant is not registered  -->
        <tbody if="{participant_status === null}">
            <tr class="center aligned ui yellow message">
                <td colspan="100%">
                    <em>You are not a participant of this competition. Please register in My Submissions tab to view the leaderboard.</em>
                </td>
            </tr>
        </tbody>
        <!--  Show when particpant registration is pending  -->
        <tbody if="{participant_status === 'pending'}">
            <tr class="center aligned ui yellow message">
                <td colspan="100%">
                    <em>Your request to participate in this competition is waiting for an approval from the competition organizer.</em>
                </td>
            </tr>
        </tbody>
        <!--  Show when particpant registration is denied  -->
        <tbody if="{participant_status === 'denied'}">
            <tr class="center aligned ui red message">
                <td colspan="100%">
                    <em>Your request to participate in this competition is denied. Please contact the competition organizer for more details.</em>
                </td>
            </tr>
        </tbody>
        <!--  Show when particpant registration is approved  -->
        <tbody if="{participant_status === 'approved'}">
        <tr if="{_.isEmpty(selected_leaderboard.submissions)}" class="center aligned">
            <td colspan="100%">
                <em>No submissions have been added to this leaderboard yet!</em>
            </td>
        </tr>
        <tr each="{ submission, index in selected_leaderboard.submissions}">
            <td class="collapsing index-column center aligned">
                <gold-medal if="{index + 1 === 1}"></gold-medal>
                <silver-medal if="{index + 1 === 2}"></silver-medal>
                <bronze-medal if="{index + 1 === 3}"></bronze-medal>
                <fourth-place-medal if="{index + 1 === 4}"></fourth-place-medal>
                <fifth-place-medal if="{index + 1 === 5}"></fifth-place-medal>
                <virtual if="{index + 1 > 5}">{index + 1}</virtual>
            </td>
            <td if="{submission.organization === null}"><a href="{submission.slug_url}">{ submission.owner }</a></td>
            <td if="{submission.organization !== null}"><a href="{submission.organization.url}">{ submission.organization.name }</a></td>
            <td>{ pretty_date(submission.created_when) }</td>
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

        self.pretty_date = function (date_string) {
            if (!!date_string) {
                return luxon.DateTime.fromISO(date_string).toFormat('yyyy-MM-dd HH:mm')
            } else {
                return ''
            }
        }
       
        self.bold_class = function(column, submission){
            // Return `text-bold` if submission has 
            // more than one scores and score index  == leaderbaord.primary_index
            // otherwise return empty string
            return_class = '' // default class value
            if(column.task_id != -1){ // factsheet check
                if(submission.scores.length > 1){ // score length check
                    let column_index = _.get(column, 'index')
                    if(column_index === self.selected_leaderboard.primary_index){ // column index check
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

        self.on("mount" , function () {
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
            self.filtered_tasks = JSON.parse(JSON.stringify(self.selected_leaderboard.tasks))
            if(search_key){
                self.filtered_columns = []
                for (const column of self.columns){
                    let key = column.key.toLowerCase()
                    let title = column.title.toLowerCase()
                    if((key.includes(search_key) || title.includes(search_key))) {
                        self.filtered_columns.push(column)
                    }
                    else {
                        let task = _.find(self.filtered_tasks, {id: column.task_id})
                        task.colWidth -= 1
                    }
                }
                self.filtered_tasks = self.filtered_tasks.filter(task => task.colWidth > 0)
            } else {
                self.filtered_columns = self.columns
            }
            self.update()
        }

        self.update_leaderboard = () => {
            CODALAB.api.get_leaderboard_for_render(self.phase_id)
                .done(responseData => {
                    self.selected_leaderboard = responseData
                    self.columns = []
                    // Make fake task and columns for Metadata so it can be filtered like columns
                    if(self.selected_leaderboard.fact_sheet_keys){
                        let fake_metadata_task = {
                            id: -1,
                            colWidth: self.selected_leaderboard.fact_sheet_keys.length,
                            columns: [],
                            name: "Fact Sheet Answers"
                        }
                        for(question of self.selected_leaderboard.fact_sheet_keys){
                            fake_metadata_task.columns.push({
                                key: question[0],
                                title: question[1],
                            })
                        }
                        self.selected_leaderboard.tasks.unshift(fake_metadata_task)
                    }
                    for(task of self.selected_leaderboard.tasks){

                        for(column of task.columns){
                            column.task_id = task.id
                            self.columns.push(column)
                        }
                        // -1 id is used for fact sheet answers
                        if(self.enable_detailed_results & self.show_detailed_results_in_leaderboard & task.id != -1){
                            self.columns.push({
                              task_id: task.id,
                              title: "Detailed Results"
                            })
                            task.colWidth += 1
                        }
                    }
                    self.filter_columns()
                    $('#leaderboardTable').tablesort()
                    self.update()
                })
        }

        self.get_detailed_result_submisison_id = function(column, submisison){
            for (index in submisison.detailed_results) {
                if(column.task_id == submisison.detailed_results[index].task){
                    return submisison.detailed_results[index].id
                }
            }
        }


        CODALAB.events.on('phase_selected', data => {
            self.phase_id = data.id
            self.update_leaderboard()
        })

        CODALAB.events.on('competition_loaded', (competition) => {
            self.competition_id = competition.id
            self.participant_status = competition.participant_status
            self.opts.is_admin ? self.show_download = "visible": self.show_download = "hidden"
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
            position absolute
            left 50%
            transform translate(-50%, 50%)
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
