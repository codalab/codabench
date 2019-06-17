<analytics>
    <h1>Analytics</h1>


    <h3>Date Range</h3>
    <div class="ui blue buttons" ref="shortcut_buttons">
        <button class="ui button" onclick="{ time_range_shortcut }" id="this-week">This Week</button>
        <button class="ui button" onclick="{ time_range_shortcut }" id="this-month">This Month</button>
        <button class="ui button" onclick="{ time_range_shortcut }" id="this-year">This Year</button>
        <button class="ui button" onclick="{ show_date_selectors }" ref="custom_date">Custom</button>
    </div>

    <div class='hidden date-selection' ref="date_selection_container">
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
                    <input type="text" placeholder="{ end_date}">
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
        <a class="active item" data-tab="competitions">Competitions</a>
        <a class="item" data-tab="submissions">Submissions</a>
        <a class="item" data-tab="users">Users</a>
    </div>

        <div class="ui bottom attached active tab segment" data-tab="competitions">
            <div class="ui statistics">
                <div class="statistic">
                    <div class="value">
                        {competitions}
                    </div>
                    <div class="label">
                        Competitions Created
                    </div>
                </div>
                <div class="statistic">
                    <div class="value">
                        {competitions_published}
                    </div>
                    <div class="label">
                        Competitions Published
                    </div>
                </div>
            </div>
            <div class='chart-container'>
                <canvas ref="competition_chart"></canvas>
            </div>
        </div>

        <div class="ui bottom attached tab segment" data-tab="submissions">
            <div class="ui statistic">
                <div class="value">
                    {submissions_made}
                </div>
                <div class="label">
                    Submissions Made
                </div>
            </div>
            <div class='chart-container'>
                <canvas ref="submission_chart"></canvas>
            </div>
        </div>

        <div class="ui bottom attached tab segment" data-tab="users">
            <div class="ui statistic">
                <div class="value">
                    {users_total}
                </div>
                <div class="label">
                    Users Joined
                </div>
            </div>
            <div class='chart-container'>
                <canvas ref="user_chart"></canvas>
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

        self.start_date = {
            year: 2018,
            month:8,
            day: 1,
        }

        var today = new Date()
        self.end_date = {
            year: today.getFullYear(),
            month: today.getMonth() + 1,
            day: today.getDate(),
        }

        self.convert_datestring_to_object = function (s, back_adjust) {
            let date = s.split('-')
            let year = date[0]
            let month = date[1]
            let day = date[2]

            let new_date = {}

            if(month === 0 && back_adjust) {
                new_date = {
                    year: year - 1,
                    month: 12,
                    day: day,
                }
            } else {
                new_date = {
                    year: year,
                    month: month - 1,
                    day: day,
                }
            }

            return new_date
        }

        self.one("mount", function () {
            // Semantic UI
            $('.tabular.menu .item', self.root).tab();

            // Calendar date-pickers
            $(document).on('click', function(e) {
                if (self.refs.shortcut_buttons.contains(e.target) && e.target !== self.refs.custom_date) {
                    $(self.refs.date_selection_container).addClass('hidden')
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
                        self.start_date = {
                            year: year - 1,
                            month: 12,
                            day: 1,
                        }
                    } else {
                        self.start_date = {
                            year: year,
                            month: month,
                            day: 1,
                        }
                    }

                    self.update_analytics(self.start_date, self.end_date, self.time_unit, false)
                },
            }

            end_specific_options = {
                startCalendar: $(self.refs.start_calendar),
                onChange: function(date, text) {

                    let year = date.getFullYear()
                    let month = date.getMonth() + 1
                    let day = date.getDate()
                    self.end_date = {
                        year: year,
                        month: month,
                        day: day,
                    }

                    self.update_analytics(self.start_date, self.end_date, self.time_unit, false)
                },
            }

            start_calendar_options = _.assign({}, general_calendar_options, start_specific_options)
            end_calendar_options = _.assign({}, general_calendar_options, end_specific_options)

            $(self.refs.start_calendar).calendar(start_calendar_options);
            $(self.refs.end_calendar).calendar(end_calendar_options);

            /*---------------------------------------------------------------------
             Chart Setup
            ---------------------------------------------------------------------*/

            var ctx_c = self.refs.competition_chart.getContext('2d');
            self.competitionsChart = new Chart(ctx_c, create_chart_config('# of Competitions'));
            var ctx_s = self.refs.submission_chart.getContext('2d');
            self.submissionsChart = new Chart(ctx_s, create_chart_config('# of Submissions'));
            var ctx_u = self.refs.user_chart.getContext('2d');
            self.usersChart = new Chart(ctx_u, create_chart_config('# of Users Joined'));

            self.update_analytics(self.start_date, null, self.time_unit, false)

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
                        borderWidth: 1,
                        lineTension: 0,
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
                                beginAtZero: true,
                                stepSize: 1,
                            }
                        }]
                    }
                }
            }
        }

        function build_chart_data(data, day_resolution, csv_format) {
            var chart_data = []

            for( let i = 0; i < data.length; i++ ) {
                let point = {}
                point.x = new Date(data[i]._datefield)
                point.x.setDate(point.x.getDate() + 1)
                point.y = data[i].count
                chart_data.push(point)
            }
            chart_data.sort(function(a,b) {
                return a.x - b.x
            })
            return chart_data
         }

        function update_chart(chart, data, day_resolution) {
            chart.data.datasets[0].data = build_chart_data(data, day_resolution, false)
            chart.update()
        }

        self.update_analytics = function (start, end, time_unit, csv) {

            if (typeof start == 'string') {
                start = self.convert_datestring_to_object(start, true)
            }

            if (typeof end == 'string') {
                end = self.convert_datestring_to_object(end, false)
            }

            var start_date_param = new Date(start.year, start.month, start.day)
            if (end) {
                var end_date_param = new Date(end.year, end.month, end.day)
            } else {
                var end_date_param = new Date(_.now() + 86400000)
            }

            let date_parameters = {
                start_date: start_date_param.toJSON().slice(0,10),
                end_date: end_date_param.toJSON().slice(0,10),
                time_unit: time_unit,
            }

            if(csv) {
                CODALAB.api.get_analytics_csv(date_parameters)
                    .done(function (data) {
//                        let csv_data = self.format_data_to_csv(data)
                        self.download('codalab_analytics.csv', data)
                    })
                    .fail(function (a, b, c) {
                        toastr.error("Could not load analytics data...")
                    })
            } else {
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
                            submissions_made: data.submissions_made_count,
                        })
                    })
                    .fail(function (a, b, c) {
                        toastr.error("Could not load analytics data...")
                    })
            }
        }


        // Shortcut buttons
        self.time_range_shortcut = function(e) {
            let id = e.target.id
            var unit_selection = id.split('-')[1]

            self.end_date = {
                year: new Date().getFullYear(),
                month: new Date().getMonth() + 1,
                day: new Date().getDate(),
            }

            if (unit_selection === 'month') {
                self.start_date = {
                    year: new Date().getFullYear(),
                    month: new Date().getMonth() + 1,
                    day: 1,
                }
            } else if (unit_selection === 'week') {
                var start = new Date()
                start.setDate(start.getDate() - 6)
                self.start_date = {

                    year: start.getFullYear(),
                    month: start.getMonth() + 1,
                    day: start.getDate(),
                }
            } else if (unit_selection === 'year') {
                self.start_date = {
                    year: new Date().getFullYear(),
                    month: 0,
                    day: 1,
                }
            }

            self.update_analytics(self.start_date, self.end_date, 'day', false)

            if (unit_selection != 'year') {
                $(self.refs.day_units).click()
            } else {
                $(self.refs.month_units).click()
            }
        }

        self.show_date_selectors = function (e) {
            $(self.refs.date_selection_container).removeClass('hidden')
        }

        // Chart Units (Months, Weeks, Days)
        self.update_chart_resolution = function(e) {
            let id = e.target.id
            var unit_selection = id.split('-')[0]

            if( unit_selection === 'day') {
                self.time_unit = 'day'
            } else if (unit_selection === 'week') {
                self.time_unit = 'week'
            } else {
                self.time_unit = 'month'
            }


            self.competitionsChart.options.scales.xAxes[0].time.unit = unit_selection
            self.submissionsChart.options.scales.xAxes[0].time.unit = unit_selection
            self.usersChart.options.scales.xAxes[0].time.unit = unit_selection
            self.competitionsChart.update()
            self.submissionsChart.update()
            self.usersChart.update()

            self.update_analytics(self.start_date, self.end_date, self.time_unit, false)
        }

        self.download = function (filename, text) {
            var element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
            element.setAttribute('download', filename);

            element.style.display = 'none';
            document.body.appendChild(element);

            element.click();

            document.body.removeChild(element);
        }

        self.format_data_to_csv = function (data) {
            let all_text = ''
            _.forOwn(data, function(value, key) {
                all_text += key + '\n'
                if (Array.isArray(value)) {
                    all_text += array_to_text(value)
                } else {
                    all_text += value
                }
                all_text += '\n'
            })
            return all_text
        }

        function array_to_text(arr) {
            x_string = ""
            y_string = ""
            _(arr).forEach(function (element) {
                x_string += element.x
                x_string += ', '
                y_string += element.y
                y_string += ', '
            })
            x_string += '\n'
            y_string += '\n'
            return x_string += y_string
        }

        self.download_analytics_data = function(e) {
            let csv = true
            self.update_analytics(self.start_date, self.end_date, self.time_unit, csv)
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
            height: 500px !important;
            width: 1000px !important;
        }

        .hidden {
             display: none !important;
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
