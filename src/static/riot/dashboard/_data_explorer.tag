<dashboard-data-explorer>
    <div class="ui segment explorer-card" if="{ (opts.p.filteredCompetitions || []).length > 0 }">
        <div class="explorer-header">
            <h3 class="ui header" style="margin: 0; color: #1b1b1b;">
                Data Explorer
            </h3>
        </div>

        <div class="explorer-controls-grid">
            <div class="control-item">
                <label>Group by:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customDim1Dropdown">
                    <input type="hidden" name="custom_dim1" value="{ customDim1 }">
                    <div class="text">{ getDimLabel(customDim1) }</div>
                    <i class="dropdown icon"></i>
                    <div class="menu">
                        <div class="item" data-value="organizer">Organizer</div>
                        <div class="item" data-value="has_reward">Has Reward</div>
                        <div class="item" data-value="created_year">Creation Year</div>
                        <div class="ui divider" if="{ (opts.p.categoriesWithTags || opts.p.availableCategories || []).length > 0 }" style="margin: 4px 0;"></div>
                        <div class="item" each="{ cat in (opts.p.categoriesWithTags || opts.p.availableCategories || []) }" data-value="cat_{ cat }">Tag: { cat }</div>
                    </div>
                </div>
            </div>

            <div class="control-item">
                <label>Metric / Split by:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customDim2Dropdown">
                    <input type="hidden" name="custom_dim2" value="{ customDim2 }">
                    <div class="text">{ getDimLabel(customDim2) }</div>
                    <i class="dropdown icon"></i>
                    <div class="menu">
                        <div class="item" data-value="count">Count of Competitions</div>
                        <div class="item" data-value="participants_sum">Total Participants</div>
                        <div class="item" data-value="participants_avg">Average Participants</div>
                        <div class="item" data-value="submissions_sum">Total Submissions</div>
                        <div class="item" data-value="submissions_avg">Average Submissions</div>
                        <div class="ui divider" if="{ getAvailableBreakdowns().length > 0 }" style="margin: 4px 0;"></div>
                        <div class="item" each="{ b in getAvailableBreakdowns() }" data-value="{ b.value }">{ b.label }</div>
                    </div>
                </div>
            </div>

            <div class="control-item">
                <label>Chart Type:</label>
                <div class="ui selection dropdown custom-dropdown" ref="customTypeDropdown">
                    <input type="hidden" name="custom_type" value="{ customChartType }">
                    <div class="text">{ getTypeLabel(customChartType) }</div>
                    <i class="dropdown icon"></i>
                    <div class="menu">
                        <div class="item" each="{ t in getAvailableChartTypes() }" data-value="{ t.value }">
                            <i class="{ t.icon } icon"></i> { t.label }
                        </div>
                    </div>
                </div>
            </div>

            <div class="control-item control-item-limit">
                <label>Limit:</label>
                <div class="custom-limit-group">
                    <div class="ui selection dropdown custom-dropdown" ref="customLimitDropdown">
                        <input type="hidden" name="custom_limit" value="{ customLimit }">
                        <div class="text">{ getLimitLabel(customLimit) }</div>
                        <i class="dropdown icon"></i>
                        <div class="menu">
                            <div class="item" data-value="5">Top 5</div>
                            <div class="item" data-value="10">Top 10</div>
                            <div class="item" data-value="15">Top 15</div>
                            <div class="item" data-value="25">Top 25</div>
                            <div class="item" data-value="50">Top 50</div>
                            <div class="ui divider" style="margin: 4px 0;"></div>
                            <div class="item" data-value="none">None (All)</div>
                            <div class="item" data-value="custom">Custom...</div>
                        </div>
                    </div>
                    <div class="ui input small custom-limit-input" if="{ customLimit === 'custom' }">
                        <input type="number" min="1" max="5000" placeholder="20" value="{ customLimitValue }" oninput="{ onCustomLimitInput }">
                    </div>
                </div>
            </div>
        </div>

        <!-- Split By Secondary Categories Selector (visible only when a breakdown is active) -->
        <div class="split-by-subcontrols" if="{ isBreakdownActive && availableSecCategories.length > 0 }">
            <div class="split-by-header">
                <span class="split-by-title">
                    <i class="tags icon"></i>
                    Categories in Split by <strong>{ getDimLabel(customDim2).replace('Split by ', '') }</strong>
                    <span class="split-by-count">({ getSelectedSecCount() } of { availableSecCategories.length } selected)</span>
                </span>
                <div class="split-by-actions">
                    <button type="button" class="ui mini basic compact button" onclick="{ selectAllSplitCategories }">All</button>
                    <button type="button" class="ui mini basic compact button" if="{ availableSecCategories.length > 5 }" onclick="{ selectTop5SplitCategories }">Top 5</button>
                    <button type="button" class="ui mini basic compact button" if="{ availableSecCategories.length > 10 }" onclick="{ selectTop10SplitCategories }">Top 10</button>
                    <button type="button" class="ui mini basic compact button" onclick="{ clearSplitCategories }">Reset</button>
                </div>
            </div>
            <div class="split-by-pills">
                <button type="button"
                        class="tag-pill { active: isSecCategorySelected(val) }"
                        each="{ val in availableSecCategories }"
                        onclick="{ toggleSecCategory.bind(this, val) }">
                    <span class="tag-pill-name">{ val }</span>
                    <span class="tag-pill-count">{ getSecCategoryCount(val) }</span>
                </button>
            </div>
        </div>

        <!-- Tabular Top Bar / Actions (when tabular view is selected) -->
        <div class="table-top-bar tabular-top-bar" show="{ customChartType === 'tabular' }">
            <h4 class="ui sub header" style="margin: 0; color: #4a5568; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                Tabular View &middot; { !isBreakdownActive ? (tabularData1D || []).length + ' rows' : (tabularRows2D || []).length + ' rows × ' + (tabularCols2D || []).length + ' cols' }
            </h4>
            <button class="ui green button" onclick="{ downloadTabularCSV }">
                <i class="icon download"></i>Download as CSV
            </button>
        </div>

        <!-- Visualization Display: Tabular View (1D) -->
        <div class="custom-tabular-wrap" show="{ customChartType === 'tabular' && !isBreakdownActive }" style="max-height: 420px; margin-top: 8px;">
            <table class="ui celled compact striped table">
                <thead>
                    <tr>
                        <th style="width: 50px; text-align: center;">#</th>
                        <th onclick="{ sortTabular1D.bind(this, 'label') }" style="cursor: pointer; user-select: none;">
                            { getDimLabel(customDim1) }
                            <i class="{ tabular1DSortKey === 'label' ? (tabular1DSortDir === 1 ? 'caret up' : 'caret down') : 'sort' } icon"></i>
                        </th>
                        <th onclick="{ sortTabular1D.bind(this, 'val') }" style="cursor: pointer; user-select: none; text-align: right; width: 220px;">
                            { getDimLabel(customDim2) }
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
                        <td colspan="3" class="center aligned" style="color: #888;">No data available.</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Visualization Display: Tabular View (2D Breakdown) -->
        <div class="custom-tabular-wrap" show="{ customChartType === 'tabular' && isBreakdownActive }" style="max-height: 420px; margin-top: 8px;">
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
                        <td colspan="{ 3 + tabularCols2D.length }" class="center aligned" style="color: #888;">No data available.</td>
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
        self.customDim2 = 'count';
        self.customChartType = 'horizontalBar';
        self.customLimit = '10';
        self.customLimitValue = 20;
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

        var PALETTE = ["#2185d0", "#00b5ad", "#21ba45", "#fbbd08", "#f2711c", "#db2828", "#a333c8", "#e03997", "#767676"];

        self.format_number = function (num) {
            if (num === null || num === undefined) return "0";
            return Number(num).toLocaleString();
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
            var esc = function (v) {
                var s = String(v == null ? '' : v);
                if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
                return '"' + s.replace(/"/g, '""') + '"';
            };

            var lines = [];
            if (!self.isBreakdownActive) {
                if (!self.tabularData1D || self.tabularData1D.length === 0) return;
                var h1 = self.getDimLabel(self.customDim1);
                var h2 = self.getDimLabel(self.customDim2);
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
                headers.push(esc("Total"));
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
            var dim2Name = String(self.customDim2 || "dim2").replace(/[^a-zA-Z0-9_]/g, "_");
            var filename = "codabench_explorer_" + dim1Name + "_" + dim2Name + ".csv";

            var blob = new Blob(["\uFEFF" + lines.join("\r\n")], { type: "text/csv;charset=utf-8;" });
            var link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
            URL.revokeObjectURL(link.href);
        };

        self.getAvailableChartTypes = function () {
            var isBreakdown = (self.customDim2 || "").indexOf("breakdown_") === 0;
            if (isBreakdown) {
                return [
                    { value: "bar", label: "Vertical Bar", icon: "chart bar" },
                    { value: "horizontalBar", label: "Horizontal Bar", icon: "bars" },
                    { value: "line", label: "Line", icon: "chart line" },
                    { value: "tabular", label: "Tabular", icon: "table" }
                ];
            }
            return [
                { value: "horizontalBar", label: "Horizontal Bar", icon: "bars" },
                { value: "bar", label: "Vertical Bar", icon: "chart bar" },
                { value: "line", label: "Line", icon: "chart line" },
                { value: "doughnut", label: "Doughnut / Pie", icon: "chart pie" },
                { value: "tabular", label: "Tabular", icon: "table" }
            ];
        };

        self.getAvailableBreakdowns = function () {
            var dim1 = self.customDim1 || "organizer";
            var items = [];
            if (dim1 !== "has_reward") {
                items.push({ value: "breakdown_has_reward", label: "Split by Reward" });
            }
            var cats = (opts.p && (opts.p.categoriesWithTags || opts.p.availableCategories)) || [];
            cats.forEach(function (cat) {
                if (dim1 !== "cat_" + cat) {
                    items.push({ value: "breakdown_cat_" + cat, label: "Split by " + cat });
                }
            });
            return items;
        };

        // Split By Secondary Categories Selection Methods
        self.getSelectedSecCount = function () {
            if (!self.selectedSplitCategoriesMap) return 0;
            var cnt = 0;
            (self.availableSecCategories || []).forEach(function (k) {
                if (self.selectedSplitCategoriesMap[k]) cnt++;
            });
            return cnt;
        };

        self.getSecCategoryCount = function (val) {
            return (self.availableSecCounts && self.availableSecCounts[val]) || 0;
        };

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

        self.selectAllSplitCategories = function (e) {
            if (e && e.preventDefault) e.preventDefault();
            self.selectedSplitCategoriesMap = {};
            (self.availableSecCategories || []).forEach(function (k) {
                self.selectedSplitCategoriesMap[k] = true;
            });
            self.renderCustomChart();
            self.update();
        };

        self.selectTop5SplitCategories = function (e) {
            if (e && e.preventDefault) e.preventDefault();
            self.selectedSplitCategoriesMap = {};
            (self.availableSecCategories || []).slice(0, 5).forEach(function (k) {
                self.selectedSplitCategoriesMap[k] = true;
            });
            self.renderCustomChart();
            self.update();
        };

        self.selectTop10SplitCategories = function (e) {
            if (e && e.preventDefault) e.preventDefault();
            self.selectedSplitCategoriesMap = {};
            (self.availableSecCategories || []).slice(0, 10).forEach(function (k) {
                self.selectedSplitCategoriesMap[k] = true;
            });
            self.renderCustomChart();
            self.update();
        };

        self.clearSplitCategories = function (e) {
            if (e && e.preventDefault) e.preventDefault();
            self.selectedSplitCategoriesMap = {};
            var defaultCount = (self.availableSecCategories || []).length <= 8 ? (self.availableSecCategories || []).length : 8;
            (self.availableSecCategories || []).slice(0, defaultCount).forEach(function (k) {
                self.selectedSplitCategoriesMap[k] = true;
            });
            self.renderCustomChart();
            self.update();
        };

        self.getDimLabel = function (val) {
            if (!val) return "";
            if (val === 'organizer') return 'Organizer';
            if (val === 'has_reward') return 'Has Reward';
            if (val === 'created_year') return 'Creation Year';
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

        self.getLimitLabel = function (val) {
            if (val === 'none') return 'None (All)';
            if (val === 'custom') return 'Custom';
            return 'Top ' + val;
        };

        self.getEffectiveLimit = function () {
            if (self.customLimit === 'none') return Infinity;
            if (self.customLimit === 'custom') return Math.max(1, parseInt(self.customLimitValue, 10) || 10);
            return parseInt(self.customLimit, 10) || 10;
        };

        self.onCustomLimitInput = function (e) {
            var val = parseInt(e.target.value, 10);
            if (!isNaN(val) && val > 0) {
                self.customLimitValue = val;
                self.renderCustomChart();
                self.update();
            }
        };

        function extractValues(comp, dim) {
            if (dim === "organizer") return [comp.organizer || "Unknown"];
            if (dim === "has_reward") return [comp.has_reward ? "Reward" : "No Reward"];
            if (dim === "created_year") {
                if (!comp.created_when) return ["Unknown"];
                var d = new Date(comp.created_when);
                return isNaN(d.getTime()) ? ["Unknown"] : [d.getUTCFullYear().toString()];
            }
            if (dim.indexOf("cat_") === 0) {
                var catName = dim.substring(4);
                var tags = (comp.tagsByCategory && comp.tagsByCategory[catName]) || [];
                return tags.length > 0 ? tags : ["(No Tag)"];
            }
            return ["All"];
        }

        self.renderCustomChart = function () {
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var dim1 = self.customDim1 || "organizer";
            var dim2 = self.customDim2 || "count";
            var chartType = self.customChartType || "horizontalBar";
            var limit = self.getEffectiveLimit();
            var isBreakdown = dim2.indexOf("breakdown_") === 0;
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

            if (isBreakdown) {
                var validBreakdownTypes = ["bar", "horizontalBar", "line", "tabular"];
                if (!validBreakdownTypes.includes(chartType)) {
                    chartType = "bar";
                    self.customChartType = chartType;
                }
            } else {
                var valid1DTypes = ["horizontalBar", "bar", "line", "doughnut", "tabular"];
                if (!valid1DTypes.includes(chartType)) {
                    chartType = "horizontalBar";
                    self.customChartType = chartType;
                }
            }

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

                var metricKey = dim2;
                var metricLabel = self.getDimLabel(dim2);
                var entries = Object.keys(groups).map(function (k) {
                    var g = groups[k];
                    var val = 0;
                    if (metricKey === "count") val = g.count;
                    else if (metricKey === "participants_sum") val = g.participants;
                    else if (metricKey === "participants_avg") val = g.count > 0 ? Math.round(g.participants / g.count) : 0;
                    else if (metricKey === "submissions_sum") val = g.submissions;
                    else if (metricKey === "submissions_avg") val = g.count > 0 ? Math.round(g.submissions / g.count) : 0;
                    return { key: k, val: val };
                });

                entries.sort(function (a, b) { return b.val - a.val; });
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

                var labels = entries.map(function (e) {
                    return e.key.length > 30 ? e.key.substring(0, 27) + "..." : e.key;
                });
                var dataVals = entries.map(function (e) { return e.val; });

                var config = null;
                if (chartType === "horizontalBar" || chartType === "bar") {
                    config = {
                        type: chartType,
                        data: {
                            labels: labels,
                            datasets: [{ label: metricLabel, data: dataVals, backgroundColor: PALETTE[0], borderWidth: 0 }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            legend: { display: false },
                            scales: chartType === "horizontalBar" ? {
                                xAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                yAxes: [{ gridLines: { display: false }, ticks: { fontSize: 11, fontColor: "#334155" } }]
                            } : {
                                yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: false, maxRotation: 45, minRotation: 20, fontSize: 11, fontColor: "#334155" } }]
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
                                borderColor: PALETTE[0],
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
                            elements: { line: { tension: 0 } },
                            scales: {
                                yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: false, maxRotation: 45, minRotation: 20, fontSize: 11, fontColor: "#334155" } }]
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
                                backgroundColor: labels.map(function (_, i) { return PALETTE[i % PALETTE.length]; })
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            legend: { position: "right", labels: { boxWidth: 12, fontSize: 11 } }
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
                var secDimKey = dim2.replace("breakdown_", "");
                var matrix = {};
                var primaryTotals = {};
                var secTotals = {};

                rows.forEach(function (c) {
                    var pVals = extractValues(c, dim1);
                    var sVals = extractValues(c, secDimKey);

                    pVals.forEach(function (p) {
                        if (!matrix[p]) matrix[p] = {};
                        primaryTotals[p] = (primaryTotals[p] || 0) + 1;
                        sVals.forEach(function (s) {
                            matrix[p][s] = (matrix[p][s] || 0) + 1;
                            secTotals[s] = (secTotals[s] || 0) + 1;
                        });
                    });
                });

                var sortedPrimaries = Object.keys(primaryTotals).sort(function (a, b) {
                    return primaryTotals[b] - primaryTotals[a];
                });
                if (limit !== Infinity) {
                    sortedPrimaries = sortedPrimaries.slice(0, limit);
                }

                var allSecondaries = Object.keys(secTotals).sort(function (a, b) {
                    return secTotals[b] - secTotals[a];
                });

                self.availableSecCategories = allSecondaries;
                self.availableSecCounts = secTotals;

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
                self.tabularCols2D = sortedSecondaries;
                self.tabularRows2D = sortedPrimaries.map(function (p) {
                    var rowVals = {};
                    var total = 0;
                    sortedSecondaries.forEach(function (s) {
                        var v = (matrix[p] && matrix[p][s]) || 0;
                        rowVals[s] = v;
                        total += v;
                    });
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
                        return (matrix[p] && matrix[p][sVal]) || 0;
                    });
                    return {
                        label: sVal,
                        data: dataArr,
                        backgroundColor: PALETTE[sIdx % PALETTE.length],
                        borderColor: PALETTE[sIdx % PALETTE.length],
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
                        scales: effType === "horizontalBar" ? {
                            xAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                            yAxes: [{ gridLines: { display: false }, ticks: { fontSize: 11, fontColor: "#334155" } }]
                        } : {
                            yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                            xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: false, maxRotation: 45, minRotation: 20, fontSize: 11, fontColor: "#334155" } }]
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
                        var avBreakdowns = self.getAvailableBreakdowns().map(function (b) { return b.value; });
                        if (self.customDim2.indexOf("breakdown_") === 0 && !avBreakdowns.includes(self.customDim2)) {
                            self.customDim2 = "count";
                        }
                        self.renderCustomChart();
                        self.update();
                    }
                },
                {
                    ref: 'customDim2Dropdown',
                    getVal: function () { return self.customDim2; },
                    setVal: function (v) {
                        self.customDim2 = v;
                        self.selectedSplitCategoriesMap = null;
                        self.activeBreakdownKey = null;
                        var avTypes = self.getAvailableChartTypes().map(function (t) { return t.value; });
                        if (!avTypes.includes(self.customChartType)) {
                            self.customChartType = avTypes[0] || "horizontalBar";
                        }
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
                },
                {
                    ref: 'customLimitDropdown',
                    getVal: function () { return self.customLimit; },
                    setVal: function (v) {
                        self.customLimit = v;
                        self.renderCustomChart();
                        self.update();
                    }
                }
            ];

            drops.forEach(function (item) {
                var el = self.refs[item.ref];
                if (!el) return;
                var $d = $(el);
                if (!$d.data('module-dropdown')) {
                    $d.dropdown({
                        onChange: function (val) {
                            if (val && val !== item.getVal()) {
                                item.setVal(val);
                            }
                        }
                    });
                } else {
                    $d.dropdown('refresh');
                }
                var cur = item.getVal();
                if (cur) {
                    $d.dropdown('set selected', cur);
                }
            });
        }

        self.on('mount', function () {
            initCustomDropdowns();
            if (opts.p && opts.p.activeTab === 'explorer') {
                self.renderCustomChart();
            }
        });

        self.on('updated', function () {
            initCustomDropdowns();
            if (opts.p && opts.p.activeTab === 'explorer') {
                self.renderCustomChart();
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
