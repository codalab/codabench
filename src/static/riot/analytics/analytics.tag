<analytics>
    <h1>Analytics</h1>

    <div class="ui grid">
        <div class="four wide column">
            <h3>Date Range</h3>

            <div class="ui selection dropdown" ref="date_shortcut_dropdown">
                <input type="hidden" name="range_shortcut">
                <i class="dropdown icon"></i>
                <div class="default text">This Year</div>
                <div class="menu">
                    <div class="item" data-value="year">This Year</div>
                    <div class="item" data-value="month">This Month</div>
                    <div class="item" data-value="week">This Week</div>
                    <div class="item" data-value="custom">Custom</div>
                </div>
            </div>
        </div>

        <div class="four wide column">
            <h3>Chart Resolution</h3>

            <div class="ui selection dropdown" ref="chart_resolution_dropdown">
                <input type="hidden" name="resolution">
                <i class="dropdown icon"></i>
                <div class="default text">Month</div>
                <div class="menu">
                    <div class="item" data-value="month">Month</div>
                    <div class="item" data-value="week">Week</div>
                    <div class="item" data-value="day">Day</div>
                </div>
            </div>
        </div>
    </div>

    <div class='hidden date-selection' ref="date_selection_container">
        <div class="start-date-input date-input">
            <h3>Start Date</h3>
            <div class="ui calendar" ref="start_calendar">
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" placeholder="{ start_date_string }">
                </div>
            </div>
        </div>
        <div class="date-input">
            <h3>End Date</h3>
            <div class="ui calendar" ref="end_calendar">
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" placeholder="{ end_date_string }">
                </div>
            </div>
        </div>
    </div>


    <div class="ui top attached tabular menu">
        <a class="active item" data-tab="competitions">Competitions</a>
        <a class="item" data-tab="submissions">Submissions</a>
        <a class="item" data-tab="users">Users</a>
    </div>

    <div class="ui bottom attached active tab segment" data-tab="competitions">
        <div class="ui small statistic">
            <div class="value">
                {competitions}
            </div>
            <div class="label">
                Competitions Created
            </div>
        </div>

        <div class="ui small statistic">
            <div class="value">
                {competitions_published}
            </div>
            <div class="label">
                Competitions Published
            </div>
        </div>

        <div class='chart-container'>
            <canvas ref="competition_chart"></canvas>
        </div>
    </div>

    <div class="ui bottom attached tab segment" data-tab="submissions">
        <div class="ui small statistic">
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
        <div class="ui small statistic">
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

    <a class="ui green button" href="{ URLS.ANALYTICS_API({start_date: start_date_string, end_date: end_date_string, time_unit: time_unit, format: 'csv'}) }" download="codalab_analytics.csv">
        <i class="icon download"></i>Download as CSV
    </a>

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

        let datetime = luxon.DateTime
        self.start_date = datetime.local(datetime.local().year)
        self.end_date = datetime.local()

        self.one("mount", function () {
            // Semantic UI
            $('.tabular.menu .item', self.root).tab();

            self.shortcut_dropdown = $(self.refs.date_shortcut_dropdown)
            self.resolution_dropdown = $(self.refs.chart_resolution_dropdown)
            self.shortcut_dropdown.dropdown({
                onChange: function(value, text, item) {
                    if (value === 'custom') {
                        $(self.refs.date_selection_container).removeClass('hidden')
                        self.resolution_dropdown.dropdown('set selected', 'day')
                    } else {
                        $(self.refs.date_selection_container).addClass('hidden')
                        self.time_range_shortcut(value)
                    }
                }
            })

            self.resolution_dropdown.dropdown({
                onChange: function(value, text, item) {
                    self.update_chart_resolution(value)
                }
            })

            /*---------------------------------------------------------------------
             Calendar Setup
            ---------------------------------------------------------------------*/

            let general_calendar_options = {
                type: 'date',
                // Sets the format of the placeholder date string to YYYY-MM-DD
                formatter: {
                   date: function (date, settings) {
                       return datetime.fromJSDate(date).toISODate()
                   }
                },
            }

            let start_specific_options = {
                endCalendar: $(self.refs.end_calendar),
                onChange: function(date, text) {
                    self.start_date = datetime.fromJSDate(date)

                    let end_date = $(self.refs.end_calendar).calendar('get date')
                    if (!!end_date) {
                        if (date <= end_date) {
                            self.update_analytics(self.start_date, self.end_date, self.time_unit)
                        } else {
                            $(self.refs.end_calendar).calendar('set date', date, true, true);
                            toastr.error("Start date must be before end date.")
                        }
                    } else {
                        self.update_analytics(self.start_date, self.end_date, self.time_unit)
                    }
                },
            }

            let end_specific_options = {
                startCalendar: $(self.refs.start_calendar),
                onChange: function(date, text) {
                    if (date) {
                        self.end_date = datetime.fromJSDate(date)
                    }

                    self.update_analytics(self.start_date, self.end_date, self.time_unit)
                },
            }

            let start_calendar_options = _.assign({}, general_calendar_options, start_specific_options)
            let end_calendar_options = _.assign({}, general_calendar_options, end_specific_options)

            $(self.refs.start_calendar).calendar(start_calendar_options);
            $(self.refs.end_calendar).calendar(end_calendar_options);

            /*---------------------------------------------------------------------
             Chart Setup
            ---------------------------------------------------------------------*/

            self.competitionsChart = new Chart($(self.refs.competition_chart), create_chart_config('# of Competitions'));
            self.submissionsChart = new Chart($(self.refs.submission_chart), create_chart_config('# of Submissions'));
            self.usersChart = new Chart($(self.refs.user_chart), create_chart_config('# of Users Joined'));

            self.update_analytics(self.start_date, null, self.time_unit)

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
            let chart_data = _.map(data, data_point => {
                let d = new Date(data_point._datefield)
                d.setDate(d.getDate() + 1)

                return {
                    x: d,
                    y: data_point.count,
                }
            })

            chart_data.sort(function(a,b) {
                return a.x - b.x
            })

            return chart_data
         }

        function update_chart(chart, data, day_resolution) {
            chart.data.datasets[0].data = build_chart_data(data, day_resolution, false)
            chart.update()
        }

        self.update_analytics = function (start, end, time_unit) {
            if (!end) {
                end = datetime.local()
            }

            // Django's __range is exclusive of the end date, so it must be incremented by one day to include it.
            let date_parameters = {
                start_date: start.toISODate(),
                end_date: end.plus({day: 1}).toISODate(),
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
                        start_date_string: data.start_date,
                        end_date_string: data.end_date,
                        submissions_made: data.submissions_made_count,
                    })
                })
                .fail(function (a, b, c) {
                    toastr.error("Could not load analytics data...")
                })
        }


        // Shortcut buttons
        self.time_range_shortcut = function(unit_selection) {
            self.end_date = datetime.local()

            let diffs = {
                month: {months: 1},
                week: {days: 6},
                year: {years: 1},
            }

            self.start_date = self.end_date.minus(diffs[unit_selection])

            self.update_analytics(self.start_date, self.end_date, 'day')

            if (unit_selection !== 'year') {
                self.resolution_dropdown.dropdown('set selected', 'day')
                self.update_analytics(self.start_date, self.end_date, 'day')
            } else {
                self.resolution_dropdown.dropdown('set selected', 'month')
                self.update_analytics(self.start_date, self.end_date, 'month')
            }
        }

        // Chart Units (Months, Weeks, Days)
        self.update_chart_resolution = function(unit_selection) {
            self.time_unit = unit_selection

            self.competitionsChart.options.scales.xAxes[0].time.unit = unit_selection
            self.submissionsChart.options.scales.xAxes[0].time.unit = unit_selection
            self.usersChart.options.scales.xAxes[0].time.unit = unit_selection
            self.competitionsChart.update()
            self.submissionsChart.update()
            self.usersChart.update()

            self.update_analytics(self.start_date, self.end_date, self.time_unit)
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
