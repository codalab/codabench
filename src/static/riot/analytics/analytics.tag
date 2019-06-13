<analytics>
    <h1>Analytics</h1>


    <h3>Date Range</h3>
    <div class="ui blue buttons">
        <button class="ui button" onclick="{ time_range_shortcut }" id="this-week">This Week</button>
        <button class="ui button" onclick="{ time_range_shortcut }" id="this-month">This Month</button>
        <button class="ui button" onclick="{ time_range_shortcut }" id="this-year">This Year</button>
        <button class="ui button" onclick="{ show_date_selectors }" ref="custom_date">Custom</button>
    </div>

    <div class='date-selection' ref="date_selection_container" style="display: none;">
        <div class="start-date-input date-input">
            <h3>Start Date</h3>
            <div class="ui calendar" ref="start_calendar">
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" placeholder="{ start_date }">
                </div>
            </div>
        </div>
        <div class="date-input">
            <h3>End Date</h3>
            <div class="ui calendar" ref="end_calendar">
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" placeholder="{end_date}">
                </div>
            </div>
        </div>
    </div>

    </div>

    <h3>Chart Resolution</h3>
    <div class="ui blue buttons">
        <button class="ui button" onclick="{ update_chart_resolution }" id="day-units">Daily</button>
        <button class="ui button" onclick="{ update_chart_resolution }" id="week-units">Weekly</button>
        <button class="ui button" onclick="{ update_chart_resolution }" id="month-units">Monthly</button>
    </div>


    <div class="ui top attached tabular menu">
        <a class="item" data-tab="competitions">competitions</a>
        <a class="item" data-tab="submissions">submissions</a>
        <a class="active item" data-tab="users">users</a>
    </div>

        <div class="ui bottom attached tab segment" data-tab="competitions">

            <h2>Competition Data</h2>

            <table>
                <thead>
                    <tr>
                        <th>Competitions</th>
                        <th>Published Competitions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{competitions}</td>
                        <td>{competitions_published}</td>
                    </tr>
                </tbody>
            </table>

            <div class='chart-container'>
                <canvas id="competition_chart"></canvas>
            </div>
        </div>

        <div class="ui bottom attached tab segment" data-tab="submissions">
            <h2>Submission Data</h2>

            <div class='chart-container'>
                <canvas id="submission_chart"></canvas>
            </div>
        </div>

        <div class="ui bottom attached active tab segment" data-tab="users">
            <h2>User Data</h2>

            <table>
                <thead>
                    <tr>
                        <th>Users</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{users_total}</td>
                    </tr>
                </tbody>
            </table>

            <div class='chart-container'>
                <canvas id="user_chart"></canvas>
            </div>
        </div>

        <button class="ui big blue button" onclick="{ download_analytics_data }">Download</button>
    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []

        self.competitionsChart;
        self.submissionsChart;
        self.usersChart;
        self.time_unit = 'month';

        self.competitions_data;
        self.submissions_data;
        self.users_data;

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
            // Semantic UI
            $('.tabular.menu .item').tab();

            // Calendar date-pickers
            $(document).on('click', function(e) {
                console.log(e.target)
                console.log(self.refs.date_selection_container)
                if (!self.refs.date_selection_container.contains(e.target) && e.target !== self.refs.custom_date) {
                    $(self.refs.date_selection_container).css('display','none')
                }
            })

            /*---------------------------------------------------------------------
             Calendar Setup
            ---------------------------------------------------------------------*/

            general_calendar_options = {
                type: 'date',
                // Sets the format of the placeholder date string to YYYY-MM-DD
                formatter: {
                   date: function (date, settings) {
                       if (!date) return '';
                       var day = date.getDate();
                       var month = date.getMonth() + 1;
                       var year = date.getFullYear();
                       return year + '-' + month + '-' + day;
                   }
                },
            }

            start_specific_options = {
                endCalendar: $(self.refs.end_calendar),
                onChange: function(date, text) {

                    let year = date.getFullYear()
                    let month = date.getMonth()
                    if(month === 0) {
                        start_date = {
                            year: year - 1,
                            month: 12,
                            day: 1,
                        }
                    } else {
                        start_date = {
                            year: year,
                            month: month,
                            day: 1,
                        }
                    }
                    self.update_analytics(start_date, end_date, self.time_unit)
                },
            }

            end_specific_options = {
                startCalendar: $(self.refs.start_calendar),
                onChange: function(date, text) {

                    let year = date.getFullYear()
                    let month = date.getMonth() + 1
                    let day = date.getDate()
                    end_date = {
                        year: year,
                        month: month,
                        day: day,
                    }

                    self.update_analytics(start_date, end_date, self.time_unit)
                },
            }

            start_calendar_options = _.assign({}, general_calendar_options, start_specific_options)
            end_calendar_options = _.assign({}, general_calendar_options, end_specific_options)

            $(self.refs.start_calendar).calendar(start_calendar_options);
            $(self.refs.end_calendar).calendar(end_calendar_options);

            /*---------------------------------------------------------------------
             Chart Setup
            ---------------------------------------------------------------------*/

            var ctx_c = document.getElementById('competition_chart').getContext('2d');
            self.competitionsChart = new Chart(ctx_c, create_chart_config('# of Competitions'));
            var ctx_s = document.getElementById('submission_chart').getContext('2d');
            self.submissionsChart = new Chart(ctx_s, create_chart_config('# of Submissions'));
            var ctx_u = document.getElementById('user_chart').getContext('2d');
            self.usersChart = new Chart(ctx_u, create_chart_config('# of Users Joined'));

            self.update_analytics(start_date, null, self.time_unit)

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

                            if (year_obj[month][day].total === undefined) {
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

        self.update_analytics = function (start, end, time_unit) {

            var start_date = new Date(start.year, start.month, start.day)
            if (end) {
                var end_date = new Date(end.year, end.month, end.day)
            } else {
                var end_date = new Date()
                end_date.setDate(end_date.getDate() + 1)
            }

            let date_parameters = {
                start_date: start_date.toJSON().slice(0,10),
                end_date: end_date.toJSON().slice(0,10),
                time_unit: time_unit,
            }

            CODALAB.api.get_analytics(date_parameters)
                .done(function (data) {
                    let time_unit = data.time_unit === 'day'

                    update_chart(self.competitionsChart, data.competitions_data, time_unit)
                    update_chart(self.submissionsChart, data.submissions_data, time_unit)
                    update_chart(self.usersChart, data.users_data, time_unit)

                    self.competitions_data = data.competitions_data
                    self.submissions_data = data.submissions_data
                    self.users_data = data.users_data

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


        // Shortcut buttons
        self.time_range_shortcut = function(e) {
            let id = e.target.id
            var unit_selection = id.split('-')[1]

            end_date = {
                year: new Date().getFullYear(),
                month: new Date().getMonth() + 1,
                day: new Date().getDate(),
            }

            if (unit_selection === 'month') {
                start_date = {
                    year: new Date().getFullYear(),
                    month: new Date().getMonth() + 1,
                    day: 1,
                }
            } else if (unit_selection === 'week') {
                var start = new Date()
                start.setDate(start.getDate() - 6)
                start_date = {

                    year: start.getFullYear(),
                    month: start.getMonth() + 1,
                    day: start.getDate(),
                }
            } else if (unit_selection === 'year') {
                start_date = {
                    year: new Date().getFullYear(),
                    month: 0,
                    day: 1,
                }
            }

            self.update_analytics(start_date, end_date, 'day')

            if (unit_selection != 'year') {
                $('#day-units').click()
            } else {
                $('#month-units').click()
            }
        }

        self.show_date_selectors = function (e) {
            $(self.refs.date_selection_container).css('display','flex')
        }

        // Chart Units (Months, Weeks, Days)
        self.update_chart_resolution = function(e) {
            let id = e.target.id
            var unit_selection = id.split('-')[0]
            console.log(unit_selection)

            if( unit_selection === 'day' || unit_selection === 'week') {
                self.time_unit = 'day'
            } else {
                self.time_unit = 'month'
            }

            self.competitionsChart.options.scales.xAxes[0].time.unit = unit_selection
            self.submissionsChart.options.scales.xAxes[0].time.unit = unit_selection
            self.usersChart.options.scales.xAxes[0].time.unit = unit_selection
            self.competitionsChart.update()
            self.submissionsChart.update()
            self.usersChart.update()

            self.update_analytics(start_date, end_date, self.time_unit)
        }

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
            let day_resolution = self.time_unit != 'month'
            let d = build_chart_data(data, day_resolution, true)

            let x_text = array_to_text(d.x)
            let y_text = array_to_text(d.y)
            let all_text = x_text + y_text

            return all_text
        }

        function array_to_text(arr) {
            return arr.join(', ') + '\n'
        }

        self.download_analytics_data = function(e) {
            let competitions_text = create_csv_data(self.competitions_data)
            let submissions_text = create_csv_data(self.submissions_data)
            let users_text = create_csv_data(self.users_data)

            let file_text = 'competitions\n' + competitions_text
            file_text += '\nsubmissions\n' + submissions_text
            file_text += '\nusers\n' + users_text

            download('codalab_analytics.csv', file_text)
        }



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

        h3 {
            margin-bottom: 8px;
        }

        canvas {
            height: 500px;
        }

        .date-input {
            display: flex;
            flex-direction: column;
        }

        .start-date-input {
            margin-right: 40px;
        }

        .date-selection {
            display: flex;
            justify-content: space-between;
            flex-direction: row;
            background: #eee;
            margin-top: 30px;
            border-radius: 4px;
            padding: 10px;
            width: fit-content;
        }


        .chart-container {
            min-height: 450px;
        }
    </style>
</analytics>
