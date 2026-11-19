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
            <a class="item" data-tab="orphan-files">Orphan files</a>
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

        <div class="ui bottom attached tab segment" data-tab="orphan-files">
            <h3>Orphan files scanner</h3>

            <p>
                Scan managed storage objects and identify files without
                database references. This operation does not delete files.
            </p>

            <div class="ui form">
                <div class="two fields">
                    <div class="field">
                        <label>Grace period</label>
                        <input
                            type="number"
                            min="0"
                            max="3650"
                            step="1"
                            value={orphan_grace_period}
                            oninput={onOrphanGracePeriodChange}
                            disabled={orphan_scan_running}
                        >
                    </div>

                    <div class="field">
                        <label>Unit</label>
                        <select
                            class="ui dropdown"
                            onchange={onOrphanGraceUnitChange}
                            disabled={orphan_scan_running}
                        >
                            <option value="days" selected={orphan_grace_unit === "days"}>Days</option>
                            <option value="months" selected={orphan_grace_unit === "months"}>Months</option>
                            <option value="years" selected={orphan_grace_unit === "years"}>Years</option>
                        </select>
                    </div>
                </div>

                <button
                    type="button"
                    class="ui primary button {loading: orphan_scan_running, disabled: orphan_scan_running}"
                    onclick={startOrphanScan}
                    disabled={orphan_scan_running}
                >
                    <i class="search icon"></i>
                    Start scan
                </button>
            </div>

            <div if={orphan_scan_running} class="ui info message">
                <i class="spinner loading icon"></i>
                Scan in progress...
                <span if={orphan_scan_status}>
                    ({orphan_scan_status})
                </span>
            </div>

            <div if={orphan_scan_error} class="ui negative message">
                {orphan_scan_error}
            </div>

            <div if={orphan_scan_result}>
                <h4 class="ui dividing header">Scan results</h4>

                <p>
                    <strong>Generated:</strong>
                    {pretty_date(orphan_scan_result.generated_at)}
                </p>

                <div class="ui small statistics">
                    <div class="statistic">
                        <div class="value">
                            {orphan_scan_result.summary.scanned_count}
                        </div>
                        <div class="label">Scanned</div>
                    </div>

                    <div class="statistic">
                        <div class="value">
                            {orphan_scan_result.summary.referenced_count}
                        </div>
                        <div class="label">Referenced</div>
                    </div>

                    <div class="statistic">
                        <div class="value">
                            {orphan_scan_result.summary.orphaned_count}
                        </div>
                        <div class="label">Orphaned</div>
                    </div>

                    <div class="statistic">
                        <div class="value">
                            {orphan_scan_result.summary.recent_unreferenced_count}
                        </div>
                        <div class="label">Recent unreferenced</div>
                    </div>

                    <div class="statistic">
                        <div class="value">
                            {orphan_scan_result.summary.missing_count}
                        </div>
                        <div class="label">Missing</div>
                    </div>
                </div>

                <h4 class="ui dividing header">Orphaned objects</h4>

                <div if={orphan_scan_result.summary.orphaned_count === 0}
                    class="ui positive message">
                    No orphaned files detected.
                </div>

                <div if={orphan_scan_result.summary.orphaned_count > 0}>

                    <p>
                        Showing up to {orphan_scan_result.preview_limit}
                        orphaned objects out of
                        {orphan_scan_result.summary.orphaned_count}.
                    </p>

                    <!-- Actions above the file list -->
                    <div class="orphan-cleanup-toolbar">

                        <div class="ui checkbox">
                            <input
                                type="checkbox"
                                checked={orphan_all_preview_selected}
                                onchange={toggleAllOrphanSelection}
                                disabled={orphan_cleanup_running || orphan_scan_running}
                            >
                            <label>Select all displayed</label>
                        </div>

                        <span>
                            {orphan_selected_count} selected
                        </span>

                        <button
                            type="button"
                            class="ui orange button {loading: orphan_cleanup_running}"
                            onclick={startSelectedOrphanCleanup}
                            disabled={orphan_cleanup_running || orphan_scan_running || orphan_selected_count === 0}
                        >
                            <i class="check square outline icon"></i>
                            Delete selected ({orphan_selected_count})
                        </button>

                        <button
                            type="button"
                            class="ui red button {loading: orphan_cleanup_running}"
                            onclick={startAllOrphanCleanup}
                            disabled={orphan_cleanup_running || orphan_scan_running}
                        >
                            <i class="trash icon"></i>
                            Delete all orphaned ({orphan_scan_result.summary.orphaned_count})
                        </button>
                    </div>

                    <div if={orphan_cleanup_running} class="ui info message">
                        <i class="spinner loading icon"></i>
                        Cleanup progress...
                        <span if={orphan_cleanup_status}>
                            ({orphan_cleanup_status})
                        </span>
                    </div>

                    <div if={orphan_cleanup_error} class="ui negative message">
                        {orphan_cleanup_error}
                    </div>

                    <div if={orphan_cleanup_result} class="ui positive message">
                        <div class="header">Cleanup simulation completed</div>
                        <p>
                            Candidates: {orphan_cleanup_result.candidates} |
                            Skipped: {orphan_cleanup_result.skipped} |
                            Failed: {orphan_cleanup_result.failed}
                        </p>
                        <p>No files were deleted.</p>
                    </div>

                    <table class="ui celled compact table">
                        <thead>
                            <tr>
                                <th class="collapsing">Select</th>
                                <th>Bucket</th>
                                <th>Object key</th>
                                <th>Size</th>
                                <th>Last modified</th>
                            </tr>
                        </thead>

                        <tbody>
                            <tr each={file in orphan_scan_result.orphaned_preview}>
                                <td class="collapsing">
                                    <input
                                        type="checkbox"
                                        checked={isOrphanSelected(file)}
                                        onchange={toggleOrphanSelection}
                                        data-bucket={file.bucket}
                                        data-key={file.key}
                                        disabled={orphan_cleanup_running || orphan_scan_running}
                                    >
                                </td>
                                <td>{file.bucket}</td>
                                <td class="orphan-object-key">{file.key}</td>
                                <td>{pretty_bytes(file.size)}</td>
                                <td>{pretty_date(file.last_modified)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
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
        self.currentStorageTab = "usage-history";

        /****** Orphan files scanner *****/
        self.orphan_grace_period = 7;
        self.orphan_grace_unit = "days";
        self.orphan_scan_running = false;
        self.orphan_scan_status = null;
        self.orphan_scan_error = null;
        self.orphan_scan_result = null;
        self.orphan_scan_task_id = null;
        self.orphan_scan_poll_timer = null;
        self.orphan_scan_destroyed = false;
        
        /****** Orphan files cleanup *****/
        self.orphan_selected_objects = {};
        self.orphan_selected_count = 0;
        self.orphan_all_preview_selected = false;

        self.orphan_cleanup_running = false;
        self.orphan_cleanup_status = null;
        self.orphan_cleanup_error = null;
        self.orphan_cleanup_result = null;
        self.orphan_cleanup_task_id = null;
        self.orphan_cleanup_poll_timer = null;
        self.orphan_cleanup_started_at = null;

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
        })

        self.on("unmount", function() {
            self.orphan_scan_destroyed = true;
            self.clearOrphanScanTimer();
            self.clearOrphanCleanupTimer();
        });

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

        self.pretty_bytes = function(bytes) {
            if (bytes === null || bytes === undefined) {
                return "-";
            }

            if (bytes === 0) {
                return "0 B";
            }

            const units = ["B", "KB", "MB", "GB", "TB"];
            const index = Math.min(
                Math.floor(Math.log(bytes) / Math.log(1024)),
                units.length - 1
            );

            if (index === 0) {
                return bytes + " B";
            }

            return (bytes / Math.pow(1024, index)).toFixed(2) + " " + units[index];
        };

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

        self.onOrphanGracePeriodChange = function(event) {
            self.orphan_grace_period = event.target.value;
        };
        self.onOrphanGraceUnitChange = function(event) {
            self.orphan_grace_unit = event.target.value;
        };

        self.clearOrphanScanTimer = function() {
            if (self.orphan_scan_poll_timer !== null) {
                clearTimeout(self.orphan_scan_poll_timer);
                self.orphan_scan_poll_timer = null;
            }
        };

        self.startOrphanScan = function(event) {
            if (event) {
                event.preventDefault();
            }
            if (self.orphan_scan_running || self.orphan_cleanup_running) {
                return;
            }
            if (self.orphan_scan_running) {
                return;
            }

            const graceValue = Number(self.orphan_grace_period);
            const multipliers = {
                days: 1,
                months: 30,
                years: 365
            };

            const multiplier = multipliers[self.orphan_grace_unit];
            const gracePeriod = graceValue * multiplier;

            if (
                self.orphan_grace_period === "" ||
                !Number.isInteger(graceValue) ||
                !multiplier ||
                gracePeriod < 0 ||
                gracePeriod > 3650
            ) {
                toastr.error("Grace period must be between 0 and 3650 days.");
                return;
            }

            self.clearOrphanScanTimer();

            self.orphan_scan_started_at = Date.now();
            self.orphan_scan_running = true;
            self.orphan_scan_status = "PENDING";
            self.orphan_scan_error = null;
            self.orphan_scan_result = null;
            self.orphan_scan_task_id = null;
            self.orphan_selected_objects = {};
            self.orphan_selected_count = 0;
            self.orphan_all_preview_selected = false;
            self.orphan_cleanup_result = null;
            self.orphan_cleanup_error = null;
            self.update();

            CODALAB.api.start_orphan_files_scan(gracePeriod)
                .done(function(data) {
                    if (self.orphan_scan_destroyed) {
                        return;
                    }

                    self.orphan_scan_task_id = data.task_id;
                    self.orphan_scan_status = data.status || "PENDING";
                    self.update();

                    self.pollOrphanScan();
                })
                .fail(function(xhr) {
                    if (self.orphan_scan_destroyed) {
                        return;
                    }

                    self.orphan_scan_running = false;
                    self.orphan_scan_status = "FAILURE";
                    self.orphan_scan_error =
                        (xhr.responseJSON && xhr.responseJSON.detail) ||
                        "Could not start orphan files scan.";

                    self.update();
                });
        };

        self.pollOrphanScan = function() {
            if (
                self.orphan_scan_started_at &&
                Date.now() - self.orphan_scan_started_at > 60 * 60 * 1000
            ) {
                self.orphan_scan_running = false;
                self.orphan_scan_error = "Scan status polling timed out after one hour.";
                self.clearOrphanScanTimer();
                self.update();
                return;
            }
            if (
                self.orphan_scan_destroyed ||
                !self.orphan_scan_running ||
                !self.orphan_scan_task_id
            ) {
                return;
            }

            CODALAB.api.get_orphan_files_scan_status(self.orphan_scan_task_id)
                .done(function(data) {
                    if (self.orphan_scan_destroyed) {
                        return;
                    }

                    self.orphan_scan_status = data.status;

                    if (data.status === "SUCCESS") {
                        self.orphan_scan_running = false;
                        self.orphan_scan_result = data.result;
                        self.clearOrphanScanTimer();
                        self.update();

                    } else if (data.status === "FAILURE" ||
                            data.status === "REVOKED") {
                        self.orphan_scan_running = false;
                        self.orphan_scan_error =
                            data.error || "Orphan files scan failed.";
                        self.clearOrphanScanTimer();
                        self.update();

                    } else {
                        self.update();
                        self.scheduleOrphanScanPoll();
                    }
                })
                .fail(function() {
                    if (self.orphan_scan_destroyed) {
                        return;
                    }

                    self.orphan_scan_running = false;
                    self.orphan_scan_error =
                        "Could not retrieve orphan files scan status.";
                    self.clearOrphanScanTimer();
                    self.update();
                });
        };

        self.scheduleOrphanScanPoll = function() {
            self.clearOrphanScanTimer();

            if (self.orphan_scan_destroyed || !self.orphan_scan_running) {
                return;
            }

            self.orphan_scan_poll_timer = setTimeout(function() {
                self.orphan_scan_poll_timer = null;
                self.pollOrphanScan();
            }, 2000);
        };

        self.orphanObjectId = function(bucket, key) {
            return JSON.stringify([bucket, key]);
        };

        self.isOrphanSelected = function(file) {
            return !!self.orphan_selected_objects[
                self.orphanObjectId(file.bucket, file.key)
            ];
        };

        self.refreshOrphanSelection = function() {
            const files = self.orphan_scan_result
                ? self.orphan_scan_result.orphaned_preview
                : [];

            self.orphan_selected_count = files.filter(
                file => self.isOrphanSelected(file)
            ).length;

            self.orphan_all_preview_selected =
                files.length > 0 &&
                self.orphan_selected_count === files.length;

            self.update();
        };

        self.toggleOrphanSelection = function(event) {
            const bucket = event.target.getAttribute("data-bucket");
            const key = event.target.getAttribute("data-key");
            const id = self.orphanObjectId(bucket, key);

            if (event.target.checked) {
                self.orphan_selected_objects[id] = {bucket, key};
            } else {
                delete self.orphan_selected_objects[id];
            }

            self.refreshOrphanSelection();
        };

        self.toggleAllOrphanSelection = function(event) {
            const checked = event.target.checked;
            const files = self.orphan_scan_result.orphaned_preview;

            files.forEach(function(file) {
                const id = self.orphanObjectId(file.bucket, file.key);

                if (checked) {
                    self.orphan_selected_objects[id] = {
                        bucket: file.bucket,
                        key: file.key
                    };
                } else {
                    delete self.orphan_selected_objects[id];
                }
            });

            self.refreshOrphanSelection();
        };

        self.clearOrphanCleanupTimer = function() {
            if (self.orphan_cleanup_poll_timer !== null) {
                clearTimeout(self.orphan_cleanup_poll_timer);
                self.orphan_cleanup_poll_timer = null;
            }
        };

        self.startSelectedOrphanCleanup = function(event) {
            if (event) event.preventDefault();

            const selected = Object.values(self.orphan_selected_objects);

            if (!selected.length || selected.length > 100) {
                toastr.error("Select between 1 and 100 files.");
                return;
            }

            self.startOrphanCleanup("selected", selected);
        };

        self.startAllOrphanCleanup = function(event) {
            if (event) event.preventDefault();

            self.startOrphanCleanup("all", null);
        };

        self.startOrphanCleanup = function(mode, selectedObjects) {
            if (
                self.orphan_cleanup_running ||
                self.orphan_scan_running ||
                !self.orphan_scan_result
            ) {
                return;
            }

            const count = mode === "all"
                ? self.orphan_scan_result.summary.orphaned_count
                : selectedObjects.length;

            const message = mode === "all"
                ? "Permanently delete all " + count +
                " eligible orphaned files, including files not displayed?"
                : "Permanently delete " + count + " selected orphaned files?";

            if (!window.confirm(
                message + "\n\nThis operation cannot be undone."
            )) {
                return;
            }

            if (!window.confirm(message + "\n\nNo files will be deleted.")) {
                return;
            }

            // Reuse the grace period of the completed scan,
            // not potentially edited form values.
            const gracePeriod = self.orphan_scan_result.grace_period_days;

            self.clearOrphanCleanupTimer();

            self.orphan_cleanup_running = true;
            self.orphan_cleanup_status = "PENDING";
            self.orphan_cleanup_error = null;
            self.orphan_cleanup_result = null;
            self.orphan_cleanup_task_id = null;
            self.orphan_cleanup_started_at = Date.now();
            self.update();

            const payload = {
                grace_period_days: gracePeriod,
                mode: mode,
                dry_run: true
            };

            if (mode === "selected") {
                payload.selected_objects = selectedObjects;
            }

            CODALAB.api.start_orphan_files_cleanup(payload)
                .done(function(data) {
                    if (self.orphan_scan_destroyed) return;

                    self.orphan_cleanup_task_id = data.task_id;
                    self.orphan_cleanup_status = data.status || "PENDING";
                    self.update();
                    self.pollOrphanCleanup();
                })
                .fail(function(xhr) {
                    if (self.orphan_scan_destroyed) return;

                    self.orphan_cleanup_running = false;
                    self.orphan_cleanup_status = "FAILURE";
                    self.orphan_cleanup_error =
                        (xhr.responseJSON && xhr.responseJSON.detail) ||
                        "Could not start cleanup simulation.";
                    self.update();
                });
        };

        self.pollOrphanCleanup = function() {
            if (
                self.orphan_scan_destroyed ||
                !self.orphan_cleanup_running ||
                !self.orphan_cleanup_task_id
            ) {
                return;
            }

            if (
                Date.now() - self.orphan_cleanup_started_at >
                60 * 60 * 1000
            ) {
                self.orphan_cleanup_running = false;
                self.orphan_cleanup_error =
                    "Cleanup status polling timed out after one hour.";
                self.clearOrphanCleanupTimer();
                self.update();
                return;
            }

            CODALAB.api.get_orphan_files_cleanup_status(
                self.orphan_cleanup_task_id
            )
                .done(function(data) {
                    if (self.orphan_scan_destroyed) return;

                    self.orphan_cleanup_status = data.status;

                    if (data.status === "SUCCESS") {
                        self.orphan_cleanup_running = false;
                        self.orphan_cleanup_result = data.result;
                        self.clearOrphanCleanupTimer();
                        self.update();

                    } else if (
                        data.status === "FAILURE" ||
                        data.status === "REVOKED"
                    ) {
                        self.orphan_cleanup_running = false;
                        self.orphan_cleanup_error =
                            data.error || "Cleanup simulation failed.";
                        self.clearOrphanCleanupTimer();
                        self.update();

                    } else {
                        self.update();
                        self.clearOrphanCleanupTimer();

                        self.orphan_cleanup_poll_timer = setTimeout(
                            function() {
                                self.orphan_cleanup_poll_timer = null;
                                self.pollOrphanCleanup();
                            },
                            2000
                        );
                    }
                })
                .fail(function() {
                    if (self.orphan_scan_destroyed) return;

                    self.orphan_cleanup_running = false;
                    self.orphan_cleanup_error =
                        "Could not retrieve cleanup status.";
                    self.clearOrphanCleanupTimer();
                    self.update();
                });
        };

        self.pretty_date = function (date_string) {
            if (!!date_string) {
                return luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL)
            } else {
                return ''
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

        .orphan-object-key {
            overflow-wrap: anywhere;
            word-break: break-word;
            max-width: 450px;
            font-family: monospace;
        }
        .orphan-cleanup-toolbar {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin: 16px 0;
        }

        .orphan-cleanup-toolbar .ui.button {
            margin: 0;
        }
    </style>
</analytics>
