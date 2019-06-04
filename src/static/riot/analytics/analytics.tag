<analytics>
    <h1>Analytics</h1>

    <div class='date-selection'>
        <div class='date-pickers'>
            <p>Start Date <input type='text' class='date-picker' id='start-date-picker' placeholder="{start_date}"></p>
            <p>End Date <input type='text' class='date-picker' id='end-date-picker' placeholder="{end_date}"></p>
        </div>
        <div class='date-submit'>
            <button id='update-data'>Update Data</button>
        </div>
    </div>

    <h2>Competition Data</h2>

    <table>
        <tr>
            <th>Competitions</th>
            <th>Published Competitions</th>
        </tr>
        <tr>
            <td>{competitions}</td>
            <td>{competitions_published}</td>
        </tr>
    </table>

    <canvas id="competition_chart"></canvas>

    <!--
    <div each="{year, y in competitions_monthly}">
        <h3>{y}</h3>
        <table>
            <tr>
                <th each="{month_count, month in year}">{month}</th>
            </tr>
            <tr>
                <td each="{month_count, month in year}">{month_count}</th>
            </tr>
        </table>
    </div>
    -->

    <h2>Submission Data</h2>

    <canvas id="submission_chart"></canvas>

    <!--
    <div each="{year, y in submissions_daily}">
        <h3>{y}</h3>
        <table>
            <tr>
                <th each="{month, month_name in year}">{month_name}</th>
            </tr>
            <tr>
                <td each="{month, month_name in year}">{month.average_submissions_per_day}</th>
            </tr>
        </table>
    </div>
    -->


    <h2>User Data</h2>

    <table>
        <tr>
            <th>Users</th>
        </tr>
        <tr>
            <td>{users_total}</td>
        </tr>
    </table>

    <canvas id="user_chart"></canvas>

    <!--
    <div each="{year, y in users_monthly}">
        <h3>{y}</h3>
        <table>
            <tr>
                <th each="{month_count, month in year}">{month}</th>
            </tr>
            <tr>
                <td each="{month_count, month in year}">{month_count}</th>
            </tr>
        </table>
    </div>
    -->

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []

        var competitionsChart;
        var submissionsChart;
        var usersChart;

        self.one("mount", function () {
            console.log("analytics mounted")
            // Make semantic elements work
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()

            $('.date-picker').datepicker();

            // init
            start_date = {
                year: 2010,
                month: 0
            }

            var ctx_c = document.getElementById('competition_chart').getContext('2d');
            competitionsChart = new Chart(ctx_c, create_chart_config('# of Competitions'));
            var ctx_s = document.getElementById('submission_chart').getContext('2d');
            submissionsChart = new Chart(ctx_s, create_chart_config('# of Submissions'));
            var ctx_u = document.getElementById('user_chart').getContext('2d');
            usersChart = new Chart(ctx_u, create_chart_config('# of Users Joined'));

            self.update_analytics(start_date, null)

        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        function create_chart_config(label) {
            return {
                type: 'line',
                data: {
                    datasets: [{
                        label: label,
                        data: null,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor:'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }],
                },
                options: {
                    scales: {
                        xAxes: [{
                            type: 'time',
                            time: {
                                unit: 'month'
                            }
                        }],
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    }
                }
            }
        }

        function update_competitions_chart(competition_data) {
            var competition_chart_data = []

            for (var year in competition_data) {
                if(!competition_data.hasOwnProperty(year)) continue;

                var year_obj = competition_data[year]
                for(var month in year_obj) {
                    if(!year_obj.hasOwnProperty(month)) continue;

                    competition_chart_data.push({
                        x: new Date(year, month - 1),
                        y: year_obj[month]
                    })
                }
            }
            competitionsChart.data.datasets[0].data = competition_chart_data
            competitionsChart.update()
        }

        function update_submissions_chart(submission_data) {
            var submission_chart_data = []

            for (var year in submission_data) {
                if(!submission_data.hasOwnProperty(year)) continue;

                var year_obj = submission_data[year]
                for(var month in year_obj) {
                    if(!year_obj.hasOwnProperty(month)) continue;

                    //var month_obj = year_obj[month]
                    //for(var day in month_obj) {
                    //    if(!month_obj.hasOwnProperty(day)) continue;

                        submission_chart_data.push({
                            x: new Date(year, month - 1),
                            y: year_obj[month].total
                        })
                    //}
                }
            }
            console.log('Submission data length')
            console.log(submission_chart_data.length)
            submissionsChart.data.datasets[0].data = submission_chart_data
            submissionsChart.update()
        }

        function update_users_chart(user_data) {
            var user_chart_data = []

            for (var year in user_data) {
                if(!user_data.hasOwnProperty(year)) continue;

                var year_obj = user_data[year]
                for(var month in year_obj) {
                    if(!year_obj.hasOwnProperty(month)) continue;

                    user_chart_data.push({
                        x: new Date(year, month - 1),
                        y: year_obj[month]
                    })
                }
            }
            usersChart.data.datasets[0].data = user_chart_data
            usersChart.update()
        }


        self.update_analytics= function (start, end) {

            var start_date = new Date(start.year, start.month)
            if (end) {
                var end_date = new Date(end.year, end.month)
            } else {
                var end_date = new Date()
                end_date.setDate(end_date.getDate() + 1)
            }


            console.log(start_date.toJSON().slice(0,10))
            console.log(end_date.toJSON().slice(0,10))

            CODALAB.api.get_analytics(start_date.toJSON().slice(0,10), end_date.toJSON().slice(0,10))
                .done(function (data) {
                    console.log(data)
                    update_competitions_chart(data.monthly_competitions_created)
                    update_submissions_chart(data.daily_submissions_created)
                    update_users_chart(data.monthly_total_users_joined)
                    self.update({
                    users_monthly: data.monthly_total_users_joined,
                    users_total: data.registered_user_count,
                    competitions: data.competition_count,
                    competitions_monthly: data.monthly_competitions_created,
                    competitions_published: data.competitions_published_count,
                    submissions_daily: data.daily_submissions_created,
                    start_date: data.start_date,
                    end_date: data.end_date,
                    })
                })
                .fail(function (response) {
                    toastr.error("Could not load analytics data...")
                })
        }

        $(document).on('click', '#update-data', function() {
            let start = $('#start-date-picker').val().split('/')
            let end = $('#end-date-picker').val().split('/')

            if (start.length == 3) {
                console.log('start exists')
                console.log(start)

                let year = parseInt(start[2])
                let month = parseInt(start[0]) - 1
                console.log(['year', year])
                console.log(['month', month])
                if(month == 0) {
                    console.log('month == 0')
                    var start_date = {
                        year: year - 1,
                        month: 12,
                    }
                } else {
                    console.log('month != 0')
                    var start_date = {
                        year: year,
                        month: month,
                    }
                }

                if (end.length == 3) {
                    console.log('end exists')

                    var end_date = {
                        year: parseInt(end[2]),
                        month: parseInt(end[0]),
                    }
                } else {
                    var end_date = null;
                }
                console.log(['start_date', start_date])
                console.log(['end_date',end_date])
                self.update_analytics(start_date, end_date)
            }
        });


    </script>
    <style>
        th {
            border-bottom: 2px solid grey;
        }

        table {
            margin-bottom: 50px;
            width: 1000px;
        }

        h1, h2 {
            margin-bottom: 20px;
            margin-top: 120px;
        }

        canvas {
            height: 500px;
        }

        .date-selection {
            display: flex;
            align-items: start;
            flex-direction: column
        }
        .date-pickers {
            display: flex;
        }

        .date-pickers p {
            margin-right: 15px;
        }

        .date-submit {
            margin-top: 15px;
        }

        .date-submit button {
            border-radius: 3px;
            margin-top: 200px;
            height: 35px;
        }

        .black-bg {
            background: #000;
        }
    </style>

</analytics>
