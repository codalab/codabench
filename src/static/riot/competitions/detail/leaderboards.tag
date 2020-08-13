<leaderboards>
    <table id="leadboardTable" class="ui celled selectable table">
        <thead>
        <tr>
            <th colspan="100%" class="center aligned">
                { selected_leaderboard.title }
                <a  href="{URLS.COMPETITION_GET_CSV(competition_id, selected_leaderboard.id)}" target="new"><button class="ui inline button right">CSV</button></a>
                <a  href="{URLS.COMPETITION_GET_JSON(competition_id, selected_leaderboard.id)}" target="new"><button class="ui inline button right">JSON</button></a>
            </th>
        </tr>
        <tr>
            <th class="center aligned">#</th>
            <th>Username</th>
            <th each="{ column in selected_leaderboard.columns }" if="{!_.includes(hidden_column_keys, column.key)}">{ column.title }</th>
        </tr>
        </thead>
        <tbody>
        <tr if="{_.isEmpty(selected_leaderboard.submissions)}" class="center aligned">
            <td colspan="100%">
                <em>No submissions have been added to this leaderboard yet!</em>
            </td>
        </tr>
        <tr each="{ submission, index in selected_leaderboard.submissions }">
            <td class="collapsing index-column center aligned">
                <gold-medal if="{index + 1 === 1}"></gold-medal>
                <silver-medal if="{index + 1 === 2}"></silver-medal>
                <bronze-medal if="{index + 1 === 3}"></bronze-medal>
                <fourth-place-medal if="{index + 1 === 4}"></fourth-place-medal>
                <fifth-place-medal if="{index + 1 === 5}"></fifth-place-medal>
                <virtual if="{index + 1 > 5}">{index + 1}</virtual>
            </td>
            <td>{ submission.owner }</td>
            <td each="{ column in selected_leaderboard.columns }" if="{!_.includes(hidden_column_keys, column.key)}">{ get_score(column, submission) } </td>
        </tr>
        </tbody>
    </table>
    <script>
        let self = this
        self.selected_leaderboard = {}
        self.hidden_column_keys = []
        self.filtered_column_keys = new Set()
        self.competition_id = 0

        self.get_score = function(column, submission) {
             return _.get(_.find(submission.scores, {column_key: column.key}), 'score', 'N/A')
        }

        self.update_leaderboard = () => {
            if (_.isEmpty(self.selected_leaderboard)) {
                return
            }
            self.hidden_column_keys = _.map(self.selected_leaderboard.columns, col => {
                if (col.hidden) {
                    return col.key
                }
            })
            self.update()
        }

        self.update_leaderboards = function () {
            if (!self.opts.leaderboards) {
                return
            }
            _.forEach(self.opts.leaderboards, leaderboard => {
                CODALAB.api.get_leaderboard(leaderboard.id)
                    .done(function (data) {
                        leaderboard.submissions = data.submissions
                        self.update_leaderboard()
                    })
                    .fail(function (response) {
                        toastr.error("Could not find leaderboard submissions")
                    })
            })
        }

        // self.filterLeaderboard = function () {
        //     let tempStr = self.refs.leaderboardFilter.value.toLowerCase()
        //     let finalArray = tempStr.match(/[a-z]+[:][a-z,0-9]+/g)
        //     if(finalArray == null){return false}
        //     for(i =0; i < finalArray.length; i++) {
        //         console.log(finalArray[i])
        //     }
        // }
        //
        // self.on("mount", function () {
        //     this.refs.leaderboardFilter.onkeyup = _.debounce(self.filterLeaderboard, 250, {
        //         'leading': true,
        //         'trailing': true,
        //         'maxWait': 500
        //     })
        // })
        //
        CODALAB.events.on('competition_loaded', () => {
            self.selected_leaderboard = self.opts.leaderboards[0]
            self.competition_id = self.opts.competition_pk
            self.update_leaderboards()
        })

        CODALAB.events.on('leaderboard_selected', leaderboard => {
            self.selected_leaderboard = leaderboard
            self.update_leaderboard()
        })

        CODALAB.events.on('submission_added_to_leaderboard', self.update_leaderboards)

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
    </style>
</leaderboards>
