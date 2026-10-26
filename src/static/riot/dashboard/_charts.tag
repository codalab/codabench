<dashboard-charts>
    <!-- Unified Stats Bar (matching home page About stats) -->
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

    <!-- Charts Grid -->
    <div class="dashboard-charts-grid">
        <!-- 1. Top Row: Top Organizers & Most Popular Competitions -->
        <div class="dashboard-chart-card" if="{ opts.p.showOrgsChart }">
            <div class="chart-header">
                <h4 class="chart-title">Top Organizers</h4>
            </div>
            <div class="canvas-wrap">
                <canvas id="chOrgs" ref="chOrgs"></canvas>
            </div>
        </div>
        <div class="dashboard-chart-card" if="{ opts.p.showCompsChart }">
            <div class="chart-header">
                <h4 class="chart-title">Most Popular Competitions</h4>
            </div>
            <div class="canvas-wrap">
                <canvas id="chComps" ref="chComps"></canvas>
            </div>
        </div>

        <!-- 2. Middle Row: Analysis and Trends Diagrams -->
        <!-- Cumulative Growth (Full width) -->
        <div class="dashboard-chart-card full-width" if="{ opts.p.filteredCompetitions.length > 0 }">
            <div class="chart-header">
                <h4 class="chart-title">Cumulative Growth</h4>
            </div>
            <div class="canvas-wrap">
                <canvas id="chCumulativeGrowth" ref="chCumulativeGrowth"></canvas>
            </div>
        </div>

        <!-- Competition Launches with Interval & Date Pickers (Full width + extra large height) -->
        <div class="dashboard-chart-card full-width" if="{ opts.p.filteredCompetitions.length > 0 }">
            <div class="chart-header chart-header-with-controls">
                <h4 class="chart-title">Competition Launches</h4>
                <div class="chart-controls">
                    <div class="control-group">
                        <div class="ui selection dropdown chart-dropdown" ref="launchesIntervalDropdown">
                            <input type="hidden" name="launches_interval" value="{ opts.p.launchesInterval || 'yearly' }">
                            <div class="text">{ formatInterval(opts.p.launchesInterval) }</div>
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
                        <button type="button" class="ui basic icon button chart-clear-btn" if="{ opts.p.launchesStartDateStr || opts.p.launchesEndDateStr }" onclick="{ onClearLaunchesDates }" title="Reset chart date range">
                            <i class="times icon"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="canvas-wrap canvas-wrap-launches">
                <canvas id="chLaunches" ref="chLaunches"></canvas>
            </div>
        </div>

        <!-- Cumulative Occurrences by Category (Full width + expanded height) -->
        <div class="dashboard-chart-card full-width" if="{ opts.p.showCumTagsChart }">
            <div class="chart-header chart-header-with-controls">
                <h4 class="chart-title">Cumulative Occurrences</h4>
                <div class="chart-controls">
                    <div class="control-group">
                        <label class="control-label">Category:</label>
                        <div class="ui selection dropdown chart-dropdown" ref="cumCatDropdown">
                            <input type="hidden" name="cum_cat" value="{ opts.p.selectedCumCat }">
                            <div class="text">{ opts.p.selectedCumCat }</div>
                            <i class="dropdown icon"></i>
                            <div class="menu">
                                <div class="item" each="{ cat in (opts.p.categoriesWithTags || opts.p.availableCategories) }" data-value="{ cat }">{ cat }</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="canvas-wrap canvas-wrap-expanded">
                <canvas id="chCumTags" ref="chCumTags"></canvas>
            </div>
        </div>

        <!-- Tag Co-occurrence Heatmap (Full width) -->
        <div class="dashboard-chart-card full-width" if="{ opts.p.showHeatmapChart }">
            <div class="chart-header chart-header-with-controls">
                <h4 class="chart-title">Tag Co-occurrence Heatmap</h4>
                <div class="chart-controls heatmap-controls">
                    <div class="control-group">
                        <label class="control-label">Rows:</label>
                        <div class="ui selection dropdown chart-dropdown" ref="heatmapCat1Dropdown">
                            <input type="hidden" name="heatmap_cat1" value="{ opts.p.heatmapCat1 }">
                            <div class="text">{ opts.p.heatmapCat1 }</div>
                            <i class="dropdown icon"></i>
                            <div class="menu">
                                <div class="item" each="{ cat in (opts.p.categoriesWithTags || opts.p.availableCategories) }" data-value="{ cat }">{ cat }</div>
                            </div>
                        </div>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Cols:</label>
                        <div class="ui selection dropdown chart-dropdown" ref="heatmapCat2Dropdown">
                            <input type="hidden" name="heatmap_cat2" value="{ opts.p.heatmapCat2 }">
                            <div class="text">{ opts.p.heatmapCat2 }</div>
                            <i class="dropdown icon"></i>
                            <div class="menu">
                                <div class="item" each="{ cat in (opts.p.categoriesWithTags || opts.p.availableCategories) }" data-value="{ cat }">{ cat }</div>
                            </div>
                        </div>
                    </div>
                    <div class="control-group">
                        <div class="ui checkbox" ref="heatmapNormalizeCheckbox" style="margin-left: 8px;">
                            <input type="checkbox" ref="heatmapNormalizeInput" checked="{ opts.p.heatmapNormalize }" onchange="{ onHeatmapNormalizeChange }">
                            <label style="cursor: pointer; user-select: none; font-weight: 600;">Normalize</label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="canvas-wrap canvas-wrap-heatmap">
                <canvas id="chHeatmap" ref="chHeatmap"></canvas>
            </div>
        </div>

        <!-- 3. Bottom: All Tag Category Charts -->
        <div class="dashboard-chart-card" each="{ chart, idx in opts.p.chartCards }">
            <div class="chart-header">
                <h4 class="chart-title">By { chart.catName }</h4>
            </div>
            <div class="canvas-wrap">
                <canvas id="{ chart.id }" ref="dynamicCharts"></canvas>
            </div>
        </div>
    </div>

    <script>
        var self = this;
        self.format_number = function (num) {
            if (num === null || num === undefined) return "0";
            return Number(num).toLocaleString();
        };

        self.formatInterval = function (interval) {
            if (interval === 'semiannual') return 'Semiannual';
            if (interval === 'monthly') return 'Monthly';
            if (interval === 'weekly') return 'Weekly';
            return 'Yearly';
        };

        var general_calendar_options = {
            type: 'date',
            formatter: {
                date: function (date, settings) {
                    if (!date) return '';
                    var d = date.getDate(),
                        m = date.getMonth() + 1,
                        y = date.getFullYear();
                    return y + '-' + (m <= 9 ? '0' + m : m) + '-' + (d <= 9 ? '0' + d : d);
                }
            }
        };

        function initCalendars() {
            if (!self.refs.launchesStartCalendar || !self.refs.launchesEndCalendar) return;
            var $start = $(self.refs.launchesStartCalendar);
            var $end = $(self.refs.launchesEndCalendar);
            if ($start.data('module-calendar')) return;

            var start_options = Object.assign({}, general_calendar_options, {
                endCalendar: $end,
                popupOptions: {
                    position: 'bottom left',
                    lastResort: 'bottom left',
                    prefer: 'opposite',
                    hideOnScroll: true
                },
                onChange: function (date, text) {
                    if (opts.p) {
                        var val = text || '';
                        if (val !== opts.p.launchesStartDateStr) {
                            opts.p.launchesStartDateStr = val;
                            opts.p.renderLaunchesChart();
                            self.update();
                        }
                    }
                }
            });

            var end_options = Object.assign({}, general_calendar_options, {
                startCalendar: $start,
                popupOptions: {
                    position: 'bottom right',
                    lastResort: 'bottom right',
                    prefer: 'opposite',
                    hideOnScroll: true
                },
                onChange: function (date, text) {
                    if (opts.p) {
                        var val = text || '';
                        if (val !== opts.p.launchesEndDateStr) {
                            opts.p.launchesEndDateStr = val;
                            opts.p.renderLaunchesChart();
                            self.update();
                        }
                    }
                }
            });

            $start.calendar(start_options);
            $end.calendar(end_options);
        }

        self.onClearLaunchesDates = function () {
            if (opts.p) {
                opts.p.launchesStartDateStr = '';
                opts.p.launchesEndDateStr = '';
                if (self.refs.launchesStartCalendar) $(self.refs.launchesStartCalendar).calendar('clear');
                if (self.refs.launchesEndCalendar) $(self.refs.launchesEndCalendar).calendar('clear');
                opts.p.renderLaunchesChart();
                self.update();
            }
        };

        self.onHeatmapNormalizeChange = function (e) {
            if (opts.p) {
                opts.p.heatmapNormalize = e.target.checked;
                opts.p.renderHeatmapChart();
            }
        };

        function initDropdowns() {
            if (self.refs.launchesIntervalDropdown) {
                var $d = $(self.refs.launchesIntervalDropdown);
                if (!$d.data('module-dropdown')) {
                    $d.dropdown({
                        onChange: function (val) {
                            if (opts.p && val && val !== opts.p.launchesInterval) {
                                opts.p.launchesInterval = val;
                                opts.p.renderLaunchesChart();
                            }
                        }
                    });
                }
                if (opts.p && opts.p.launchesInterval) {
                    $d.dropdown('set selected', opts.p.launchesInterval);
                }
            }

            var catDropdowns = [
                {
                    ref: 'cumCatDropdown',
                    getVal: function () { return opts.p && opts.p.selectedCumCat; },
                    setVal: function (v) {
                        if (opts.p) {
                            opts.p.selectedCumCat = v;
                            opts.p.renderCumTagsChart();
                        }
                    }
                },
                {
                    ref: 'heatmapCat1Dropdown',
                    getVal: function () { return opts.p && opts.p.heatmapCat1; },
                    setVal: function (v) {
                        if (opts.p) {
                            opts.p.heatmapCat1 = v;
                            opts.p.renderHeatmapChart();
                        }
                    }
                },
                {
                    ref: 'heatmapCat2Dropdown',
                    getVal: function () { return opts.p && opts.p.heatmapCat2; },
                    setVal: function (v) {
                        if (opts.p) {
                            opts.p.heatmapCat2 = v;
                            opts.p.renderHeatmapChart();
                        }
                    }
                }
            ];

            catDropdowns.forEach(function (item) {
                var el = self.refs[item.ref];
                if (!el) return;
                var $dropdown = $(el);
                if (!$dropdown.data('module-dropdown')) {
                    $dropdown.dropdown({
                        onChange: function (val) {
                            if (val && val !== item.getVal()) {
                                item.setVal(val);
                            }
                        }
                    });
                } else {
                    $dropdown.dropdown('refresh');
                }
                var cur = item.getVal();
                if (cur) {
                    $dropdown.dropdown('set selected', cur);
                }
            });
        }

        function syncRefs() {
            if (opts.p && opts.p.refs) {
                opts.p.refs.chCumulativeGrowth = self.refs.chCumulativeGrowth;
                opts.p.refs.chLaunches = self.refs.chLaunches;
                opts.p.refs.chCumTags = self.refs.chCumTags;
                opts.p.refs.chHeatmap = self.refs.chHeatmap;
                opts.p.refs.chOrgs = self.refs.chOrgs;
                opts.p.refs.chComps = self.refs.chComps;
                opts.p.refs.dynamicCharts = self.refs.dynamicCharts;
            }
        }

        self.on('mount', function () {
            syncRefs();
            initCalendars();
            initDropdowns();
        });

        self.on('updated', function () {
            syncRefs();
            initCalendars();
            initDropdowns();
        });
    </script>

    <style type="text/stylus">
        dashboard-charts
            display block
            width 100%

        .dashboard-stats-bar
            display grid
            grid-template-columns repeat(4, 1fr)
            width 100%
            margin 0 0 20px 0
            padding 22px 0
            background-color #fff
            border 1px solid #e3e7ec
            border-radius 10px
            box-shadow 0 1px 2px rgba(0, 0, 0, 0.04)

        .dashboard-stat
            padding 0 16px
            text-align center
            border-left 1px solid #e3e7ec

            &:first-child
                border-left none

        .dashboard-stat-value
            color #1b1b1b
            font-size 28px
            font-weight 700
            line-height 1.1

        .dashboard-stat-label
            margin-top 6px
            color #4a5568
            font-size 15px
            font-weight 600

        @media (max-width 767px)
            .dashboard-stats-bar
                grid-template-columns 1fr
                padding 16px 0

            .dashboard-stat
                border-left none
                padding 12px 16px

                &:not(:first-child)
                    border-top 1px solid #e3e7ec

        .dashboard-charts-grid
            display grid
            grid-template-columns repeat(2, minmax(0, 1fr))
            gap 16px

        @media (max-width 768px)
            .dashboard-charts-grid
                grid-template-columns 1fr

        .dashboard-chart-card
            background #fff
            border 1px solid #e3e7ec
            border-radius 10px
            box-shadow 0 1px 2px rgba(0, 0, 0, 0.04)
            padding 16px 18px
            min-width 0
            transition transform 150ms ease, box-shadow 150ms ease

            &:hover
                box-shadow 0 4px 14px rgba(27, 47, 64, 0.06)

            .chart-header
                margin-bottom 12px
                padding-bottom 8px
                border-bottom 1px solid #f1f4f7
                position relative
                z-index 10

            .chart-header-with-controls
                display flex
                justify-content space-between
                align-items center
                flex-wrap wrap
                gap 10px

            .chart-controls
                display flex
                align-items center
                flex-wrap wrap
                gap 8px
                max-width 100%

            .control-group
                display inline-flex
                align-items center
                gap 6px

            .control-label
                font-size 12px
                font-weight 600
                color #4a5568
                margin 0

            .date-range-group
                display inline-flex
                align-items center
                gap 6px
                flex-wrap nowrap
                max-width 100%

            .chart-calendar
                width 145px
                max-width 145px
                min-width 0
                position relative

                .ui.input
                    width 100%

                    input
                        border-color #d4d4d5

            .chart-dropdown.ui.selection.dropdown
                min-width 140px
                border-color #d4d4d5

            .date-sep
                color #64748b
                font-weight 600
                font-size 14px

            .chart-clear-btn
                height 38px
                margin 0 !important

            .chart-title
                margin 0
                font-size 16px
                font-weight 700
                color #1b1b1b
                letter-spacing -0.01em

            .canvas-wrap
                position relative
                height 250px
                width 100%

        .full-width
            grid-column 1 / -1

        .canvas-wrap-launches
            height 480px !important

        .canvas-wrap-expanded
            height 330px !important

        .canvas-wrap-heatmap
            height 380px !important

        @media (max-width 991px)
            .dashboard-chart-card .chart-header-with-controls
                flex-direction column
                align-items flex-start
                gap 10px

            .dashboard-chart-card .chart-controls
                width 100%
                justify-content flex-start

        @media (max-width 768px)
            .canvas-wrap-launches
                height 340px !important
            .canvas-wrap-expanded
                height 260px !important

        @media (max-width 576px)
            .dashboard-chart-card .date-range-group
                flex-wrap wrap

            .dashboard-chart-card .chart-calendar
                width 100%
                max-width 100%
    </style>
</dashboard-charts>