<dashboard-data-explorer>
    <div class="ui segment explorer-card" if="{ (opts.p.filteredCompetitions || []).length > 0 }">
        <div class="explorer-header">
            <h3 class="ui header" style="margin: 0; color: #1b1b1b;">
                Competitions Data Explorer
            </h3>
            <button class="ui green button" onclick="{ downloadTabularCSV }">
                <i class="icon download"></i>Download as CSV
            </button>
        </div>

        <div class="explorer-controls-grid">
            <!-- Row 1: Group by | Metric | Chart Type -->
            <div class="control-item">
                <label>Group by:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customDim1Dropdown">
                    <input type="hidden" name="custom_dim1" value="{ customDim1 }">
                    <i class="dropdown icon"></i>
                    <div class="text">{ getDimLabel(customDim1) }</div>
                    <div class="menu">
                        <div class="item" data-value="competition">Competition</div>
                        <div class="item" data-value="organizer">Organizer</div>
                        <div class="item" data-value="has_reward">Has Reward</div>
                        <div class="item" data-value="created_year">Creation Year</div>
                        <div class="item" data-value="created_month">Creation Month</div>
                        <div class="item" data-value="created_week">Creation Week</div>
                        <div class="item" data-value="created_day">Creation Day</div>
                        <div class="ui divider" if="{ (opts.p.categoriesWithTags || opts.p.availableCategories || []).length > 0 }" style="margin: 4px 0;"></div>
                        <div class="item" each="{ cat in (opts.p.categoriesWithTags || opts.p.availableCategories || []) }" data-value="cat_{ cat }">Tag: { cat }</div>
                    </div>
                </div>
            </div>

            <div class="control-item">
                <label>Metric:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customMetricDropdown">
                    <input type="hidden" name="custom_metric" value="{ customMetric }">
                    <i class="dropdown icon"></i>
                    <div class="text">{ getMetricLabel(customMetric) }</div>
                    <div class="menu">
                        <div class="item" data-value="count">Count of Competitions</div>
                        <div class="item" data-value="participants_sum">Total Participants</div>
                        <div class="item" data-value="participants_avg">Average Participants</div>
                        <div class="item" data-value="submissions_sum">Total Submissions</div>
                        <div class="item" data-value="submissions_avg">Average Submissions</div>
                    </div>
                </div>
            </div>

            <div class="control-item">
                <label>Chart Type:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customTypeDropdown">
                    <input type="hidden" name="custom_type" value="{ customChartType }">
                    <i class="dropdown icon"></i>
                    <div class="text">{ getTypeLabel(customChartType) }</div>
                    <div class="menu">
                        <div class="item" each="{ t in getAvailableChartTypes() }" data-value="{ t.value }">
                            <i class="{ t.icon } icon"></i> { t.label }
                        </div>
                    </div>
                </div>
            </div>

            <!-- Row 2: Split by | Order by | Limit -->
            <div class="control-item">
                <label>Split by:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customSplitByDropdown">
                    <input type="hidden" name="custom_split_by" value="{ customSplitBy }">
                    <i class="dropdown icon"></i>
                    <div class="text">{ getSplitByLabel(customSplitBy) }</div>
                    <div class="menu">
                        <div class="item" each="{ s in getAvailableSplitCategories() }" data-value="{ s.value }">{ s.label }</div>
                    </div>
                </div>
            </div>

            <div class="control-item">
                <label>Order by:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customOrderByDropdown">
                    <input type="hidden" name="custom_order_by" value="{ customOrderBy }">
                    <i class="dropdown icon"></i>
                    <div class="text">{ getOrderByLabel(customOrderBy) }</div>
                    <div class="menu">
                        <div class="item" each="{ o in getAvailableOrderOptions() }" data-value="{ o.value }">{ o.label }</div>
                    </div>
                </div>
            </div>

            <div class="control-item control-item-limit">
                <label>Limit:</label>
                <div class="ui input custom-limit-input">
                    <input type="number" min="1" max="5000" placeholder="All" value="{ customLimitValue }" oninput="{ onCustomLimitInput }">
                </div>
            </div>
        </div>

        <!-- Split By Secondary Categories Selector (visible only when a breakdown is active) -->
        <div class="split-by-pills" if="{ isBreakdownActive && availableSecCategories.length > 0 }">
            <button type="button"
                    class="tag-pill { active: isSecCategorySelected(val) }"
                    each="{ val in availableSecCategories }"
                    onclick="{ toggleSecCategory.bind(this, val) }">
                { val }
            </button>
        </div>

        <!-- Visualization Display: Tabular View (1D) -->
        <div class="custom-tabular-wrap" show="{ customChartType === 'tabular' && !isBreakdownActive }" style="max-height: 420px; margin-top: 14px;">
            <table class="ui celled compact striped table">
                <thead>
                    <tr>
                        <th style="width: 50px; text-align: center;">#</th>
                        <th onclick="{ sortTabular1D.bind(this, 'label') }" style="cursor: pointer; user-select: none;">
                            { getDimLabel(customDim1) }
                            <i class="{ tabular1DSortKey === 'label' ? (tabular1DSortDir === 1 ? 'caret up' : 'caret down') : 'sort' } icon"></i>
                        </th>
                        <th onclick="{ sortTabular1D.bind(this, 'val') }" style="cursor: pointer; user-select: none; text-align: right; width: 220px;">
                            { getMetricLabel(customMetric) }
                            <i class="{ tabular1DSortKey === 'val' ? (tabular1DSortDir === 1 ? 'caret up' : 'caret down') : 'sort' } icon"></i>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr each="{ row, idx in tabularData1D }">
                        <td class="center aligned">{ idx + 1 }</td>
                        <td><strong>{ row.label }</strong></td>
                        <td class="right aligned" style="font-weight: 600;">{ format_number(row.val) }</td>
                    </tr>
                    <tr if="{ !tabularData1D || tabularData1D.length === 0 }">
                        <td colspan="3" class="center aligned table-empty-row">No data available.</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Visualization Display: Tabular View (2D Breakdown) -->
        <div class="custom-tabular-wrap" show="{ customChartType === 'tabular' && isBreakdownActive }" style="max-height: 420px; margin-top: 14px;">
            <table class="ui celled compact striped table">
                <thead>
                    <tr>
                        <th style="width: 50px; text-align: center;">#</th>
                        <th onclick="{ sortTabular2D.bind(this, 'label') }" style="cursor: pointer; user-select: none;">
                            { getDimLabel(customDim1) }
                            <i class="{ tabular2DSortKey === 'label' ? (tabular2DSortDir === 1 ? 'caret up' : 'caret down') : 'sort' } icon"></i>
                        </th>
                        <th each="{ col in tabularCols2D }" onclick="{ sortTabular2D.bind(this, col) }" style="cursor: pointer; user-select: none; text-align: right;">
                            { col }
                            <i class="{ tabular2DSortKey === col ? (tabular2DSortDir === 1 ? 'caret up' : 'caret down') : 'sort' } icon"></i>
                        </th>
                        <th onclick="{ sortTabular2D.bind(this, 'total') }" style="cursor: pointer; user-select: none; text-align: right; width: 120px; background: #f8fafc;">
                            Total
                            <i class="{ tabular2DSortKey === 'total' ? (tabular2DSortDir === 1 ? 'caret up' : 'caret down') : 'sort' } icon"></i>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr each="{ row, idx in tabularRows2D }">
                        <td class="center aligned">{ idx + 1 }</td>
                        <td><strong>{ row.label }</strong></td>
                        <td each="{ col in tabularCols2D }" class="right aligned">{ format_number(row.values[col] || 0) }</td>
                        <td class="right aligned" style="font-weight: bold; background: #f8fafc;">{ format_number(row.total) }</td>
                    </tr>
                    <tr if="{ !tabularRows2D || tabularRows2D.length === 0 }">
                        <td colspan="{ 3 + tabularCols2D.length }" class="center aligned table-empty-row">No data available.</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Visualization Display: Chart Canvas View -->
        <div class="canvas-wrap canvas-wrap-custom" show="{ customChartType !== 'tabular' }" style="height: 380px; position: relative; margin-top: 16px;">
            <canvas id="chCustom" ref="chCustom"></canvas>
        </div>
    </div>

    <script>
        var self = this;
        self.chart = null;

        // Explorer State
        self.customDim1 = 'organizer';
        self.customMetric = 'count';
        self.customSplitBy = 'none';
        self.customChartType = 'horizontalBar';
        self.customOrderBy = 'val_desc';
        self.customLimitValue = 10;
        self.isBreakdownActive = false;

        // Split By Category Selection State
        self.availableSecCategories = [];
        self.availableSecCounts = {};
        self.selectedSplitCategoriesMap = null;
        self.activeBreakdownKey = null;

        // Tabular Data & Sorting State
        self.tabularData1D = [];
        self.tabularRows2D = [];
        self.tabularCols2D = [];
        self.tabular1DSortKey = 'val';
        self.tabular1DSortDir = -1;
        self.tabular2DSortKey = 'total';
        self.tabular2DSortDir = -1;

        var DISTINCT_COLORS = (opts.p && opts.p.DISTINCT_COLORS) || [];
        function getDistinctColors(count) {
            if (opts.p && opts.p.getDistinctColors) return opts.p.getDistinctColors(count);
            return [];
        }

        self.format_number = function (num) {
            return (opts.p && opts.p.format_number) ? opts.p.format_number(num) : Number(num || 0).toLocaleString();
        };

        // Tabular Sorting Methods
        self.sortTabular1D = function (key) {
            if (self.tabular1DSortKey === key) {
                self.tabular1DSortDir *= -1;
            } else {
                self.tabular1DSortKey = key;
                self.tabular1DSortDir = (key === 'val') ? -1 : 1;
            }
            self.applyTabular1DSort();
            self.update();
        };

        self.applyTabular1DSort = function () {
            if (!self.tabularData1D || self.tabularData1D.length === 0) return;
            var k = self.tabular1DSortKey;
            var dir = self.tabular1DSortDir;
            self.tabularData1D.sort(function (a, b) {
                var va = a[k];
                var vb = b[k];
                if (typeof va === 'string') va = va.toLowerCase();
                if (typeof vb === 'string') vb = vb.toLowerCase();
                if (va < vb) return -1 * dir;
                if (va > vb) return 1 * dir;
                return 0;
            });
        };

        self.sortTabular2D = function (key) {
            if (self.tabular2DSortKey === key) {
                self.tabular2DSortDir *= -1;
            } else {
                self.tabular2DSortKey = key;
                self.tabular2DSortDir = (key === 'label') ? 1 : -1;
            }
            self.applyTabular2DSort();
            self.update();
        };

        self.applyTabular2DSort = function () {
            if (!self.tabularRows2D || self.tabularRows2D.length === 0) return;
            var k = self.tabular2DSortKey;
            var dir = self.tabular2DSortDir;
            self.tabularRows2D.sort(function (a, b) {
                var va, vb;
                if (k === 'label') {
                    va = (a.label || '').toLowerCase();
                    vb = (b.label || '').toLowerCase();
                } else if (k === 'total') {
                    va = a.total || 0;
                    vb = b.total || 0;
                } else {
                    va = (a.values && a.values[k]) || 0;
                    vb = (b.values && b.values[k]) || 0;
                }
                if (va < vb) return -1 * dir;
                if (va > vb) return 1 * dir;
                return 0;
            });
        };

        self.downloadTabularCSV = function (e) {
            if (e && e.preventDefault) e.preventDefault();
            var esc = (opts.p && opts.p.escapeCsv) || function (v) { return '"' + String(v || '').replace(/"/g, '""') + '"'; };

            var lines = [];
            if (!self.isBreakdownActive) {
                if (!self.tabularData1D || self.tabularData1D.length === 0) return;
                var h1 = self.getDimLabel(self.customDim1);
                var h2 = self.getMetricLabel(self.customMetric);
                lines.push([esc(h1), esc(h2)].join(","));
                self.tabularData1D.forEach(function (row) {
                    lines.push([esc(row.label), esc(row.val)].join(","));
                });
            } else {
                if (!self.tabularRows2D || self.tabularRows2D.length === 0) return;
                var h1 = self.getDimLabel(self.customDim1);
                var headers = [esc(h1)];
                (self.tabularCols2D || []).forEach(function (col) {
                    headers.push(esc(col));
                });
                headers.push(esc("Total (" + self.getMetricLabel(self.customMetric) + ")"));
                lines.push(headers.join(","));

                self.tabularRows2D.forEach(function (row) {
                    var rowData = [esc(row.label)];
                    (self.tabularCols2D || []).forEach(function (col) {
                        rowData.push(esc(row.values[col] || 0));
                    });
                    rowData.push(esc(row.total || 0));
                    lines.push(rowData.join(","));
                });
            }

            var dim1Name = String(self.customDim1 || "dim1").replace(/[^a-zA-Z0-9_]/g, "_");
            var metricName = String(self.customMetric || "metric").replace(/[^a-zA-Z0-9_]/g, "_");
            var splitName = self.isBreakdownActive ? ("_" + String(self.customSplitBy || "split").replace(/[^a-zA-Z0-9_]/g, "_")) : "";
            var filename = "codabench_explorer_" + dim1Name + "_" + metricName + splitName + ".csv";

            if (opts.p && opts.p.downloadCsv) {
                opts.p.downloadCsv(filename, lines);
            }
        };

        self.getAvailableChartTypes = function () {
            var dim1 = self.customDim1 || "organizer";
            var metricKey = self.customMetric || "count";
            var isBreakdown = Boolean(self.customSplitBy && self.customSplitBy !== 'none');
            var isDate = isDateDim(dim1);
            var isAvg = metricKey.indexOf('_avg') !== -1;

            if (isBreakdown) {
                if (isDate) {
                    return [
                        { value: "line", label: "Line", icon: "chart line" },
                        { value: "bar", label: "Vertical Bar", icon: "chart bar" },
                        { value: "horizontalBar", label: "Horizontal Bar", icon: "bars" },
                        { value: "tabular", label: "Tabular", icon: "table" }
                    ];
                }
                return [
                    { value: "horizontalBar", label: "Horizontal Bar", icon: "bars" },
                    { value: "bar", label: "Vertical Bar", icon: "chart bar" },
                    { value: "line", label: "Line", icon: "chart line" },
                    { value: "tabular", label: "Tabular", icon: "table" }
                ];
            }

            // In 1D mode:
            // 1. If Date dimension: Line and Bar charts are appropriate; Pie charts are mathematically & visually irrelevant.
            if (isDate) {
                return [
                    { value: "line", label: "Line", icon: "chart line" },
                    { value: "bar", label: "Vertical Bar", icon: "chart bar" },
                    { value: "horizontalBar", label: "Horizontal Bar", icon: "bars" },
                    { value: "tabular", label: "Tabular", icon: "table" }
                ];
            }

            // 2. If Nominal dimension:
            // Pie/Doughnut represents parts of a whole (composition).
            // It is only relevant when:
            // - Metric is an additive sum/count, NOT an average (!isAvg)
            // - Dimension is not individual competition items (dim1 !== 'competition')
            var canShowPie = (dim1 !== 'competition') && !isAvg;

            var types = [
                { value: "horizontalBar", label: "Horizontal Bar", icon: "bars" },
                { value: "bar", label: "Vertical Bar", icon: "chart bar" }
            ];

            if (canShowPie) {
                types.push({ value: "doughnut", label: "Doughnut / Pie", icon: "chart pie" });
            }

            if (dim1 !== "has_reward") {
                types.push({ value: "line", label: "Line", icon: "chart line" });
            }

            types.push({ value: "tabular", label: "Tabular", icon: "table" });
            return types;
        };

        self.getAvailableSplitCategories = function () {
            var dim1 = self.customDim1 || "organizer";
            var items = [{ value: "none", label: "None" }];
            if (dim1 !== "has_reward") {
                items.push({ value: "has_reward", label: "Reward" });
            }
            var cats = (opts.p && (opts.p.categoriesWithTags || opts.p.availableCategories)) || [];
            cats.forEach(function (cat) {
                if (dim1 !== "cat_" + cat) {
                    items.push({ value: "cat_" + cat, label: "Tag: " + cat });
                }
            });
            return items;
        };

        self.getAvailableOrderOptions = function () {
            var dim = self.customDim1 || 'organizer';
            if (isDateDim(dim)) {
                return [
                    { value: 'date_asc', label: 'Date (Ascending)' },
                    { value: 'date_desc', label: 'Date (Descending)' },
                    { value: 'val_desc', label: 'Metric Value (Descending)' },
                    { value: 'val_asc', label: 'Metric Value (Ascending)' }
                ];
            }
            if (dim === 'has_reward') {
                return [
                    { value: 'val_desc', label: 'Metric Value (Descending)' },
                    { value: 'val_asc', label: 'Metric Value (Ascending)' }
                ];
            }
            return [
                { value: 'val_desc', label: 'Metric Value (Descending)' },
                { value: 'val_asc', label: 'Metric Value (Ascending)' },
                { value: 'name_asc', label: 'Alphabetical (Ascending)' },
                { value: 'name_desc', label: 'Alphabetical (Descending)' }
            ];
        };

        self.getOrderByLabel = function (val) {
            var orderOpts = self.getAvailableOrderOptions();
            for (var i = 0; i < orderOpts.length; i++) {
                if (orderOpts[i].value === val) return orderOpts[i].label;
            }
            return (orderOpts[0] && orderOpts[0].label) || '';
        };

        self.getMetricLabel = function (val) {
            if (val === 'count') return 'Count of Competitions';
            if (val === 'participants_sum') return 'Total Participants';
            if (val === 'participants_avg') return 'Average Participants';
            if (val === 'submissions_sum') return 'Total Submissions';
            if (val === 'submissions_avg') return 'Average Submissions';
            return val || '';
        };

        self.getSplitByLabel = function (val) {
            if (!val || val === 'none') return 'None';
            if (val === 'has_reward') return 'Reward';
            if (val.indexOf('cat_') === 0) return 'Tag: ' + val.substring(4);
            return val;
        };

        // Split By Secondary Categories Selection Methods
        self.isSecCategorySelected = function (val) {
            return self.selectedSplitCategoriesMap ? Boolean(self.selectedSplitCategoriesMap[val]) : false;
        };

        self.toggleSecCategory = function (val, e) {
            if (e && e.preventDefault) e.preventDefault();
            if (e && e.currentTarget && e.currentTarget.blur) e.currentTarget.blur();
            if (!self.selectedSplitCategoriesMap) {
                self.selectedSplitCategoriesMap = {};
                (self.availableSecCategories || []).forEach(function (k) {
                    self.selectedSplitCategoriesMap[k] = true;
                });
            }
            if (self.selectedSplitCategoriesMap[val]) {
                delete self.selectedSplitCategoriesMap[val];
            } else {
                self.selectedSplitCategoriesMap[val] = true;
            }
            self.renderCustomChart();
            self.update();
        };

        self.getDimLabel = function (val) {
            if (!val) return "";
            if (val === 'competition') return 'Competition';
            if (val === 'organizer') return 'Organizer';
            if (val === 'has_reward') return 'Has Reward';
            if (val === 'created_year') return 'Creation Year';
            if (val === 'created_month') return 'Creation Month';
            if (val === 'created_week') return 'Creation Week';
            if (val === 'created_day') return 'Creation Day';
            if (val.indexOf('cat_') === 0) return 'Tag: ' + val.substring(4);
            if (val === 'count') return 'Count of Competitions';
            if (val === 'participants_sum') return 'Total Participants';
            if (val === 'participants_avg') return 'Average Participants';
            if (val === 'submissions_sum') return 'Total Submissions';
            if (val === 'submissions_avg') return 'Average Submissions';
            if (val === 'breakdown_has_reward') return 'Split by Reward';
            if (val.indexOf('breakdown_cat_') === 0) return 'Split by ' + val.substring(14);
            return val;
        };

        self.getTypeLabel = function (val) {
            if (val === 'horizontalBar') return 'Horizontal Bar';
            if (val === 'bar') return 'Vertical Bar';
            if (val === 'line') return 'Line';
            if (val === 'doughnut') return 'Doughnut / Pie';
            if (val === 'tabular') return 'Tabular';
            return val;
        };

        self.getEffectiveLimit = function () {
            if (self.customLimitValue === '' || self.customLimitValue === null || self.customLimitValue === undefined) {
                return Infinity;
            }
            var n = parseInt(self.customLimitValue, 10);
            return (!isNaN(n) && n > 0) ? n : Infinity;
        };

        self.onCustomLimitInput = function (e) {
            self.customLimitValue = e.target.value;
            self.renderCustomChart();
            if (self.customChartType === 'tabular') {
                self.update();
            }
        };

        function isDateDim(dim) {
            return dim && dim.indexOf("created_") === 0;
        }

        function getISOWeekString(d) {
            var target = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
            var dayNum = target.getUTCDay() || 7;
            target.setUTCDate(target.getUTCDate() + 4 - dayNum);
            var yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
            var weekNo = Math.ceil((((target - yearStart) / 86400000) + 1) / 7);
            var wStr = weekNo < 10 ? "0" + weekNo : String(weekNo);
            return target.getUTCFullYear() + "-W" + wStr;
        }

        function extractValues(comp, dim) {
            if (dim === "competition") return [comp.title || ("Competition #" + comp.id) || "Unknown"];
            if (dim === "organizer") return [comp.organizer || "Unknown"];
            if (dim === "has_reward") return [comp.has_reward ? "Reward" : "No Reward"];
            if (isDateDim(dim)) {
                if (!comp.created_when) return ["Unknown"];
                var d = new Date(comp.created_when);
                if (isNaN(d.getTime())) return ["Unknown"];
                if (dim === "created_year") return [d.getUTCFullYear().toString()];
                if (dim === "created_month") {
                    var m = ("0" + (d.getUTCMonth() + 1)).slice(-2);
                    return [d.getUTCFullYear() + "-" + m];
                }
                if (dim === "created_week") {
                    return [getISOWeekString(d)];
                }
                if (dim === "created_day") {
                    var m2 = ("0" + (d.getUTCMonth() + 1)).slice(-2);
                    var day = ("0" + d.getUTCDate()).slice(-2);
                    return [d.getUTCFullYear() + "-" + m2 + "-" + day];
                }
            }
            if (dim.indexOf("cat_") === 0) {
                var catName = dim.substring(4);
                var tags = (comp.tagsByCategory && comp.tagsByCategory[catName]) || [];
                return tags.length > 0 ? tags : ["(No Tag)"];
            }
            return ["All"];
        }

        function computeMetricValue(stats, metricKey) {
            if (!stats || !stats.count) return 0;
            if (metricKey === "count") return stats.count;
            if (metricKey === "participants_sum") return stats.participants;
            if (metricKey === "participants_avg") return Math.round(stats.participants / stats.count);
            if (metricKey === "submissions_sum") return stats.submissions;
            if (metricKey === "submissions_avg") return Math.round(stats.submissions / stats.count);
            return stats.count;
        }

        self.renderCustomChart = function () {
            if (!opts.p || opts.p.activeTab !== 'explorer') {
                if (self.chart) {
                    self.chart.destroy();
                    self.chart = null;
                }
                return;
            }
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var dim1 = self.customDim1 || "organizer";
            var metricKey = self.customMetric || "count";
            var splitBy = self.customSplitBy || "none";
            var chartType = self.customChartType || "horizontalBar";
            var limit = self.getEffectiveLimit();
            var isBreakdown = Boolean(splitBy && splitBy !== "none");
            self.isBreakdownActive = isBreakdown;

            if (!isBreakdown) {
                self.availableSecCategories = [];
                self.availableSecCounts = {};
            }

            if (rows.length === 0) {
                self.tabularData1D = [];
                self.tabularRows2D = [];
                self.tabularCols2D = [];
                if (self.chart) {
                    self.chart.destroy();
                    self.chart = null;
                }
                return;
            }

            var avTypes = self.getAvailableChartTypes().map(function (t) { return t.value; });
            if (!avTypes.includes(chartType)) {
                chartType = avTypes[0] || "horizontalBar";
                self.customChartType = chartType;
            }

            var metricLabel = self.getMetricLabel(metricKey);

            if (!isBreakdown) {
                var groups = {};
                rows.forEach(function (c) {
                    var vals = extractValues(c, dim1);
                    vals.forEach(function (v) {
                        if (!groups[v]) groups[v] = { count: 0, participants: 0, submissions: 0 };
                        groups[v].count += 1;
                        groups[v].participants += (c.participants_count || 0);
                        groups[v].submissions += (c.submissions_count || 0);
                    });
                });

                var entries = Object.keys(groups).map(function (k) {
                    var g = groups[k];
                    var val = computeMetricValue(g, metricKey);
                    return { key: k, val: val };
                });

                var avOrders1D = self.getAvailableOrderOptions().map(function (o) { return o.value; });
                var order = self.customOrderBy;
                if (!avOrders1D.includes(order)) {
                    order = avOrders1D[0] || (isDateDim(dim1) ? 'date_asc' : 'val_desc');
                    self.customOrderBy = order;
                }

                entries.sort(function (a, b) {
                    if (order === 'date_asc') {
                        if (a.key < b.key) return -1;
                        if (a.key > b.key) return 1;
                        return 0;
                    }
                    if (order === 'date_desc') {
                        if (a.key < b.key) return 1;
                        if (a.key > b.key) return -1;
                        return 0;
                    }
                    if (order === 'name_asc') {
                        return a.key.localeCompare(b.key, undefined, { sensitivity: 'base', numeric: true });
                    }
                    if (order === 'name_desc') {
                        return b.key.localeCompare(a.key, undefined, { sensitivity: 'base', numeric: true });
                    }
                    if (order === 'val_asc') {
                        if (a.val !== b.val) return a.val - b.val;
                        return a.key.localeCompare(b.key);
                    }
                    // default 'val_desc'
                    if (a.val !== b.val) return b.val - a.val;
                    return a.key.localeCompare(b.key);
                });

                if (limit !== Infinity) {
                    entries = entries.slice(0, limit);
                }

                // Populate 1D Tabular Data
                self.tabularData1D = entries.map(function (e) {
                    return { label: e.key, val: e.val };
                });
                self.applyTabular1DSort();

                if (chartType === "tabular") {
                    if (self.chart) {
                        self.chart.destroy();
                        self.chart = null;
                    }
                    return;
                }

                var el = self.refs.chCustom || document.getElementById("chCustom");
                if (!el) return;

                var fullLabels = entries.map(function (e) { return e.key; });
                var labels = entries.map(function (e) {
                    return e.key.length > 30 ? e.key.substring(0, 27) + "..." : e.key;
                });
                var dataVals = entries.map(function (e) { return e.val; });

                var tooltipOpt = {
                    callbacks: {
                        title: function (tooltipItems) {
                            if (!tooltipItems || tooltipItems.length === 0) return "";
                            var idx = tooltipItems[0].index;
                            return fullLabels[idx] || tooltipItems[0].label || "";
                        }
                    }
                };

                var config = null;
                if (chartType === "horizontalBar" || chartType === "bar") {
                    config = {
                        type: chartType,
                        data: {
                            labels: labels,
                            datasets: [{ label: metricLabel, data: dataVals, backgroundColor: DISTINCT_COLORS[0], borderWidth: 0 }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            legend: { display: false },
                            tooltips: tooltipOpt,
                            scales: chartType === "horizontalBar" ? {
                                xAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                yAxes: [{
                                    gridLines: { display: false },
                                    ticks: {
                                        fontSize: 11,
                                        fontColor: "#334155",
                                        callback: function (val, idx, vals) {
                                            if (!vals || vals.length <= 36) return val;
                                            var step = Math.ceil(vals.length / 36);
                                            return (idx % step === 0 || idx === vals.length - 1) ? val : "";
                                        }
                                    }
                                }]
                            } : {
                                yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: true, autoSkipPadding: 8, maxTicksLimit: 36, maxRotation: 45, minRotation: 0, fontSize: 11, fontColor: "#334155" } }]
                            }
                        }
                    };
                } else if (chartType === "line") {
                    config = {
                        type: "line",
                        data: {
                            labels: labels,
                            datasets: [{
                                label: metricLabel,
                                data: dataVals,
                                borderColor: DISTINCT_COLORS[0],
                                backgroundColor: "rgba(33, 133, 208, 0.12)",
                                borderWidth: 2.5,
                                fill: true,
                                lineTension: 0
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            legend: { display: false },
                            tooltips: tooltipOpt,
                            elements: { line: { tension: 0 } },
                            scales: {
                                yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: true, autoSkipPadding: 8, maxTicksLimit: 36, maxRotation: 45, minRotation: 0, fontSize: 11, fontColor: "#334155" } }]
                            }
                        }
                    };
                } else {
                    config = {
                        type: chartType,
                        data: {
                            labels: labels,
                            datasets: [{
                                data: dataVals,
                                backgroundColor: getDistinctColors(labels.length)
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            legend: {
                                display: true,
                                position: "right",
                                labels: {
                                    boxWidth: 10,
                                    fontSize: 10,
                                    padding: 4,
                                    generateLabels: function (chart) {
                                        var data = chart.data;
                                        if (data.labels && data.labels.length && data.datasets && data.datasets.length) {
                                            var ds = data.datasets[0];
                                            var items = data.labels.map(function (label, i) {
                                                var meta = chart.getDatasetMeta(0);
                                                var arc = (meta && meta.data && meta.data[i]) || {};
                                                var custom = arc.custom || {};
                                                var fill = custom.backgroundColor || (ds.backgroundColor && (Array.isArray(ds.backgroundColor) ? ds.backgroundColor[i] : ds.backgroundColor)) || "#999";
                                                var stroke = custom.borderColor || (ds.borderColor && (Array.isArray(ds.borderColor) ? ds.borderColor[i] : ds.borderColor)) || "#fff";
                                                var bw = custom.borderWidth !== undefined ? custom.borderWidth : (ds.borderWidth !== undefined ? ds.borderWidth : 0);
                                                var shortLabel = label.length > 20 ? label.substring(0, 18) + "..." : label;
                                                return {
                                                    text: shortLabel + " (" + (ds.data[i] || 0) + ")",
                                                    fillStyle: fill,
                                                    strokeStyle: stroke,
                                                    lineWidth: bw,
                                                    hidden: isNaN(ds.data[i]) || (arc && arc.hidden),
                                                    index: i
                                                };
                                            });
                                            return items.slice(0, 36);
                                        }
                                        return [];
                                    }
                                }
                            },
                            tooltips: tooltipOpt
                        }
                    };
                }

                if (self.chart && self.chart.config && self.chart.config.type === chartType && self.chart.ctx && self.chart.ctx.canvas === el) {
                    self.chart.data.labels = config.data.labels;
                    self.chart.data.datasets = config.data.datasets;
                    self.chart.options = config.options;
                    self.chart.update();
                } else {
                    if (self.chart) self.chart.destroy();
                    self.chart = new Chart(el, config);
                }
            } else {
                var secDimKey = splitBy;
                var matrix = {};
                var primaryStats = {};
                var secStats = {};

                rows.forEach(function (c) {
                    var pVals = extractValues(c, dim1);
                    var sVals = extractValues(c, secDimKey);
                    var pCount = c.participants_count || 0;
                    var sCount = c.submissions_count || 0;

                    pVals.forEach(function (p) {
                        if (!matrix[p]) matrix[p] = {};
                        if (!primaryStats[p]) primaryStats[p] = { count: 0, participants: 0, submissions: 0 };
                        primaryStats[p].count += 1;
                        primaryStats[p].participants += pCount;
                        primaryStats[p].submissions += sCount;

                        sVals.forEach(function (s) {
                            if (!matrix[p][s]) matrix[p][s] = { count: 0, participants: 0, submissions: 0 };
                            matrix[p][s].count += 1;
                            matrix[p][s].participants += pCount;
                            matrix[p][s].submissions += sCount;

                            if (!secStats[s]) secStats[s] = { count: 0, participants: 0, submissions: 0 };
                            secStats[s].count += 1;
                            secStats[s].participants += pCount;
                            secStats[s].submissions += sCount;
                        });
                    });
                });

                var avOrders2D = self.getAvailableOrderOptions().map(function (o) { return o.value; });
                var order = self.customOrderBy;
                if (!avOrders2D.includes(order)) {
                    order = avOrders2D[0] || (isDateDim(dim1) ? 'date_asc' : 'val_desc');
                    self.customOrderBy = order;
                }

                var sortedPrimaries = Object.keys(primaryStats);
                sortedPrimaries.sort(function (a, b) {
                    if (order === 'date_asc') {
                        if (a < b) return -1;
                        if (a > b) return 1;
                        return 0;
                    }
                    if (order === 'date_desc') {
                        if (a < b) return 1;
                        if (a > b) return -1;
                        return 0;
                    }
                    if (order === 'name_asc') {
                        return a.localeCompare(b, undefined, { sensitivity: 'base', numeric: true });
                    }
                    if (order === 'name_desc') {
                        return b.localeCompare(a, undefined, { sensitivity: 'base', numeric: true });
                    }
                    var va = computeMetricValue(primaryStats[a], metricKey);
                    var vb = computeMetricValue(primaryStats[b], metricKey);
                    if (order === 'val_asc') {
                        if (va !== vb) return va - vb;
                        return a.localeCompare(b);
                    }
                    // default 'val_desc'
                    if (va !== vb) return vb - va;
                    return a.localeCompare(b);
                });

                if (limit !== Infinity) {
                    sortedPrimaries = sortedPrimaries.slice(0, limit);
                }

                var allSecondaries = Object.keys(secStats).sort(function (a, b) {
                    var sa = computeMetricValue(secStats[a], metricKey);
                    var sb = computeMetricValue(secStats[b], metricKey);
                    if (sb !== sa) return sb - sa;
                    return a.localeCompare(b);
                });

                self.availableSecCategories = allSecondaries;
                self.availableSecCounts = secStats;

                if (!self.selectedSplitCategoriesMap || self.activeBreakdownKey !== secDimKey) {
                    self.activeBreakdownKey = secDimKey;
                    self.selectedSplitCategoriesMap = {};
                    var defaultCount = allSecondaries.length <= 8 ? allSecondaries.length : 8;
                    allSecondaries.slice(0, defaultCount).forEach(function (s) {
                        self.selectedSplitCategoriesMap[s] = true;
                    });
                }

                var sortedSecondaries = allSecondaries.filter(function (s) {
                    return self.selectedSplitCategoriesMap && self.selectedSplitCategoriesMap[s];
                });

                if (sortedSecondaries.length === 0 && allSecondaries.length > 0) {
                    sortedSecondaries = [allSecondaries[0]];
                    self.selectedSplitCategoriesMap[allSecondaries[0]] = true;
                }

                // Populate 2D Tabular Data
                var isAvgMetric = metricKey.indexOf('_avg') !== -1;
                self.tabularCols2D = sortedSecondaries;
                self.tabularRows2D = sortedPrimaries.map(function (p) {
                    var rowVals = {};
                    var total = 0;
                    sortedSecondaries.forEach(function (s) {
                        var v = computeMetricValue(matrix[p] && matrix[p][s], metricKey);
                        rowVals[s] = v;
                        if (!isAvgMetric) {
                            total += v;
                        }
                    });
                    if (isAvgMetric) {
                        total = computeMetricValue(primaryStats[p], metricKey);
                    }
                    return { label: p, values: rowVals, total: total };
                });
                self.applyTabular2DSort();

                if (chartType === "tabular") {
                    if (self.chart) {
                        self.chart.destroy();
                        self.chart = null;
                    }
                    return;
                }

                var el = self.refs.chCustom || document.getElementById("chCustom");
                if (!el) return;

                var labels = sortedPrimaries.map(function (p) {
                    return p.length > 30 ? p.substring(0, 27) + "..." : p;
                });

                var datasets = sortedSecondaries.map(function (sVal, sIdx) {
                    var dataArr = sortedPrimaries.map(function (p) {
                        return computeMetricValue(matrix[p] && matrix[p][sVal], metricKey);
                    });
                    return {
                        label: sVal,
                        data: dataArr,
                        backgroundColor: DISTINCT_COLORS[sIdx % DISTINCT_COLORS.length],
                        borderColor: DISTINCT_COLORS[sIdx % DISTINCT_COLORS.length],
                        borderWidth: chartType === "line" ? 2 : 0,
                        fill: chartType === "line" ? false : undefined,
                        lineTension: 0
                    };
                });

                var effType = chartType;
                var config = {
                    type: effType,
                    data: { labels: labels, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: { position: "top", labels: { boxWidth: 12, fontSize: 11 } },
                        elements: { line: { tension: 0 } },
                        tooltips: {
                            callbacks: {
                                title: function (tooltipItems) {
                                    if (!tooltipItems || tooltipItems.length === 0) return "";
                                    var idx = tooltipItems[0].index;
                                    return sortedPrimaries[idx] || tooltipItems[0].label || "";
                                }
                            }
                        },
                        scales: effType === "horizontalBar" ? {
                            xAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                            yAxes: [{
                                gridLines: { display: false },
                                ticks: {
                                    fontSize: 11,
                                    fontColor: "#334155",
                                    callback: function (val, idx, vals) {
                                        if (!vals || vals.length <= 36) return val;
                                        var step = Math.ceil(vals.length / 36);
                                        return (idx % step === 0 || idx === vals.length - 1) ? val : "";
                                    }
                                }
                            }]
                        } : {
                            yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                            xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: true, autoSkipPadding: 8, maxTicksLimit: 36, maxRotation: 45, minRotation: 0, fontSize: 11, fontColor: "#334155" } }]
                        }
                    }
                };

                if (self.chart && self.chart.config && self.chart.config.type === effType && self.chart.ctx && self.chart.ctx.canvas === el) {
                    self.chart.data.labels = config.data.labels;
                    self.chart.data.datasets = config.data.datasets;
                    self.chart.options = config.options;
                    self.chart.update();
                } else {
                    if (self.chart) self.chart.destroy();
                    self.chart = new Chart(el, config);
                }
            }
        };

        function initCustomDropdowns() {
            var drops = [
                {
                    ref: 'customDim1Dropdown',
                    getVal: function () { return self.customDim1; },
                    setVal: function (v) {
                        self.customDim1 = v;
                        self.selectedSplitCategoriesMap = null;
                        self.activeBreakdownKey = null;

                        if (isDateDim(v)) {
                            self.customOrderBy = 'date_asc';
                        } else {
                            self.customOrderBy = 'val_desc';
                        }
                        if (self.refs.customOrderByDropdown) {
                            $(self.refs.customOrderByDropdown).dropdown('set selected', self.customOrderBy);
                        }

                        if (v === 'competition' && self.customMetric === 'count') {
                            self.customMetric = 'participants_sum';
                            if (self.refs.customMetricDropdown) {
                                $(self.refs.customMetricDropdown).dropdown('set selected', 'participants_sum');
                            }
                        }

                        if (self.customSplitBy === v) {
                            self.customSplitBy = 'none';
                            if (self.refs.customSplitByDropdown) {
                                $(self.refs.customSplitByDropdown).dropdown('set selected', 'none');
                            }
                        }

                        var avTypes = self.getAvailableChartTypes().map(function (t) { return t.value; });
                        if (!avTypes.includes(self.customChartType)) {
                            self.customChartType = avTypes[0] || "horizontalBar";
                            if (self.refs.customTypeDropdown) {
                                $(self.refs.customTypeDropdown).dropdown('set selected', self.customChartType);
                            }
                        }

                        self.renderCustomChart();
                        self.update();
                    }
                },
                {
                    ref: 'customMetricDropdown',
                    getVal: function () { return self.customMetric; },
                    setVal: function (v) {
                        self.customMetric = v;
                        var avTypes = self.getAvailableChartTypes().map(function (t) { return t.value; });
                        if (!avTypes.includes(self.customChartType)) {
                            self.customChartType = avTypes[0] || "horizontalBar";
                            if (self.refs.customTypeDropdown) {
                                $(self.refs.customTypeDropdown).dropdown('set selected', self.customChartType);
                            }
                        }
                        self.renderCustomChart();
                        self.update();
                    }
                },
                {
                    ref: 'customSplitByDropdown',
                    getVal: function () { return self.customSplitBy; },
                    setVal: function (v) {
                        self.customSplitBy = v;
                        self.selectedSplitCategoriesMap = null;
                        self.activeBreakdownKey = null;

                        var avTypes = self.getAvailableChartTypes().map(function (t) { return t.value; });
                        if (!avTypes.includes(self.customChartType)) {
                            self.customChartType = avTypes[0] || "horizontalBar";
                            if (self.refs.customTypeDropdown) {
                                $(self.refs.customTypeDropdown).dropdown('set selected', self.customChartType);
                            }
                        }

                        self.renderCustomChart();
                        self.update();
                    }
                },
                {
                    ref: 'customOrderByDropdown',
                    getVal: function () { return self.customOrderBy; },
                    setVal: function (v) {
                        self.customOrderBy = v;
                        self.renderCustomChart();
                        self.update();
                    }
                },
                {
                    ref: 'customTypeDropdown',
                    getVal: function () { return self.customChartType; },
                    setVal: function (v) {
                        self.customChartType = v;
                        self.renderCustomChart();
                        self.update();
                    }
                }
            ];

            if (opts.p && opts.p.initDropdowns) {
                opts.p.initDropdowns(self, drops);
            }
        }

        self.on('mount', function () {
            initCustomDropdowns();
            if (opts.p && opts.p.activeTab === 'explorer') {
                self.renderCustomChart();
            }
        });

        self.on('updated', function () {
            if (opts.p && opts.p.activeTab === 'explorer') {
                initCustomDropdowns();
                self.renderCustomChart();
            } else if (self.chart) {
                self.chart.destroy();
                self.chart = null;
            }
        });

        self.on('unmount', function () {
            if (self.chart) {
                self.chart.destroy();
                self.chart = null;
            }
        });
    </script>
</dashboard-data-explorer>
