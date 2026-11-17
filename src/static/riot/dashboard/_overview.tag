<dashboard-overview>
    <div class="dashboard-tab-pane" show="{ opts.p.activeTab === 'overview' }">
        <!-- Unified Stats Bar -->
        <div class="dashboard-stats-bar">
            <div class="dashboard-stat">
                <div class="dashboard-stat-value">{ format_number(opts.p.filteredCompetitions.length) }</div>
                <div class="dashboard-stat-label">Competitions</div>
            </div>
            <div class="dashboard-stat">
                <div class="dashboard-stat-value">{ format_number(opts.p.kpis.distinctOrganizers) }</div>
                <div class="dashboard-stat-label">Organizers</div>
            </div>
            <div class="dashboard-stat">
                <div class="dashboard-stat-value">{ format_number(opts.p.kpis.participants) }</div>
                <div class="dashboard-stat-label">Participants</div>
            </div>
            <div class="dashboard-stat">
                <div class="dashboard-stat-value">{ format_number(opts.p.kpis.submissions) }</div>
                <div class="dashboard-stat-label">Submissions</div>
            </div>
        </div>

        <!-- Charts Grid for Overview -->
        <div class="dashboard-charts-grid">
            <!-- 1. Most popular Competitions (Full width, exact same component style as CSV download table) -->
            <div class="ui segment table-card full-width" if="{ opts.p.showCompsChart }">
                <div class="table-top-bar">
                    <h3 class="ui header" style="margin: 0;">
                        Most popular Competitions
                    </h3>
                    <button class="ui green button" onclick="{ downloadLeaderboardCSV }">
                        <i class="icon download"></i>Download as CSV
                    </button>
                </div>

                <div class="table-scroll-wrap" style="max-height: 480px; overflow-y: auto; overflow-x: auto; -webkit-overflow-scrolling: touch;">
                    <table class="ui celled compact striped selectable table">
                        <thead>
                            <tr>
                                <th style="width: 50px; text-align: center;">#</th>
                                <th>Competition</th>
                                <th style="width: 150px;">Organizer</th>
                                <th style="width: 120px; text-align: right;">Participants</th>
                                <th style="width: 120px; text-align: right;">Submissions</th>
                                <th style="width: 120px; text-align: center;">Created</th>
                                <th style="width: 70px; text-align: center;">Link</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ comp, idx in opts.p.popularCompetitions }">
                                <td class="center aligned">{ idx + 1 }</td>
                                <td>
                                    <strong><a href="{ comp.url }" target="_blank">{ comp.title }</a></strong>
                                </td>
                                <td>{ comp.organizer }</td>
                                <td class="right aligned">{ format_number(comp.participants_count) }</td>
                                <td class="right aligned">{ format_number(comp.submissions_count) }</td>
                                <td class="center aligned">{ pretty_date(comp.created_when) }</td>
                                <td class="center aligned">
                                    <a href="{ comp.url }" class="ui mini primary icon button" target="_blank" title="View Competition">
                                        <i class="external alternate icon"></i>
                                    </a>
                                </td>
                            </tr>
                            <tr if="{ !opts.p.popularCompetitions || opts.p.popularCompetitions.length === 0 }">
                                <td colspan="7" class="center aligned table-empty-row">
                                    <em>No competitions match the selected filters.</em>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 2. Top Organizers (Full width) -->
            <div class="dashboard-chart-card full-width" if="{ opts.p.showOrgsChart }">
                <div class="chart-header">
                    <h4 class="chart-title">Top Organizers</h4>
                </div>
                <div class="canvas-wrap canvas-wrap-orgs">
                    <canvas id="chOrgs" ref="chOrgs"></canvas>
                </div>
            </div>

            <!-- 3. Cumulative Competition Launches Over Time (Full width) -->
            <div class="dashboard-chart-card full-width" if="{ opts.p.filteredCompetitions.length > 0 }">
                <div class="chart-header">
                    <h4 class="chart-title">Cumulative Competition Launches Over Time</h4>
                </div>
                <div class="canvas-wrap canvas-wrap-cum">
                    <canvas id="chCumulativeGrowth" ref="chCumulativeGrowth"></canvas>
                </div>
            </div>

            <!-- 4. Competition Launches with Interval & Date Pickers (Full width) -->
            <div class="dashboard-chart-card full-width" if="{ opts.p.filteredCompetitions.length > 0 }">
                <div class="chart-header chart-header-with-controls">
                    <h4 class="chart-title">Competition Launches</h4>
                    <div class="chart-controls">
                        <div class="control-group">
                            <div class="ui selection dropdown chart-dropdown" ref="launchesIntervalDropdown">
                                <input type="hidden" name="launches_interval" value="{ launchesInterval }">
                                <div class="text">{ formatInterval(launchesInterval) }</div>
                                <i class="dropdown icon"></i>
                                <div class="menu">
                                    <div class="item" data-value="yearly">Yearly</div>
                                    <div class="item" data-value="semiannual">Semiannual</div>
                                    <div class="item" data-value="monthly">Monthly</div>
                                    <div class="item" data-value="weekly">Weekly</div>
                                </div>
                            </div>
                        </div>
                        <div class="control-group date-range-group">
                            <div class="ui calendar chart-calendar" ref="launchesStartCalendar">
                                <div class="ui input left icon">
                                    <i class="calendar icon"></i>
                                    <input type="text" placeholder="Start Date">
                                </div>
                            </div>
                            <span class="date-sep">–</span>
                            <div class="ui calendar chart-calendar" ref="launchesEndCalendar">
                                <div class="ui input left icon">
                                    <i class="calendar icon"></i>
                                    <input type="text" placeholder="End Date">
                                </div>
                            </div>
                            <button type="button" class="ui basic icon button chart-clear-btn" if="{ launchesStartDateStr || launchesEndDateStr }" onclick="{ onClearLaunchesDates }" title="Reset chart date range">
                                <i class="times icon"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="canvas-wrap canvas-wrap-launches">
                    <canvas id="chLaunches" ref="chLaunches"></canvas>
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this;
        self.charts = {};
        self.launchesInterval = 'yearly';
        self.launchesStartDateStr = '';
        self.launchesEndDateStr = '';

        self.format_number = function (num) {
            return (opts.p && opts.p.format_number) ? opts.p.format_number(num) : Number(num || 0).toLocaleString();
        };

        self.pretty_date = function (date_string) {
            if (!date_string) return '—';
            try {
                if (typeof luxon !== 'undefined' && luxon.DateTime) {
                    var dt = luxon.DateTime.fromISO(date_string);
                    if (dt.isValid) return dt.toLocaleString(luxon.DateTime.DATE_MED);
                }
                var d = new Date(date_string);
                return !isNaN(d.getTime()) ? d.toLocaleDateString() : date_string;
            } catch (e) {
                return date_string;
            }
        };

        self.formatInterval = function (interval) {
            if (!interval) return 'Yearly';
            return interval.charAt(0).toUpperCase() + interval.slice(1);
        };

        self.downloadLeaderboardCSV = function (e) {
            if (e) e.preventDefault();
            var rows = (opts.p && opts.p.popularCompetitions) || [];
            if (rows.length === 0) return;
            var esc = (opts.p && opts.p.escapeCsv) || function (v) { return '"' + String(v || '').replace(/"/g, '""') + '"'; };
            var headers = ["rank", "id", "title", "organizer", "participants", "submissions", "created_when", "url"].map(esc);
            var lines = [headers.join(",")];
            rows.forEach(function (c, idx) {
                var rowData = [
                    idx + 1,
                    c.id,
                    esc(c.title),
                    esc(c.organizer),
                    c.participants_count || 0,
                    c.submissions_count || 0,
                    esc(c.created_when ? c.created_when.split("T")[0] : ""),
                    esc(c.url)
                ];
                lines.push(rowData.join(","));
            });
            if (opts.p && opts.p.downloadCsv) {
                opts.p.downloadCsv("codabench_popular_competitions.csv", lines);
            }
        };

        self.onClearLaunchesDates = function () {
            self.launchesStartDateStr = '';
            self.launchesEndDateStr = '';
            if (self.refs.launchesStartCalendar) $(self.refs.launchesStartCalendar).calendar('clear');
            if (self.refs.launchesEndCalendar) $(self.refs.launchesEndCalendar).calendar('clear');
            self.renderLaunchesChart();
            self.update();
        };

        self.renderCharts = function () {
            if (!opts.p || opts.p.activeTab !== 'overview') {
                self.destroyAllCharts();
                return;
            }
            var rows = opts.p.filteredCompetitions || [];
            if (rows.length === 0) {
                self.destroyAllCharts();
                return;
            }

            self.renderCumulativeGrowthChart();
            self.renderLaunchesChart();
            if (opts.p.showOrgsChart) {
                self.renderTopOrganizersChart();
            } else if (self.charts.chOrgs) {
                self.charts.chOrgs.destroy();
                delete self.charts.chOrgs;
            }
        };

        self.renderTopOrganizersChart = function () {
            var el = self.refs.chOrgs || document.getElementById("chOrgs");
            if (!el) return;
            var rows = opts.p.filteredCompetitions || [];
            var map = {};
            rows.forEach(function (c) {
                map[c.organizer] = (map[c.organizer] || 0) + 1;
            });
            var entries = Object.keys(map).map(function (k) { return [k, map[k]]; });
            entries.sort(function (a, b) { return b[1] - a[1]; });
            var pairs = entries.slice(0, 10);

            var labels = pairs.map(function (p) { return p[0]; });
            var dataVals = pairs.map(function (p) { return p[1]; });

            if (self.charts.chOrgs && self.charts.chOrgs.ctx && self.charts.chOrgs.ctx.canvas === el) {
                self.charts.chOrgs.data.labels = labels;
                self.charts.chOrgs.data.datasets[0].data = dataVals;
                self.charts.chOrgs.update();
            } else {
                if (self.charts.chOrgs) self.charts.chOrgs.destroy();
                self.charts.chOrgs = new Chart(el, {
                    type: "horizontalBar",
                    data: {
                        labels: labels,
                        datasets: [{
                            data: dataVals,
                            backgroundColor: "#21ba45",
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: { display: false },
                        scales: {
                            xAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                            yAxes: [{ gridLines: { display: false }, ticks: { fontSize: 11, fontColor: "#334155" } }]
                        }
                    }
                });
            }
        };

        self.renderCumulativeGrowthChart = function () {
            var el = self.refs.chCumulativeGrowth || document.getElementById("chCumulativeGrowth");
            if (!el) return;
            var rows = opts.p.filteredCompetitions || [];
            var validComps = rows.filter(function (c) {
                if (!c.created_when) return false;
                var d = new Date(c.created_when);
                return !isNaN(d.getTime());
            });

            if (validComps.length === 0) {
                if (self.charts.chCumulativeGrowth) {
                    self.charts.chCumulativeGrowth.destroy();
                    delete self.charts.chCumulativeGrowth;
                }
                return;
            }

            var months = (opts.p && opts.p.getCompetitionsMonthRange) ? opts.p.getCompetitionsMonthRange(validComps) : [];

            var countsByMonth = {};
            validComps.forEach(function (c) {
                var d = new Date(c.created_when);
                var mStr = d.getUTCFullYear() + "-" + (d.getUTCMonth() + 1 < 10 ? "0" : "") + (d.getUTCMonth() + 1);
                countsByMonth[mStr] = (countsByMonth[mStr] || 0) + 1;
            });

            var runningTotal = 0;
            var cumData = months.map(function (m) {
                runningTotal += (countsByMonth[m] || 0);
                return runningTotal;
            });

            if (self.charts.chCumulativeGrowth && self.charts.chCumulativeGrowth.ctx && self.charts.chCumulativeGrowth.ctx.canvas === el) {
                self.charts.chCumulativeGrowth.data.labels = months;
                self.charts.chCumulativeGrowth.data.datasets[0].data = cumData;
                self.charts.chCumulativeGrowth.data.datasets[0].lineTension = 0;
                self.charts.chCumulativeGrowth.update();
            } else {
                if (self.charts.chCumulativeGrowth) self.charts.chCumulativeGrowth.destroy();
                self.charts.chCumulativeGrowth = new Chart(el, {
                    type: "line",
                    data: {
                        labels: months,
                        datasets: [{
                            label: "Cumulative Competition Launches",
                            data: cumData,
                            borderColor: "#2980b9",
                            backgroundColor: "rgba(41, 128, 185, 0.08)",
                            borderWidth: 2.5,
                            pointRadius: months.length > 36 ? 0 : 2,
                            pointHoverRadius: 5,
                            pointBackgroundColor: "#2980b9",
                            fill: true,
                            lineTension: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: { display: false },
                        elements: {
                            line: { tension: 0 }
                        },
                        tooltips: {
                            mode: "index",
                            intersect: false
                        },
                        scales: {
                            xAxes: [{
                                gridLines: { display: false },
                                ticks: {
                                    autoSkip: true,
                                    maxTicksLimit: 12,
                                    maxRotation: 45,
                                    minRotation: 0
                                }
                            }],
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0
                                }
                            }]
                        }
                    }
                });
            }
        };

        self.renderLaunchesChart = function () {
            var el = self.refs.chLaunches || document.getElementById("chLaunches");
            if (!el) return;

            var startDate = self.launchesStartDateStr ? new Date(self.launchesStartDateStr + "T00:00:00Z") : null;
            var endDate = self.launchesEndDateStr ? new Date(self.launchesEndDateStr + "T23:59:59.999Z") : null;

            var rows = opts.p.filteredCompetitions || [];
            var validComps = rows.filter(function (c) {
                if (!c.created_when) return false;
                var d = new Date(c.created_when);
                if (isNaN(d.getTime())) return false;
                if (startDate && d < startDate) return false;
                if (endDate && d > endDate) return false;
                return true;
            });

            if (validComps.length === 0) {
                if (self.charts.chLaunches) {
                    self.charts.chLaunches.destroy();
                    delete self.charts.chLaunches;
                }
                return;
            }

            var interval = self.launchesInterval || "yearly";

            function getBucketKey(d) {
                var y = d.getUTCFullYear();
                var m = d.getUTCMonth();
                if (interval === "yearly") {
                    return y.toString();
                } else if (interval === "semiannual") {
                    return y + (m < 6 ? "-S1" : "-S2");
                } else if (interval === "monthly") {
                    return y + "-" + (m + 1 < 10 ? "0" : "") + (m + 1);
                } else {
                    var target = new Date(Date.UTC(y, m, d.getUTCDate()));
                    var dayNr = target.getUTCDay() || 7;
                    target.setUTCDate(target.getUTCDate() + 4 - dayNr);
                    var yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
                    var weekNo = Math.ceil((((target - yearStart) / 86400000) + 1) / 7);
                    return target.getUTCFullYear() + "-W" + (weekNo < 10 ? "0" : "") + weekNo;
                }
            }

            var counts = {};
            validComps.forEach(function (c) {
                var k = getBucketKey(new Date(c.created_when));
                counts[k] = (counts[k] || 0) + 1;
            });

            var labels = Object.keys(counts).sort();

            if (interval === "monthly" && labels.length > 1) {
                var first = labels[0].split("-");
                var last = labels[labels.length - 1].split("-");
                if (opts.p && opts.p.getMonthRange) {
                    var sDate = new Date(Date.UTC(parseInt(first[0], 10), parseInt(first[1], 10) - 1, 1));
                    var eDate = new Date(Date.UTC(parseInt(last[0], 10), parseInt(last[1], 10) - 1, 1));
                    labels = opts.p.getMonthRange(sDate, eDate);
                }
            }

            var dataVals = labels.map(function (k) {
                return counts[k] || 0;
            });

            if (self.charts.chLaunches && self.charts.chLaunches.ctx && self.charts.chLaunches.ctx.canvas === el) {
                self.charts.chLaunches.data.labels = labels;
                self.charts.chLaunches.data.datasets[0].data = dataVals;
                self.charts.chLaunches.update();
            } else {
                if (self.charts.chLaunches) self.charts.chLaunches.destroy();
                self.charts.chLaunches = new Chart(el, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "Launches",
                            data: dataVals,
                            backgroundColor: "#2980b9",
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: { display: false },
                        scales: {
                            xAxes: [{
                                gridLines: { display: false },
                                ticks: {
                                    autoSkip: true,
                                    maxTicksLimit: 20,
                                    maxRotation: 45,
                                    minRotation: 0
                                }
                            }],
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0
                                }
                            }]
                        }
                    }
                });
            }
        };

        var general_calendar_options = {
            type: 'date',
            formatter: {
                date: function (date) {
                    if (!date) return '';
                    var d = date.getDate(), m = date.getMonth() + 1, y = date.getFullYear();
                    return y + '-' + (m <= 9 ? '0' + m : m) + '-' + (d <= 9 ? '0' + d : d);
                }
            }
        };

        function initCalendars() {
            if (!self.refs.launchesStartCalendar || !self.refs.launchesEndCalendar) return;
            var $start = $(self.refs.launchesStartCalendar);
            var $end = $(self.refs.launchesEndCalendar);
            if ($start.data('module-calendar')) return;

            $start.calendar(Object.assign({}, general_calendar_options, {
                endCalendar: $end,
                popupOptions: { position: 'bottom left', prefer: 'opposite', hideOnScroll: true },
                onChange: function (date, text) {
                    var val = text || '';
                    if (val !== self.launchesStartDateStr) {
                        self.launchesStartDateStr = val;
                        self.renderLaunchesChart();
                        self.update();
                    }
                }
            }));

            $end.calendar(Object.assign({}, general_calendar_options, {
                startCalendar: $start,
                popupOptions: { position: 'bottom right', prefer: 'opposite', hideOnScroll: true },
                onChange: function (date, text) {
                    var val = text || '';
                    if (val !== self.launchesEndDateStr) {
                        self.launchesEndDateStr = val;
                        self.renderLaunchesChart();
                        self.update();
                    }
                }
            }));
        }

        function initIntervalDropdown() {
            if (!self.refs.launchesIntervalDropdown) return;
            var $dd = $(self.refs.launchesIntervalDropdown);
            if (!$dd.data('module-dropdown')) {
                $dd.dropdown({
                    onChange: function (val) {
                        if (val && val !== self.launchesInterval) {
                            self.launchesInterval = val;
                            self.renderLaunchesChart();
                            self.update();
                        }
                    }
                });
            }
        }

        self.destroyAllCharts = function () {
            Object.keys(self.charts).forEach(function (id) {
                if (self.charts[id]) self.charts[id].destroy();
            });
            self.charts = {};
        };

        self.on('mount', function () {
            if (opts.p && opts.p.activeTab === 'overview') {
                initCalendars();
                initIntervalDropdown();
                self.renderCharts();
            }
        });

        self.on('updated', function () {
            if (opts.p && opts.p.activeTab === 'overview') {
                initCalendars();
                initIntervalDropdown();
                self.renderCharts();
            } else {
                self.destroyAllCharts();
            }
        });

        self.on('unmount', function () {
            self.destroyAllCharts();
        });
    </script>
</dashboard-overview>
