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
    </div>

    <h3>Shortcut Date Ranges</h3>
    <div class='ui button-group'>
        <div class='grouped-button shortcut-button' id='this-week'>
            <h6>This Week</h6>
        </div>
        <div class='grouped-button shortcut-button' id='this-month'>
            <h6>This Month</h6>
        </div>
        <div class='grouped-button last-grouped-button shortcut-button' id='this-year'>
            <h6>This Year</h6>
        </div>
    </div>

    <h3>Chart Resolution</h3>
    <div class='ui button-group'>
        <div class='grouped-button selected-grouped-button chart-resolution-button'id='month-units'>
            <h6>Month</h6>
        </div>
        <div class='grouped-button chart-resolution-button' id='week-units'>
            <h6>Week</h6>
        </div>
        <div class='grouped-button last-grouped-button chart-resolution-button' id='day-units'>
            <h6>Day</h6>
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

    <div class='data-tab-container'>
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

    <div id='download-analytics-data'>
        <h3 class='download-button'>Download</h3>
    </div>

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
        var g_time_unit = 'month';

        var g_competitions_data;
        var g_submissions_data;
        var g_users_data;

        var start_date = {
            year: 2018,
            month:8,
            day: 1,
        }

        var today = new Date()
        var end_date = {
            year: today.getFullYear(),
            month: today.getMonth() + 1,
            day: today.getDate(),
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
                            day: 1,
                        }
                    } else {
                        console.log('month != 0')
                        start_date = {
                            year: year,
                            month: month,
                            day: 1,
                        }
                    }

                    console.log(['start_date', start_date])
                    console.log(['end_date',end_date])
                    self.update_analytics(start_date, end_date, g_time_unit)
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
                    let day = date.getDate()
                    console.log(['year', year])
                    console.log(['month', month])
                    end_date = {
                        year: year,
                        month: month,
                        day: day,
                    }

                    console.log(['start_date', start_date])
                    console.log(['end_date',end_date])
                    self.update_analytics(start_date, end_date, g_time_unit)
                },
                formatter: formatter,
            });


            var ctx_c = document.getElementById('competition_chart').getContext('2d');
            competitionsChart = new Chart(ctx_c, create_chart_config('# of Competitions'));
            var ctx_s = document.getElementById('submission_chart').getContext('2d');
            submissionsChart = new Chart(ctx_s, create_chart_config('# of Submissions'));
            var ctx_u = document.getElementById('user_chart').getContext('2d');
            usersChart = new Chart(ctx_u, create_chart_config('# of Users Joined'));

            self.update_analytics(start_date, null, g_time_unit)

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
                                unit: 'week'
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

        function build_chart_data(data, day_resolution, csv_format) {
            var chart_data = []
            var x_data = []
            var y_data = []

            for (var year in data) {
                if(!data.hasOwnProperty(year)) continue;

                var year_obj = data[year]
                for(var month in year_obj) {
                    if(!year_obj.hasOwnProperty(month)) continue;

                    if(day_resolution) {
                        var month_obj = data[year][month]
                        for(var day in month_obj) {
                            if(!month_obj.hasOwnProperty(day)) continue;

                            if (year_obj[month][day].total == undefined) {
                                console.log('undefined date')
                                console.log(year_obj[month])
                                console.log(day)
                            }
                            if (csv_format) {
                                x_data.push(new Date(year, month - 1, day).toJSON().slice(0,10))
                                y_data.push(year_obj[month][day].total)
                            } else {
                                chart_data.push({
                                    x: new Date(year, month - 1, day),
                                    y: year_obj[month][day].total
                                })
                            }
                        }
                    } else {
                        if (csv_format) {
                                x_data.push(new Date(year, month - 1).toJSON().slice(0,10))
                                y_data.push(year_obj[month].total)
                        } else {
                            chart_data.push({
                                x: new Date(year, month - 1),
                                y: year_obj[month].total
                            })
                        }
                    }
                }
            }
            if (csv_format) {
                let d = {
                    x: x_data,
                    y: y_data,
                }
                return d
            } else {
                return chart_data
            }
         }

        function update_chart(chart, data, day_resolution) {
            chart.data.datasets[0].data = build_chart_data(data, day_resolution, false)
            chart.update()
        }

        self.update_analytics= function (start, end, time_unit) {

            var start_date = new Date(start.year, start.month, start.day)
            if (end) {
                var end_date = new Date(end.year, end.month, end.day)
            } else {
                var end_date = new Date()
                end_date.setDate(end_date.getDate() + 1)
            }


            console.log(start_date.toJSON().slice(0,10))
            console.log(end_date.toJSON().slice(0,10))

            CODALAB.api.get_analytics(start_date.toJSON().slice(0,10), end_date.toJSON().slice(0,10), time_unit)
                .done(function (data) {
                    console.log(data)
                    let time_unit = data.time_unit == 'day'
                    update_chart(competitionsChart, data.competitions_data, time_unit)
                    update_chart(submissionsChart, data.submissions_data, time_unit)
                    update_chart(usersChart, data.users_data, time_unit)

                    g_competitions_data = data.competitions_data
                    g_submissions_data = data.submissions_data
                    g_users_data = data.users_data

                    self.update({
                    users_total: data.registered_user_count,
                    competitions: data.competition_count,
                    competitions_published: data.competitions_published_count,
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

        // Shortcut buttons
        $(document).on('click','.shortcut-button', function(e) {
            $('.shortcut-button').removeClass('selected-grouped-button')
            if ($(e.target).prop('tagName') == 'H6') {
                var id = $(e.target).parent().attr('id')
            } else {
                var id = $(e.target).attr('id')
            }
            var unit_selection = id.split('-')[1]
            $('#' + id).addClass('selected-grouped-button')

            end_date = {
                year: new Date().getFullYear(),
                month: new Date().getMonth() + 1,
                day: new Date().getDate(),
            }

            if (unit_selection == 'month') {
                start_date = {
                    year: new Date().getFullYear(),
                    month: new Date().getMonth() + 1,
                    day: 1,
                }
            } else if (unit_selection == 'week') {
                var start = new Date()
                start.setDate(start.getDate() - 6)
                start_date = {

                    year: start.getFullYear(),
                    month: start.getMonth() + 1,
                    day: start.getDate(),
                }
            } else if (unit_selection == 'year') {
                start_date = {
                    year: new Date().getFullYear(),
                    month: 0,
                    day: 1,
                }
            }

            console.log(start_date)

            self.update_analytics(start_date, end_date, 'day')

            if (unit_selection != 'year') {
                $('#day-units').click()
            } else {
                $('#month-units').click()
            }
        })

        // Chart Unit Scale
        $(document).on('click','.chart-resolution-button', function(e) {
            $('.chart-resolution-button').removeClass('selected-grouped-button')
            if ($(e.target).prop('tagName') == 'H6') {
                var id = $(e.target).parent().attr('id')
            } else {
                var id = $(e.target).attr('id')
            }
            var unit_selection = id.split('-')[0]
            $('#' + id).addClass('selected-grouped-button')

            if( unit_selection == 'day' || unit_selection == 'week') {
                g_time_unit = 'day'
            } else {
                g_time_unit = 'month'
            }

            competitionsChart.options.scales.xAxes[0].time.unit = unit_selection
            submissionsChart.options.scales.xAxes[0].time.unit = unit_selection
            usersChart.options.scales.xAxes[0].time.unit = unit_selection
            competitionsChart.update()
            submissionsChart.update()
            usersChart.update()

            self.update_analytics(start_date, end_date, g_time_unit)
        })

        function download(filename, text) {
            var element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
            element.setAttribute('download', filename);

            element.style.display = 'none';
            document.body.appendChild(element);

            element.click();

            document.body.removeChild(element);
        }

        function create_csv_data(data) {
            let day_resolution = g_time_unit != 'month'
            console.log(['day_resolution', day_resolution])
            let d = build_chart_data(data, day_resolution, true)

            let x_text = array_to_text(d.x)
            let y_text = array_to_text(d.y)
            let all_text = x_text + y_text

            return all_text
        }

        function array_to_text(arr) {
            return arr.join(', ') + '\n'
        }

        $(document).on('click','#download-analytics-data', function(e) {
            console.log('downloading csv')
            let competitions_text = create_csv_data(g_competitions_data)
            let submissions_text = create_csv_data(g_submissions_data)
            let users_text = create_csv_data(g_users_data)

            let file_text = 'competitions\n' + competitions_text
            file_text += '\nsubmissions\n' + submissions_text
            file_text += '\nusers\n' + users_text

            console.log(file_text)
            download('codalab_analytics.csv', file_text)
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
            margin-top: 80px;
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

        .data-tab-container {
            height: 800px;
        }

        .data-tab {
            display: none;
        }

        .ui-datepicker {
            width: 500px;
        }

        .button-group {
            display: flex;
            align-items: stretch;
            overflow: hidden;
            border-radius: 4px;
            border: solid 1px #ddd;
            width: 40%;
            margin-bottom: 30px;
        }

        .grouped-button {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-grow: 1;
            border-right: solid 1px #ddd;
            text-align: center;
            padding: 10px;
            height: 35px;
        }

        .grouped-button h6 {
            margin: 0;
        }

        .grouped-button:hover {
            color: #666;
        }

        .last-grouped-button {
            border-right: none;
        }

        .selected-grouped-button {
            background: #eee;
        }

        #download-analytics-data {
            display: flex;
            align-items: center;
            justify-content: center;
            border: solid 1px #ddd;
            padding: 15px;
            width: 15%;
            margin-top: 30px;
        }

        .download-button {
            margin: none;
        }

        #download-analytics-data:hover {
            color: #666;
        }

    </style>

</analytics>
