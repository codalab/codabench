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
                <canvas class="big" ref="competition_chart"></canvas>
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
                <canvas class="big" ref="submission_chart"></canvas>
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
                <canvas class="big" ref="user_chart"></canvas>
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
            <div class="delete-oprhans-container">
                <button class="ui red button { disabled: delete_orphans_button_modal_disabled }" onclick="{showConfirmationModal}">
                    <i class="icon { warning: !delete_orphans_button_modal_loading}"></i>
                    {delete_orphans_button_modal_text}
                </button>
            </div>
        </div>

        <div class="ui bottom attached tab segment" data-tab="usage-history">
            <analytics-storage-usage-history start_date={start_date_string} end_date={end_date_string} resolution={time_unit} is_visible={current_view=="usage-history"}></analytics-storage-usage-history>
        </div>

        <div class="ui bottom attached tab segment" data-tab="competitions-usage">
            <analytics-storage-competitions-usage start_date={start_date_string} end_date={end_date_string} resolution={time_unit} is_visible={current_view=="competitions-usage"}></analytics-storage-competitions-usage>
        </div>

        <div class="ui bottom attached tab segment" data-tab="users-usage">
            <analytics-storage-users-usage start_date={start_date_string} end_date={end_date_string} resolution={time_unit} is_visible={current_view=="users-usage"}></analytics-storage-users-usage>
        </div>

        <!--  Orphan Deletion Modal  -->
        <div ref="confirmation_modal" class="ui small modal">
        <div class="header">
            Delete orphan files
        </div>
        <div class="content">
            <h4>You are about to delete {nb_orphan_files} orphan files.</h4>
            <h5><i>Note: The number of orphan files displayed is based on the most recent storage inconsistency analytics. Its value will be updated during the next storage analytics task.</i></h5>
            <h3>This operation is irreversible!</h3>
            <h3>Do you want to proceed ?</h3>
        </div>
        <div class="actions">
            <button class="ui icon button {delete_button_color} { disabled: delete_button_disabled }" onclick="{deleteOrphanFiles}">
                <i if={delete_button_color=="green"} class="check icon"></i>
                {delete_button_text}
            </button>
            <button class="ui cancel button">Close</button>
        </div>
    </div>

    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.current_view = "overview";
        self.currentAnalyticsTab = "overview";
        self.currentStorageTab = "usageHistory";
        self.isDataReloadNeeded = {
            "overview": true,
            "storage": {
                "usageHistory": true,
                "competitionsUsage": true,
                "usersUsage": true,
            }
        };

        self.time_unit = 'month';
        let datetime = luxon.DateTime;
        self.start_date = datetime.local(datetime.local().year);
        self.end_date = datetime.local();
        self.start_date_string = self.start_date.toISODate();
        self.end_date_string = self.end_date.toISODate();

        self.colors = ["#36a2eb", "#ff6384", "#4bc0c0", "#ff9f40", "#9966ff", "#ffcd56", "#c9cbcf"];

        /****** Overview *****/
        self.competitionsChart;
        self.submissionsChart;
        self.usersChart;

        self.competitions_data;
        self.submissions_data;
        self.users_data;

        /****** Storage *****/

        self.nb_orphan_files = 0
        self.delete_button_color = "red"
        self.delete_button_loading = false
        self.delete_button_disabled = false
        self.delete_button_text = "Yes, delete all orphan files"

        self.delete_orphans_button_modal_text = "Delete orphan files"
        self.delete_orphans_button_modal_loading = false
        self.delete_orphans_button_modal_disabled = false
        self.pollingInterval;

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
                    self.start_date_string = self.start_date.toISODate();
                    self.update({start_date_string: self.start_date_string});
                    let end_date = $(self.refs.end_calendar).calendar('get date')

                    if (!!end_date && date > end_date) {
                        $(self.refs.end_calendar).calendar('set date', date, true, true);
                        toastr.error("Start date must be before end date.");
                    } else {
                        self.isDataReloadNeeded["overview"] = true;
                        Object.keys(self.isDataReloadNeeded["storage"]).forEach(v => self.isDataReloadNeeded["storage"][v] = true);
                        if (self.currentAnalyticsTab == "overview") {
                            self.update_analytics(self.start_date, self.end_date, self.time_unit);
                        }
                    }
                }
            };

            let end_specific_options = {
                startCalendar: $(self.refs.start_calendar),
                onChange: function(date, text) {
                    if (date) {
                        self.end_date = datetime.fromJSDate(date)
                        self.end_date_string = self.end_date.toISODate();
                        self.update({end_date_string: self.end_date_string});
                    }

                    self.isDataReloadNeeded["overview"] = true;
                    Object.keys(self.isDataReloadNeeded["storage"]).forEach(v => self.isDataReloadNeeded["storage"][v] = true);
                    if (self.currentAnalyticsTab == "overview") {
                        self.update_analytics(self.start_date, self.end_date, self.time_unit);
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
             Initialization
            ---------------------------------------------------------------------*/

            self.update_analytics(self.start_date, null, self.time_unit);
            self.time_range_shortcut("month");
            self.update_chart_resolution("day");
            self.getOrphanFiles();
            self.startCheckOrphansDeletionStatus();
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
                    });

                    self.isDataReloadNeeded["overview"] = false;
                })
                .fail(function (a, b, c) {
                    toastr.error("Could not load analytics data...")
                })
        }

        self.onAnalyticsTabChange = function (tabName) {
            self.currentAnalyticsTab = tabName;
            if (tabName == "overview") {
                self.current_view = self.currentAnalyticsTab;
                self.update({current_view: self.currentAnalyticsTab});
            } else if (tabName == "storage") {
                self.current_view = self.currentStorageTab;
                self.update({current_view: self.currentStorageTab});
            }

            if (tabName == "overview" && self.isDataReloadNeeded["overview"]) {
                self.update_analytics(self.start_date, self.end_date, self.time_unit);
            }
        };

        self.onStorageTabChange = function(tabName) {
            self.currentStorageTab = tabName;
            if (self.current_view != "overview") {
                self.current_view = self.currentStorageTab;
                self.update({current_view: self.currentStorageTab});
            }
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

            self.start_date_string = self.start_date.toISODate();
            self.end_date_string = self.end_date.toISODate();

            if (unit_selection !== 'year') {
                self.resolution_dropdown.dropdown('set selected', 'day');
            } else {
                self.time_unit = 'month';
                self.resolution_dropdown.dropdown('set selected', 'month');
            }

            self.update({start_date_string: self.start_date_string, end_date_string: self.end_date_string, time_unit: self.time_unit});

            self.isDataReloadNeeded["overview"] = true;
            Object.keys(self.isDataReloadNeeded["storage"]).forEach(v => self.isDataReloadNeeded["storage"][v] = true);

            if (self.currentAnalyticsTab == "overview") {
                self.update_analytics(self.start_date, self.end_date, self.time_unit);
            }
        }

        // Chart Units (Months, Weeks, Days)
        self.update_chart_resolution = function(unit_selection) {
            self.time_unit = unit_selection;
            self.update({time_unit: self.time_unit});
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
            }
            self.update();
        }

        self.pretty_date = function (date_string) {
            if (!!date_string) {
                return luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL)
            } else {
                return ''
            }
        }

        // Orhpan related
        self.showConfirmationModal = function() {
            $(self.refs.confirmation_modal).modal('show');
            self.delete_button_color = "red";
            self.delete_button_loading = false;
            self.delete_button_disabled = false;
            self.delete_button_text = "Yes, delete all orphan files";
            self.update();
        }

        self.checkOrphansDeletionStatus = function() {
            CODALAB.api.check_orphans_deletion_status()
                .done(function(data) {
                    if (data.status) {
                        if (data.status == "SUCCESS") {
                            toastr.success("Orphan files deletion successful")
                            self.delete_button_color = "green";
                            self.delete_button_text = "Deletion Successful";
                        }
                        if (data.status == "FAILURE") {
                            toastr.error("Orphan files deletion failed")
                            self.delete_button_color = "red";
                            self.delete_button_text = "Deletion Failed";
                        }
                        if (data.status == "REVOKED") {
                            toastr.error("Orphan files deletion has been canceled")
                            self.delete_button_color = "red";
                            self.delete_button_text = "Deletion canceled";
                        }
                        if (data.status == "SUCCESS" || data.status == "FAILURE" || data.status == "REVOKED") {
                            // Task is over
                            self.stopCheckOrphansDeletionStatus();
                            self.delete_orphans_button_modal_text = "Delete orphan files";
                            self.delete_orphans_button_modal_loading = false;
                            self.delete_orphans_button_modal_disabled = false;
                            self.delete_button_loading = false;
                            self.delete_button_disabled = true;
                        } else {
                            // Task is running
                            self.delete_orphans_button_modal_text = "Orphan files deletion in progress...";
                            self.delete_orphans_button_modal_disabled = true;
                            self.delete_orphans_button_modal_loading = true;

                            self.delete_button_text = "Orphan files deletion in progress...";
                            self.delete_button_disabled = true;
                            self.delete_button_loading = true;
                        }
                    } else {
                        // No task running
                        self.stopCheckOrphansDeletionStatus();

                        self.delete_orphans_button_modal_text = "Delete orphan files";
                        self.delete_orphans_button_modal_disabled = false;
                        self.delete_orphans_button_modal_loading = false;

                        self.delete_button_color = "red";
                        self.delete_button_loading = false;
                        self.delete_button_disabled = false;
                        self.delete_button_text = "Yes, delete all orphan files";
                    }
                    
                })
                .fail(function(response) {
                    toastr.error("Orphan files deletion's task status check failed")
                    self.delete_orphans_button_modal_text = "Delete orphan files";
                    self.delete_orphans_button_modal_loading = false;
                    self.delete_orphans_button_modal_disabled = false;

                    self.delete_button_text = "Yes, delete all orphan files";
                    self.delete_button_color = "red";
                    self.delete_button_loading = false;
                    self.delete_button_disabled = false;

                    self.stopCheckOrphansDeletionStatus();
                })
                .always(function() {
                    self.update();
                })
        }

        self.startCheckOrphansDeletionStatus = function () {
            self.pollingInterval = setInterval(self.checkOrphansDeletionStatus, 2000);
        }

        self.stopCheckOrphansDeletionStatus = function() {
            if (self.pollingInterval) {
                clearInterval(self.pollingInterval);
                self.pollingInterval = null;
            }
        }

        self.deleteOrphanFiles = function() {
            self.delete_button_loading = true
            self.delete_button_disabled = true
            self.delete_orphans_button_modal_loading = true;
            self.delete_orphans_button_modal_disabled = true;
            self.delete_button_text = "Orphan files deletion in progress...";
            self.delete_orphans_button_modal_text = "Orphan files deletion in progress...";
            self.update()
            CODALAB.api.delete_orphan_files()
                .done(function (data) {
                    if (data && data.success && !self.pollingInterval) {
                        self.startCheckOrphansDeletionStatus();
                    }
                })
                .fail(function (response) {
                    toastr.error("Orphan files deletion failed to start")
                })
                .always(function () {
                    self.delete_button_loading = false
                    self.update()
                });
        }

        self.getOrphanFiles = function() {
            CODALAB.api.get_orphan_files()
                .done(function (data) {
                    self.nb_orphan_files = data.data.length
                    self.update({nb_orphan_files: self.nb_orphan_files});
                })
                .fail(function (response) {
                    toastr.error("Get oprhan files failed, error occurred")
                });
        }

    </script>
    <style>
        analytics {
            width: 100%;
        }

        .ui.inverted.bluewood.menu {
            background-color: #2C3F4C
        }

        h1 {
            margin-bottom: 20px;
            margin-top: 30px;
        }

        h3 {
            margin-bottom: 8px;
        }

        canvas.big {
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

        .delete-oprhans-container {
            margin-bottom: 5px;
            margin-left: auto;
        }
    </style>
</analytics>
