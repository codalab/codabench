<analytics>
    <h1>Analytics</h1>

    <div class='date-selection'>
        <div class="ui calendar" id="start-calendar">
            <div class="ui input left icon">
                <i class="calendar icon"></i>
                <input type="text" placeholder="{ start_date }">
            </div>
        </div>
        <div class="ui calendar" id="end-calendar">
            <div class="ui input left icon">
                <i class="calendar icon"></i>
                <input type="text" placeholder="{end_date}">
            </div>
        </div>
        <div class='ui chart-unit-scale'>
            <div class='chart-unit-scale-button selected-chart-unit-scale-button' id='month-units'>
                <h6>Month</h6>
            </div>
            <div class='chart-unit-scale-button' id='week-units'>
                <h6>Week</h6>
            </div>
            <div class='chart-unit-scale-button last-chart-unit-scale-button' id='day-units'>
                <h6>Day</h6>
            </div>
        </div>
    </div>

    <div class='tab-buttons'>
        <div class='spacer-button'></div>
        <div id='competitions-button' class='tab-button selected-tab-button'>
            <h4>Competitions</h4>
        </div>
        <div id='submissions-button' class='tab-button'>
            <h4>Submissions</h4>
        </div>
        <div id='users-button' class='tab-button last-tab-button'>
            <h4>Users</h4>
        </div>
        <div class='spacer-button'></div>
    </div>

    <div id='competitions-data' class='data-tab' style='display: block;'>
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
    </div>

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

    <div id='submissions-data' class='data-tab'>
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

    </div>

    <div id='users-data' class='data-tab'>
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
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []

        var competitionsChart;
        var submissionsChart;
        var usersChart;

        var start_date = {
            year: 2018,
            month:8
        }

        var today = new Date()
        var end_date = {
            year: today.getFullYear(),
            month: today.getMonth() + 1,
        }

        self.one("mount", function () {
            console.log("analytics mounted")
            // Make semantic elements work
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()


            formatter = {
                date: function (date, settings) {
                    if (!date) return '';
                    var day = date.getDate();
                    var month = date.getMonth() + 1;
                    var year = date.getFullYear();
                    return year + '-' + month + '-' + day;
                }
            }
            $('#start-calendar').calendar({
                type: 'date',
                endCalendar: $('#end-calendar'),
                onChange: function(date, text) {
                    console.log(date)

                    let year = date.getFullYear()
                    let month = date.getMonth()
                    console.log(['year', year])
                    console.log(['month', month])
                    if(month == 0) {
                        console.log('month == 0')
                        start_date = {
                            year: year - 1,
                            month: 12,
                        }
                    } else {
                        console.log('month != 0')
                        start_date = {
                            year: year,
                            month: month,
                        }
                    }

                    console.log(['start_date', start_date])
                    console.log(['end_date',end_date])
                    self.update_analytics(start_date, end_date)
                },
                formatter: formatter,
            });

            $('#end-calendar').calendar({
                type: 'date',
                startCalendar: $('#start-calendar'),
                onChange: function(date, text) {
                    console.log(date)

                    let year = date.getFullYear()
                    let month = date.getMonth() + 1
                    console.log(['year', year])
                    console.log(['month', month])
                    end_date = {
                        year: year,
                        month: month,
                    }

                    console.log(['start_date', start_date])
                    console.log(['end_date',end_date])
                    self.update_analytics(start_date, end_date)
                },
                formatter: formatter,
            });


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

                        submission_chart_data.push({
                            x: new Date(year, month - 1),
                            y: year_obj[month].total
                        })
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

        // Tabs
        $(document).on('click','.tab-button', function(e) {
            $('.data-tab').css('display', 'none')
            $('.tab-button').removeClass('selected-tab-button')
            if ($(e.target).prop('tagName') == 'H4') {
                var id = $(e.target).parent().attr('id')
            } else {
                var id = $(e.target).attr('id')
            }
            var data_selection = id.split('-')[0]
            $('#' + id).addClass('selected-tab-button')
            $('#' + data_selection + '-data').css('display', 'block')
        })

        // Chart Unit Scale
        $(document).on('click','.chart-unit-scale-button', function(e) {
            $('.data-tab').css('display', 'none')
            $('.chart-unit-scale-button').removeClass('selected-chart-unit-scale-button')
            if ($(e.target).prop('tagName') == 'H6') {
                var id = $(e.target).parent().attr('id')
            } else {
                var id = $(e.target).attr('id')
            }
            var unit_selection = id.split('-')[0]
            $('#' + id).addClass('selected-chart-unit-scale-button')

            console.log(competitionsChart)
            competitionsChart.options.scales.xAxes[0].time.unit = unit_selection
            competitionsChart.update()
            submissionsChart.options.scales.xAxes[0].time.unit = unit_selection
            submissionsChart.update()
            usersChart.options.scales.xAxes[0].time.unit = unit_selection
            usersChart.update()
        })
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
            margin-top: 30px;
        }

        canvas {
            height: 500px;
        }

        .date-selection {
            display: flex;
            justify-content: start;
            flex-direction: row;
            width: 1000px;
            margin: 40px 0 70px 0;
        }

        .calendar {
            margin-right: 40px;
        }

        .black-bg {
            background: #000;
        }

        .tab-buttons {
            display: flex;
            justify-content: stretch;
            align-items: center;
            width: 100%;
            height: 65px;
            margin-top: 20px;
        }

        .tab-button {
            display: flex;
            align-items: center;
            justify-content: center;
            border: solid 1px #ddd;
            border-right: none;
            background: #fff;
            height: 100%;
            width: 150px;
        }

        .spacer-button {
            flex-grow: 1;
            height: 100%;
            border-bottom: solid 1px #ddd;
        }

        .tab-button:hover {
            color: #666;
        }

        .selected-tab-button{
            border-bottom: none;
            background: #eee;
        }

        .last-tab-button {
            border-right: solid 1px #ddd;
        }

        .data-tab {
            display: none;
        }

        .ui-datepicker {
            width: 500px;
        }

        .chart-unit-scale {
            display: flex;
            overflow: hidden;
            border-radius: 4px;
            border: solid 1px #ddd;
        }

        .chart-unit-scale-button {
            display: flex;
            align-items: center;
            justify-content: center;
            border-right: solid 1px #ddd;
            text-align: center;
            padding: 10px;
            height: 35px;
        }

        .chart-unit-scale-button h6 {
            margin: 0;
        }

        .chart-unit-scale-button:hover {
            color: #666;
        }

        .last-chart-unit-scale-button {
            border-right: none;
        }

        .selected-chart-unit-scale-button {
            background: #eee;
        }
    </style>

</analytics>
