<comp-run-info>
    <div class="comp-run-info">
        <div class="comp-leaderboard">
            <table class="ui tiny unstackable single line table">
                <thead>
                <tr>
                    <th>Rank</th>
                    <th>Username</th>
                    <th class="score">Score</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td><img src="{ URLS.STATIC('img/gold_medal.svg') }"></td>
                    <td>Machine_Wizard</td>
                    <td class="score">9001</td>
                </tr>
                <tr>
                    <td><img src="{ URLS.STATIC('img/silver_medal.svg') }"></td>
                    <td>traincomps98</td>
                    <td class="score">6500</td>
                </tr>
                <tr>
                    <td><img src="{ URLS.STATIC('img/bronze_medal.svg') }"></td>
                    <td>digitaldynamo</td>
                    <td class="score">5200</td>
                </tr>
                <tr>
                    <td><img src="{ URLS.STATIC('img/4th_medal.svg') }"></td>
                    <td>nick_name</td>
                    <td class="score">2250</td>
                </tr>
                <tr>
                    <td><img src="{ URLS.STATIC('img/5th_medal.svg') }"></td>
                    <td>grade_a_learning</td>
                    <td class="score">1375</td>
                </tr>
                </tbody>
            </table>
        </div>

        <div class="comp-submissions">
            <table class="ui unstackable single line table">
                <thead>
                <tr>
                    <th>Public Submissions</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>John Lilki</td>
                </tr>
                <tr>
                    <td>Jamie Harington</td>
                </tr>
                <tr>
                    <td>Jill Lewis</td>
                </tr>
                <tr>
                    <td>John Lilki</td>
                </tr>
                <tr>
                    <td>Jamie Harington</td>
                </tr>
                </tbody>
            </table>
        </div>

        <div class="comp-comments">
            <table class="ui unstackable single line table">
                <thead>
                <tr>
                    <th>Comment Feed</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>John Lilki</td>
                </tr>
                <tr>
                    <td>Jamie Harington</td>
                </tr>
                <tr>
                    <td>Jill Lewis</td>
                </tr>
                <tr>
                    <td>John Lilki</td>
                </tr>
                <tr>
                    <td>Jamie Harington</td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
    <style type="text/stylus">
        .comp-run-info
            width inherit
            display grid
            grid-template "comp-leaderboard" "comp-submissions" "comp-comments"
            grid-gap 10px

        .comp-leaderboard
            grid-template-areas comp-leaderboard
            height 100%

            table
                height 100%

            table td
                font-size 13px

                img
                    height 24px

            th.score, td.score
                text-align center

        .comp-submissions
            grid-template-areas comp-submissions
            height 100%

            table
                height 100%

        .comp-comments
            grid-template-areas comp-comments
            height 100%

            table
                height 100%

        @media screen and (min-width 700px) {
            .comp-run-info {
                grid-template-columns 1fr 1fr 1fr
                grid-template "comp-leaderboard comp-submissions comp-comments"
            }
        }
    </style>
    <script>
        var self = this
        self.competition = {}
        CODALAB.events.on('competition_loaded', function(competition) {
            self.competition = competition
        })
    </script>
</comp-run-info>