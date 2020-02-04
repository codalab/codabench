<submission-scores>
    <form class="ui form" id="score_update_form">
        <div each="{leaderboard in leaderboards}" class="leaderboard">
            <h3>{leaderboard.title}</h3>

            <table class="ui collapsing table">
                <thead>
                <tr>
                    <th each="{column in leaderboard.columns}">
                        {column.title}
                    </th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td each="{column in leaderboard.columns}">
                        <input type="number" name="{ column.score_id }"
                               disabled="{ !!column.computation }"
                               value="{ column.score }" step="any">
                    </td>
                </tr>
                </tbody>
            </table>
        </div>
        <button class="ui blue button" onclick="{ update_scores }">
            Submit
        </button>
    </form>

    <script>
        let self = this

        self.on('update', () => {
            self.leaderboards = opts.leaderboards
        })

        self.update_scores = function (event) {
            event.preventDefault()
            let data = get_form_data($('#score_update_form', self.root))
            _.forEach(_.keys(data), (key) => {
                CODALAB.api.update_submission_score(key, {score: data[key]})
                    .done(function (data) {
                        toastr.success('Score updated')
                        CODALAB.events.trigger('score_updated')
                    })
            })
        }
    </script>

    <style type="text/stylus">
        .leaderboard
            padding-bottom 10px
    </style>
</submission-scores>
