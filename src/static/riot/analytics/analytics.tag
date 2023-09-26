<analytics>
    <h1>Analytics</h1>

    <div class="ui top no-segment bluewood inverted two column item menu analytics">
        <a class="active item" data-tab="overview">Overview</a>
        <a class="item" data-tab="storage">Storage</a>
    </div>

    <div class="ui grid">
        <div class="four wide column">
            <h3>Date Range</h3>

            <div class="ui selection dropdown" ref="date_shortcut_dropdown">
                <input type="hidden" name="range_shortcut" value="month">
                <i class="dropdown icon"></i>
                <div class="text">This Month</div>
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

        <div class=" hidden four wide column" ref="start_date_selection_container">
            <h3>Start Date</h3>

            <div class="ui calendar" ref="start_calendar">
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" placeholder="{ start_date_string }">
                </div>
            </div>
        </div>

        <div class="hidden four wide column" ref="end_date_selection_container">
            <h3>End Date</h3>

            <div class="ui calendar" ref="end_calendar">
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" placeholder="{ end_date_string }">
                </div>
            </div>
        </div>
    </div>

    <div class="ui active tab segment" data-tab="overview">
        <div class="ui top attached tabular menu">
            <a class="active item" data-tab="competitions">Benchmarks</a>
            <a class="item" data-tab="submissions">Submissions</a>
            <a class="item" data-tab="users">Users</a>
        </div>

        <div class="ui bottom attached active tab segment" data-tab="competitions">
            <div class="ui small statistic">
                <div class="value">
                    {competitions}
                </div>
                <div class="label">
                    Benchmarks Created
                </div>
            </div>

            <div class="ui small statistic">
                <div class="value">
                    {competitions_published}
                </div>
                <div class="label">
                    Benchmarks Published
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
    </div>

    <div class="ui tab segment storage" data-tab="storage">
        <div class="ui top attached tabular menu">
            <a class="item" data-tab="usage-history">Usage history</a>
            <a class="item" data-tab="competitions-usage">Competitions usage</a>
            <a class="item" data-tab="users-usage">Users usage</a>
            <a class="item" data-tab="admin-usage">Administration usage</a>
        </div>

        <div class="ui bottom attached tab segment" data-tab="usage-history">
            <div class='chart-container'>
                <canvas ref="storage_usage_history_chart"></canvas>
            </div>
        </div>

        <div class="ui bottom attached tab segment" data-tab="competitions-usage">
            <select class="ui search multiple selection dropdown" multiple ref="competitions_dropdown">
                <i class="dropdown icon"></i>
                <div class="default text">Select Competitions</div>
                <div class="menu">
                    <option each="{ competition in competitionsDropdownOptions }" value="{ competition.id }">{ competition.title }</div> 
                </div>
            </select>
            <button class="ui button" onclick={selectTopFiveBiggestCompetitions}>Select top 5 biggest competitions</button>
            <div class='chart-container'>
                <canvas ref="storage_competitions_usage_chart"></canvas>
            </div>
            <div class="ui calendar" ref="table_date_calendar">
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text">
                </div>
            </div>
            <div class='chart-container'>
                <canvas ref="storage_competitions_usage_pie"></canvas>
            </div>
            <table id="storageCompetitionsTable" class="ui selectable sortable celled table">
                <thead>
                    <tr>
                        <th is="su-th" field="title">Competition</th>
                        <th is="su-th" field="organizer">Organizer</th>
                        <th is="su-th" field="created_when">Creation date</th>
                        <th is="su-th" field="datasets">Datasets</th>
                    </tr>
                </thead>
                <tbody>
                    <tr each="{ competitionUsage in competitionsUsageTableData }">
                        <td><a href="{ URLS.COMPETITION_DETAIL(competitionUsage.id) }">{ competitionUsage.title }</a></td>
                        <td>{ competitionUsage.organizer }</td>
                        <td>{ competitionUsage.created_when }</td>
                        <td>{ competitionUsage.datasets }</td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr>
                        <su-pagination total-page="10" />
                    </tr>
                </tfoot>
            </table>
        </div>

        <div class="ui bottom attached tab segment" data-tab="users-usage">
            <h3>TODO</h3>
        </div>

        <div class="ui bottom attached tab segment" data-tab="admin-usage">
            <h3>TODO</h3>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/

        self.currentAnalyticsTab = "overview";
        self.currentStorageTab = "usageHistory";
        self.isDataReloadNeeded = {
            "overview": true,
            "storage": {
                "usageHistory": true,
                "competitionsUsage": true,
                "usersUsage": true,
                "adminUsage": true
            }
        };

        self.time_unit = 'month';
        let datetime = luxon.DateTime;
        self.start_date = datetime.local(datetime.local().year);
        self.end_date = datetime.local();

        self.colors = ["#36a2eb", "#ff6384", "#4bc0c0", "#ff9f40", "#9966ff", "#ffcd56", "#c9cbcf"];

        /****** Overview *****/
        self.competitionsChart;
        self.submissionsChart;
        self.usersChart;

        self.competitions_data;
        self.submissions_data;
        self.users_data;

        /****** Storage *****/

        // Usage history
        self.storageUsageHistoryData = null;
        self.competitionsUsageData = null;
        self.usersUsageData = null;
        self.adminUsageData = null;
        self.storageUsageChart;

        // Competitions usage
        self.competitionsDropdownOptions = [];
        self.storageCompetitionsUsageChart;
        self.storageCompetitionsUsagePieChart;
        self.competitionsUsageTableData = [];
        self.competitionsColor = {};

        // Users usage

        // Admin usage

        self.one("mount", function () {
            // Semantic UI
            $('.tabular.menu .item', self.root).tab();
            $('.no-segment.menu .item', self.root).tab();

            self.shortcut_dropdown = $(self.refs.date_shortcut_dropdown);
            self.resolution_dropdown = $(self.refs.chart_resolution_dropdown);
            self.shortcut_dropdown.dropdown({
                onChange: function(value, text, item) {
                    if (value === 'custom') {
                        $(self.refs.start_date_selection_container).removeClass('hidden')
                        $(self.refs.end_date_selection_container).removeClass('hidden')
                    } else {
                        $(self.refs.start_date_selection_container).addClass('hidden')
                        $(self.refs.end_date_selection_container).addClass('hidden')
                        self.time_range_shortcut(value)
                    }
                }
            });
            self.resolution_dropdown.dropdown({
                onChange: function(value, text, item) {
                    self.update_chart_resolution(value)
                }
            });

            /*---------------------------------------------------------------------
             Calendar Setup
            ---------------------------------------------------------------------*/

            let general_calendar_options = {
                type: 'date',
                // Sets the format of the placeholder date string to YYYY-MM-DD
                formatter: {
                   date: function (date, settings) {
                       return datetime.fromJSDate(date).toISODate();
                   }
                },
            };

            let start_specific_options = {
                endCalendar: $(self.refs.end_calendar),
                onChange: function(date, text) {
                    self.start_date = datetime.fromJSDate(date)
                    let end_date = $(self.refs.end_calendar).calendar('get date')

                    if (!!end_date && date > end_date) {
                        $(self.refs.end_calendar).calendar('set date', date, true, true);
                        toastr.error("Start date must be before end date.");
                    } else {
                        self.isDataReloadNeeded["overview"] = true;
                        Object.keys(self.isDataReloadNeeded["storage"]).forEach(v => self.isDataReloadNeeded["storage"][v] = true);
                        if (self.currentAnalyticsTab == "overview") {
                            self.update_analytics(self.start_date, self.end_date, self.time_unit);
                        } else {
                            if (self.currentStorageTab == "usage-history") {
                                self.get_storage_usage_history(self.start_date, self.end_date, self.time_unit);
                            } else if (self.currentStorageTab == "competitions-usage") {
                                self.get_competitions_usage(self.start_date, self.end_date, self.time_unit);
                            } else if (self.currentStorageTab == "users-usage") {
                                console.log("TODO");
                            } else if (self.currentStorageTab == "admin-usage") {
                                console.log("TODO");
                            }
                        }
                    }
                }
            };

            let end_specific_options = {
                startCalendar: $(self.refs.start_calendar),
                onChange: function(date, text) {
                    if (date) {
                        self.end_date = datetime.fromJSDate(date)
                    }

                    self.isDataReloadNeeded["overview"] = true;
                    Object.keys(self.isDataReloadNeeded["storage"]).forEach(v => self.isDataReloadNeeded["storage"][v] = true);
                    if (self.currentAnalyticsTab == "overview") {
                        self.update_analytics(self.start_date, self.end_date, self.time_unit);
                    } else {
                        if (self.currentStorageTab == "usage-history") {
                            self.get_storage_usage_history(self.start_date, self.end_date, self.time_unit);
                        } else if (self.currentStorageTab == "competitions-usage") {
                            self.get_competitions_usage(self.start_date, self.end_date, self.time_unit);
                        } else if (self.currentStorageTab == "users-usage") {
                            console.log("TODO");
                        } else if (self.currentStorageTab == "admin-usage") {
                            console.log("TODO");
                        }
                    }
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

            /*---------------------------------------------------------------------
             Tabs
            ---------------------------------------------------------------------*/

            $('.top.menu.analytics .item').tab({'onVisible': this.onAnalyticsTabChange});
            $('.storage .top.menu .item').tab({'onVisible': this.onStorageTabChange});

            // Default selected tabs
            $('.top.menu.analytics .item').tab('change tab', 'overview');
            $('.storage .top.menu .item').tab('change tab', 'usage-history');

            /*---------------------------------------------------------------------
             Storage Usage History Chart Setup
            ---------------------------------------------------------------------*/
            let storageUsageConfig = {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Total usage',
                            data: [],
                            borderColor: 'rgb(255, 99, 132)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Competitions usage',
                            data: [],
                            borderColor: 'rgb(255, 164, 74)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Users usage',
                            data: [],
                            borderColor: 'rgb(54, 162, 235)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Administration usage',
                            data: [],
                            borderColor: 'rgb(153, 102, 255)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Orphaned files usage',
                            data: [],
                            borderColor: 'rgb(228, 229, 231)',
                            borderWidth: 1,
                            lineTension: 0
                        }
                    ],
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    },
                    scales: {
                        xAxes: [{
                            type: 'time',
                            ticks: {
                                source: 'auto'
                            }
                        }],
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                stepSize: 'auto',
                                callback: function(value, index, values) {
                                    return pretty_bytes(value);
                                }
                            }
                        }]
                    },
                    tooltips: {
                        mode: 'index',
                        intersect: false,
                        position: 'nearest',
                        callbacks: {
                            label: function(tooltipItem, data) {
                                return pretty_bytes(tooltipItem.yLabel);
                            }
                        }
                    }
                }
            };
            self.storageUsageChart = new Chart($(self.refs.storage_usage_history_chart), storageUsageConfig);

            /*---------------------------------------------------------------------
             Competition usage
            ---------------------------------------------------------------------*/

            // Sementic UI components setups
            self.selectedCompetitions = [];
            $(self.refs.competitions_dropdown).dropdown({
                onAdd: self.addCompetitionToSelection,
                onRemove: self.removeCompetitionFromSelection,
                clearable: true,
                preserveHTML: false,
                
            });
            $('#storageCompetitionsTable').tablesort();
            self.tableSelectedDate = null;
            let table_date_specific_options = {
                onChange: function(date, text) {
                    self.tableSelectedDate = date;
                    self.updateCompetitionsTable();
                    self.updateCompetitionsChart();
                    self.updateCompetitionsPieChart();
                }
            };
            let table_date_calendar_options = _.assign({}, general_calendar_options, table_date_specific_options);
            $(self.refs.table_date_calendar).calendar(table_date_calendar_options);

            /*---------------------------------------------------------------------
             Competitions Usage Chart Setup
            ---------------------------------------------------------------------*/

            let storageCompetitionsUsageConfig = {
                type: 'line',
                data: {
                    datasets: [],
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    },
                    scales: {
                        xAxes: [{
                            type: 'time',
                            ticks: {
                                source: 'auto'
                            }
                        }],
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                stepSize: 'auto',
                                callback: function(value, index, values) {
                                    return pretty_bytes(value);
                                }
                            }
                        }]
                    },
                    tooltips: {
                        mode: 'index',
                        intersect: false,
                        position: 'nearest',
                        callbacks: {
                            label: function(tooltipItem, data) {
                                return pretty_bytes(tooltipItem.yLabel);
                            }
                        }
                    }
                }
            };

            self.storageCompetitionsUsageChart = new Chart($(self.refs.storage_competitions_usage_chart), storageCompetitionsUsageConfig);

            /*---------------------------------------------------------------------
             Competitions Usage Pie Chart Setup
            ---------------------------------------------------------------------*/

            let storageCompetitionsUsagePieConfig = {
                type: 'pie',
                data: {
                    labels: [],
                    competitionsId: [],
                    datasets: [
                        {
                            label: 'Competitions distribution',
                            backgroundColor: [],
                            hoverOffset: 4,
                            data: []
                        }
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'left',
                        },
                        title: {
                            display: true,
                            text: 'Competitions distribution'
                        }
                    },
                    tooltips: {
                        callbacks: {
                            label: function(tooltipItem, data) {
                                const label = data.labels[tooltipItem.index];
                                const value = pretty_bytes(data.datasets[0].data[tooltipItem.index]);
                                return " " + label + ": " + value;
                            }
                        }
                    }
                }
            };

            self.storageCompetitionsUsagePieChart = new Chart($(self.refs.storage_competitions_usage_pie), storageCompetitionsUsagePieConfig);

            /*---------------------------------------------------------------------
             Initialization
            ---------------------------------------------------------------------*/

            self.update_analytics(self.start_date, null, self.time_unit);
            self.time_range_shortcut("month");
            self.update_chart_resolution("day");
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

        self.update_storage_usage_history_chart = function(data) {
            var list_usages = {};
            for (let [date, usages] of Object.entries(data)) {
                for (let [usage_label, usage] of Object.entries(usages)) {
                    if (!list_usages.hasOwnProperty(usage_label)) {
                        list_usages[usage_label] = [];
                    }
                    list_usages[usage_label].push({x: new Date(date), y: usage * 1024});
                }
            }
            for (const [index, usage_label] of Object.entries(Object.keys(list_usages))) {
                list_usages[usage_label].sort(function(a, b) {return a.x - b.x;});
                self.storageUsageChart.data.datasets[index].data = list_usages[usage_label];
            }
            self.storageUsageChart.update();
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
                    });

                    self.isDataReloadNeeded["overview"] = false;
                })
                .fail(function (a, b, c) {
                    toastr.error("Could not load analytics data...")
                })
        }

        self.onAnalyticsTabChange = function (tabName) {
            self.currentAnalyticsTab = tabName;
            if (tabName == "overview" && self.isDataReloadNeeded["overview"]) {
                self.update_analytics(self.start_date, self.end_date, self.time_unit);
            } else if (tabName == "storage") {
                if (self.currentStorageTab == "usage-history" && self.isDataReloadNeeded["storage"]["usageHistory"]) {
                    self.get_storage_usage_history(self.start_date, self.end_date, self.time_unit);
                } else if (self.currentStorageTab == "competitions-usage" && self.isDataReloadNeeded["storage"]["competitionsUsage"]) {
                    self.get_competitions_usage(self.start_date, self.end_date, self.time_unit);
                } else if (self.currentStorageTab == "users-usage" && self.isDataReloadNeeded["storage"]["usersUsage"]) {
                    console.log("TODO");
                } else if (self.currentStorageTab == "admin-usage" && self.isDataReloadNeeded["storage"]["adminUsage"]) {
                    console.log("TODO");
                }
            }
        };

        self.onStorageTabChange = function(tabName) {
            self.currentStorageTab = tabName;
            if (tabName == "usage-history" && self.isDataReloadNeeded["storage"]["usageHistory"]) {
                self.get_storage_usage_history(self.start_date, self.end_date, self.time_unit);
            } else if (tabName == "competitions-usage" && self.isDataReloadNeeded["storage"]["competitionsUsage"]) {
                self.get_competitions_usage(self.start_date, self.end_date, self.time_unit);
            } else if (tabName == "users-usage" && self.isDataReloadNeeded["storage"]["usersUsage"]) {
                console.log("TODO");
            } else if (tabName == "admin-usage" && self.isDataReloadNeeded["storage"]["adminUsage"]) {
                console.log("TODO");
            }
        }

        self.get_storage_usage_history = function(start_date, end_date, resolution) {
            let parameters = {
                start_date: start_date.toISODate(),
                end_date: end_date.toISODate(),
                resolution: resolution
            };
            CODALAB.api.get_storage_usage_history(parameters)
                .done(function(data) {
                    self.update({storageUsageHistoryData: data});
                    self.update_storage_usage_history_chart(data);
                    self.isDataReloadNeeded["storage"]["usageHistory"] = false;
                })
                .fail(function(error) {
                    toastr.error("Could not load storage analytics data");
                });
        }

        self.get_competitions_usage = function(start_date, end_date, resolution) {
            let parameters = {
                start_date: start_date.toISODate(),
                end_date: end_date.toISODate(),
                resolution: resolution
            };
            CODALAB.api.get_competitions_usage(parameters)
                .done(function(data) {
                    self.competitionsUsageData = data;
                    self.update({competitionsUsageData: data});
                    self.updateCompetitionsSelectionDropdown();
                    self.updateCompetitionTableCalendar(data);
                    self.updateCompetitionsChart();
                    self.updateCompetitionsPieChart();
                    self.updateCompetitionsTable();
                    self.isDataReloadNeeded["storage"]["competitionsUsage"] = false;
                })
                .fail(function(error) {
                    toastr.error("Could not load storage analytics data");
                });
        }

        // Shortcut buttons
        self.time_range_shortcut = function(unit_selection) {
            self.end_date = datetime.local();

            let diffs = {
                month: {months: 1},
                week: {days: 6},
                year: {years: 1},
            }

            self.start_date = self.end_date.minus(diffs[unit_selection]);
            self.shortcut_dropdown.dropdown('set selected', unit_selection);
            self.time_unit = 'day';

            if (unit_selection !== 'year') {
                self.resolution_dropdown.dropdown('set selected', 'day');
            } else {
                self.time_unit = 'month';
                self.resolution_dropdown.dropdown('set selected', 'month');
            }

            self.isDataReloadNeeded["overview"] = true;
            Object.keys(self.isDataReloadNeeded["storage"]).forEach(v => self.isDataReloadNeeded["storage"][v] = true);

            if (self.currentAnalyticsTab == "overview") {
                self.update_analytics(self.start_date, self.end_date, self.time_unit);
            } else {
                if (self.currentStorageTab == "usage-history") {
                    self.get_storage_usage_history(self.start_date, self.end_date, self.time_unit);
                } else if (self.currentStorageTab == "competitions-usage") {
                    self.get_competitions_usage(self.start_date, self.end_date, self.time_unit);
                } else if (self.currentStorageTab == "users-usage") {
                    console.log("TODO");
                } else if (self.currentStorageTab == "admin-usage") {
                    console.log("TODO");
                }
            }
        }

        // Chart Units (Months, Weeks, Days)
        self.update_chart_resolution = function(unit_selection) {
            self.time_unit = unit_selection;
            self.resolution_dropdown.dropdown('set selected', unit_selection);

            self.competitionsChart.options.scales.xAxes[0].time.unit = unit_selection;
            self.submissionsChart.options.scales.xAxes[0].time.unit = unit_selection;
            self.usersChart.options.scales.xAxes[0].time.unit = unit_selection;
            self.competitionsChart.update();
            self.submissionsChart.update();
            self.usersChart.update();

            self.isDataReloadNeeded["overview"] = true;
            Object.keys(self.isDataReloadNeeded["storage"]).forEach(v => self.isDataReloadNeeded["storage"][v] = true);

            if (self.currentAnalyticsTab == "overview") {
                self.update_analytics(self.start_date, self.end_date, self.time_unit);
            } else {
                if (self.currentStorageTab == "usage-history") {
                    self.get_storage_usage_history(self.start_date, self.end_date, self.time_unit);
                } else if (self.currentStorageTab == "competitions-usage") {
                    self.get_competitions_usage(self.start_date, self.end_date, self.time_unit);
                } else if (self.currentStorageTab == "users-usage") {
                    console.log("TODO");
                } else if (self.currentStorageTab == "admin-usage") {
                    console.log("TODO");
                }
            }
            self.update();
        }

        self.addCompetitionToSelection = function(value, text, $addedItem) {
            if(Object.keys(self.competitionsUsageData).length > 0) {
                self.selectedCompetitions.push(value);
                let competitionUsage = [];
                for (let [dateString, competitions] of Object.entries(self.competitionsUsageData)) {
                    for (let [competitionId, competition] of Object.entries(competitions)) {
                        if (competitionId == value) {
                            competitionUsage.push({x: new Date(dateString), y: competition.datasets * 1024});
                        }
                    }
                }
                const competitions = Object.values(self.competitionsUsageData)[0];
                const competitionTitle = competitions[value].title;
                if(!self.competitionsColor.hasOwnProperty(value)) {
                    self.competitionsColor[value] = self.colors[Object.keys(self.competitionsColor).length % self.colors.length];
                }
                const color = self.competitionsColor[value];

                // Update chart
                self.storageCompetitionsUsageChart.data.datasets.push({
                    competitionId: value,
                    label: competitionTitle,
                    data: competitionUsage,
                    backgroundColor: color,
                    borderWidth: 1,
                    lineTension: 0,
                    fill: false
                });
                self.storageCompetitionsUsageChart.update();

                // Update pie chart
                let selectedDate = self.tableSelectedDate;
                if (!selectedDate) {
                    selectedDate = new Date(Object.keys(self.competitionsUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
                }
                const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
                const closestOlderDateString = Object.keys(self.competitionsUsageData).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
                const competitionsAtSelectedDate = self.competitionsUsageData[closestOlderDateString];
                const selectedCompetitions = Object.keys(competitionsAtSelectedDate).filter(date => self.selectedCompetitions.includes(date)).reduce((competition, date) => ({ ...competition, [date]: competitionsAtSelectedDate[date] }), {});
                
                const {labels, competitionsId, data} = self.formatDataForCompetitionsPieChart(selectedCompetitions);
                self.storageCompetitionsUsagePieChart.data.labels = labels;
                self.storageCompetitionsUsagePieChart.data.competitionsId = competitionsId;
                self.storageCompetitionsUsagePieChart.data.datasets[0].data = data;
                self.storageCompetitionsUsagePieChart.data.datasets[0].labels = labels;
                self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor = self.listOfColors(data.length);
                self.storageCompetitionsUsagePieChart.update();
            }
        }

        self.listOfColors = function(arrayLength) {
            return Array.apply(null, Array(arrayLength)).map(function (x, i) { return self.colors[i%self.colors.length]; })
        }

        self.formatDataForCompetitionsPieChart = function (data) {
            var labels = [];
            var competitionsId = [];
            var formattedData = [];

            const competitionArray = Object.entries(data).map(([key, value]) => ({ ...value, id: key }));
            competitionArray.sort((a, b) => b.datasets - a.datasets);
            for (const competition of competitionArray) {
                labels.push(competition.title);
                competitionsId.push(competition.id);
                formattedData.push(competition.datasets * 1024);
            }

            return {labels: labels, competitionsId: competitionsId, data: formattedData};
        }

        self.removeCompetitionFromSelection = function(value, text, $removedItem) {
            // Remove from selection
            const indexToRemoveInSelected = self.selectedCompetitions.findIndex(competitionId => competitionId == value);
            if (indexToRemoveInSelected !== -1) {
                self.selectedCompetitions.splice(indexToRemoveInSelected, 1);
            }

            // Reassign competitions color
            self.competitionsColor = {};
            for(const competitionId of self.selectedCompetitions) {
                self.competitionsColor[competitionId] = self.colors[Object.keys(self.competitionsColor).length % self.colors.length];
            }

            // Remove from competition usage chart
            let indexToRemove = self.storageCompetitionsUsageChart.data.datasets.findIndex(dataset => dataset.competitionId == value);
            if (indexToRemove !== -1) {
                self.storageCompetitionsUsageChart.data.datasets.splice(indexToRemove, 1);
                for(let dataset of self.storageCompetitionsUsageChart.data.datasets) {
                    dataset.backgroundColor = self.competitionsColor[dataset.competitionId]
                }
                self.storageCompetitionsUsageChart.update();
            }

            // Remove from competition pie chart
            indexToRemove = self.storageCompetitionsUsagePieChart.data.competitionsId.findIndex(id => id == value);
            if (indexToRemove !== -1) {
                self.storageCompetitionsUsagePieChart.data.labels.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.competitionsId.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.datasets[0].data.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor = self.storageCompetitionsUsagePieChart.data.competitionsId.map(competitionId => self.competitionsColor[competitionId]);
                self.storageCompetitionsUsagePieChart.update();
            }
        }

        self.updateCompetitionsSelectionDropdown = function () {
            // Remove current selection
            $(self.refs.competitions_dropdown).dropdown('clear');
            
            // Update the options
            let competitionsOptions = [];
            if(Object.keys(self.competitionsUsageData).length > 0) {
                const competitions = Object.values(self.competitionsUsageData)[0];
                competitionsOptions = Object.entries(competitions).map(([id, { title }]) => ({ id, title }));
            }
            self.competitionsDropdownOptions = competitionsOptions;
            $(self.refs.competitions_dropdown).dropdown('change values', competitionsOptions);
            self.update({competitionsDropdownOptions: competitionsOptions});
        }

        self.selectTopFiveBiggestCompetitions = function () {
            let selectCompetitions = [];
            if (Object.keys(self.competitionsUsageData).length > 0) {
                const mostRecentDateString = Object.keys(self.competitionsUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur );
                let competitions = Object.entries(self.competitionsUsageData[mostRecentDateString]);
                competitions.sort((a, b) => b[1].datasets - a[1].datasets);
                selectCompetitions = competitions.slice(0, 5).map(([id]) => id);
            }
            self.selectedCompetitions = selectCompetitions;
            $(self.refs.competitions_dropdown).dropdown('clear');
            for(const competitionId of selectCompetitions) {
                $(self.refs.competitions_dropdown).dropdown('set selected', competitionId);
            }
        }

        self.updateCompetitionTableCalendar = function(data) {
            // Set the min and max date of the calendar
            const minDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) < new Date(cur) ? acc : cur, '9999-12-31'));
            const maxDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur, '0000-00-00'));
            $(self.refs.table_date_calendar).calendar('setting', 'minDate', minDate);
            $(self.refs.table_date_calendar).calendar('setting', 'maxDate', maxDate);

            // Select the most current date available
            self.tableSelectedDate = maxDate;
            $(self.refs.table_date_calendar).calendar('set date', maxDate);
            $(self.refs.table_date_calendar).calendar('refresh');
        }

        self.updateCompetitionsChart = function() {
            if(Object.keys(self.competitionsUsageData).length > 0) {
                const selectedCompetitions = Object.fromEntries(
                    Object.entries(self.competitionsUsageData).map(([dateString, competitions]) => [
                        dateString,
                        Object.fromEntries(
                            Object.entries(competitions).filter(([competitionId]) => self.selectedCompetitions.includes(competitionId))
                        )
                    ])
                );
                
                const competitionsUsage = {};
                for (let [dateString, competitions] of Object.entries(selectedCompetitions)) {
                    for (let [competitionId, competition] of Object.entries(competitions)) {
                        if (!competitionsUsage.hasOwnProperty(competitionId)) {
                            competitionsUsage[competitionId] = [];
                        }
                        competitionsUsage[competitionId].push({x: new Date(dateString), y: competition.datasets * 1024});
                    }
                }

                self.storageCompetitionsUsageChart.data.datasets = [];
                let index = 0;
                for(let [competitionId, dataset] of Object.entries(competitionsUsage)) {
                    const color = self.colors[index % self.colors.length];
                    const title = Object.values(self.competitionsUsageData)[0][competitionId].title;
                    self.storageCompetitionsUsageChart.data.datasets.push({
                        competitionId: competitionId,
                        label: title,
                        data: dataset,
                        backgroundColor: color,
                        borderWidth: 1,
                        lineTension: 0,
                        fill: false
                    });
                    index++;
                }

                self.storageCompetitionsUsageChart.update();
            }
        }

        self.updateCompetitionsPieChart = function() {
            let selectedDate = self.tableSelectedDate;
            if (!selectedDate) {
                selectedDate = new Date(Object.keys(self.competitionsUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
            }
            const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
            const closestOlderDateString = Object.keys(self.competitionsUsageData).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
            const competitionsAtSelectedDate = self.competitionsUsageData[closestOlderDateString];
            const selectedCompetitions = Object.keys(competitionsAtSelectedDate).filter(date => self.selectedCompetitions.includes(date)).reduce((competition, date) => ({ ...competition, [date]: competitionsAtSelectedDate[date] }), {});

            const {labels, competitionsId, data} = self.formatDataForCompetitionsPieChart(selectedCompetitions);
            self.storageCompetitionsUsagePieChart.data.labels = labels;
            self.storageCompetitionsUsagePieChart.data.competitionsId = competitionsId;
            self.storageCompetitionsUsagePieChart.data.datasets[0].data = data;
            self.storageCompetitionsUsagePieChart.data.datasets[0].labels = labels;
            self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor = self.listOfColors(data.length);
            self.storageCompetitionsUsagePieChart.update();
        }

        self.updateCompetitionsTable = function() {
            const data = self.competitionsUsageData;
            let competitionsUsageTableData = [];
            if (Object.keys(data).length > 0) {
                let selectedDate = self.tableSelectedDate;
                if (!selectedDate) {
                    selectedDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
                }
                const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
                const closestOlderDateString = Object.keys(data).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
                const competitions = data[closestOlderDateString];
                Object.entries(competitions).forEach(keyValue => {
                    const [competitionId, competition] = keyValue;
                    competitionsUsageTableData.push({
                        'id': competitionId,
                        'title': competition.title,
                        'organizer': competition.organizer,
                        'created_when': new Date(competition.created_when).toDateString(),
                        'datasets': pretty_bytes(competition.datasets * 1024)
                    });
                });
                self.update({competitionsUsageTableData: competitionsUsageTableData});
            }
        }

    </script>
    <style>
        analytics {
            width: 100%;
        }

        .ui.inverted.bluewood.menu {
            background-color: #2C3F4C
        }

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
