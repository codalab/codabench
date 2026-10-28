<dashboard-tags-stats>
    <div class="dashboard-tab-pane" show="{ opts.p.activeTab === 'tags' }">
        <div class="dashboard-charts-grid">
            <!-- All Tag Category Charts with Type Switcher (At the top) -->
            <div class="dashboard-chart-card tag-category-card { 'full-width': (idx === opts.p.chartCards.length - 1 && opts.p.chartCards.length % 2 === 1) }" each="{ chart, idx in opts.p.chartCards }">
                <div class="chart-header chart-header-with-controls">
                    <h4 class="chart-title">Competitions by { chart.catName }</h4>
                    <div class="ui mini basic icon buttons chart-type-buttons">
                        <button type="button" class="ui button { active: getCategoryChartType(chart.catName) === 'horizontalBar' }"
                                onclick="{ onChangeCategoryType.bind(this, chart.catName, 'horizontalBar') }" title="Horizontal Bar">
                            <i class="bars icon"></i>
                        </button>
                        <button type="button" class="ui button { active: getCategoryChartType(chart.catName) === 'bar' }"
                                onclick="{ onChangeCategoryType.bind(this, chart.catName, 'bar') }" title="Vertical Bar">
                            <i class="chart bar icon"></i>
                        </button>
                        <button type="button" class="ui button { active: getCategoryChartType(chart.catName) === 'doughnut' }"
                                onclick="{ onChangeCategoryType.bind(this, chart.catName, 'doughnut') }" title="Doughnut / Pie">
                            <i class="chart pie icon"></i>
                        </button>
                    </div>
                </div>
                <div class="canvas-wrap canvas-wrap-expanded">
                    <canvas id="{ chart.id }"></canvas>
                </div>
            </div>

            <!-- Cumulative Occurrences over Time (Full width) -->
            <div class="dashboard-chart-card full-width" if="{ opts.p.showCumTagsChart }">
                <div class="chart-header chart-header-with-controls">
                    <h4 class="chart-title">Cumulative Occurrences over Time</h4>
                    <div class="chart-controls">
                        <div class="control-group">
                            <span class="control-label">Category:</span>
                            <div class="ui selection dropdown chart-dropdown" ref="cumCatDropdown">
                                <input type="hidden" name="cum_cat" value="{ selectedCumCat }">
                                <div class="text">{ selectedCumCat || 'Select Category' }</div>
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
                    <div class="chart-controls">
                        <div class="control-group">
                            <span class="control-label">Rows:</span>
                            <div class="ui selection dropdown chart-dropdown" ref="heatmapCat1Dropdown">
                                <input type="hidden" name="heatmap_cat1" value="{ heatmapCat1 }">
                                <div class="text">{ heatmapCat1 || 'Category 1' }</div>
                                <i class="dropdown icon"></i>
                                <div class="menu">
                                    <div class="item" each="{ cat in (opts.p.categoriesWithTags || opts.p.availableCategories) }" data-value="{ cat }">{ cat }</div>
                                </div>
                            </div>
                        </div>
                        <div class="control-group">
                            <span class="control-label">Cols:</span>
                            <div class="ui selection dropdown chart-dropdown" ref="heatmapCat2Dropdown">
                                <input type="hidden" name="heatmap_cat2" value="{ heatmapCat2 }">
                                <div class="text">{ heatmapCat2 || 'Category 2' }</div>
                                <i class="dropdown icon"></i>
                                <div class="menu">
                                    <div class="item" each="{ cat in (opts.p.categoriesWithTags || opts.p.availableCategories) }" data-value="{ cat }">{ cat }</div>
                                </div>
                            </div>
                        </div>
                        <div class="control-group">
                            <div class="ui checkbox" ref="heatmapNormalizeCheckbox" style="margin-left: 8px;">
                                <input type="checkbox" ref="heatmapNormalizeInput" checked="{ heatmapNormalize }" onchange="{ onHeatmapNormalizeChange }">
                                <label class="control-label" style="cursor: pointer; user-select: none;">Normalize</label>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="canvas-wrap canvas-wrap-heatmap">
                    <canvas id="chHeatmap" ref="chHeatmap"></canvas>
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this;
        self.charts = {};
        self.categoryChartTypes = {};
        self.selectedCumCat = null;
        self.heatmapCat1 = null;
        self.heatmapCat2 = null;
        self.heatmapNormalize = false;

        var PALETTE = ["#2185d0", "#00b5ad", "#21ba45", "#fbbd08", "#f2711c", "#db2828", "#a333c8", "#e03997", "#767676"];
        var CUM_PALETTE = ["#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#e74c3c", "#16a085", "#f39c12", "#d35400", "#2c3e50", "#c0392b"];

        var DISTINCT_COLORS = [
            "#2185d0", "#21ba45", "#f2711c", "#a333c8", "#db2828",
            "#00b5ad", "#fbbd08", "#e03997", "#16a085", "#e67e22",
            "#8e44ad", "#2980b9", "#27ae60", "#d35400", "#c0392b",
            "#1abc9c", "#3498db", "#9b59b6", "#f39c12", "#e74c3c",
            "#34495e", "#00cec9", "#6c5ce7", "#fd79a8", "#0984e3",
            "#b2bec3", "#e17055", "#fdcb6e", "#636e72", "#d63031"
        ];

        function getDistinctColors(count) {
            if (count <= DISTINCT_COLORS.length) {
                return DISTINCT_COLORS.slice(0, count);
            }
            var list = DISTINCT_COLORS.slice();
            var goldenRatio = 0.618033988749895;
            var h = 0.15;
            for (var i = DISTINCT_COLORS.length; i < count; i++) {
                h = (h + goldenRatio) % 1;
                var s = 65 + (i % 3) * 10;
                var l = 45 + (i % 4) * 8;
                list.push("hsl(" + Math.round(h * 360) + ", " + s + "%, " + l + "%)");
            }
            return list;
        }

        self.getCategoryChartType = function (cat) {
            return self.categoryChartTypes[cat] || "horizontalBar";
        };

        self.onChangeCategoryType = function (cat, type, e) {
            if (e) e.preventDefault();
            self.categoryChartTypes[cat] = type;
            self.renderCategoryCharts();
            self.update();
        };

        self.onHeatmapNormalizeChange = function (e) {
            if (e) e.preventUpdate = true;
            self.heatmapNormalize = Boolean(e && e.target && e.target.checked);
            self.renderHeatmapChart();
        };

        self.renderCharts = function () {
            if (!opts.p || opts.p.activeTab !== 'tags') return;
            var rows = opts.p.filteredCompetitions || [];
            if (rows.length === 0) {
                self.destroyAllCharts();
                return;
            }

            self.renderCategoryCharts();
            if (opts.p.showCumTagsChart) {
                self.renderCumTagsChart();
            } else if (self.charts.chCumTags) {
                self.charts.chCumTags.destroy();
                delete self.charts.chCumTags;
            }
            if (opts.p.showHeatmapChart) {
                self.renderHeatmapChart();
            } else if (self.charts.chHeatmap) {
                self.charts.chHeatmap.destroy();
                delete self.charts.chHeatmap;
            }
        };

        self.renderCategoryCharts = function () {
            var chartCards = (opts.p && opts.p.chartCards) || [];
            var currentIds = chartCards.map(function (c) { return c.id; });
            Object.keys(self.charts).forEach(function (id) {
                if (id !== 'chCumTags' && id !== 'chHeatmap' && !currentIds.includes(id)) {
                    if (self.charts[id]) self.charts[id].destroy();
                    delete self.charts[id];
                }
            });
            chartCards.forEach(function (chart) {
                var cat = chart.catName;
                var counts = (opts.p && opts.p.categoryTagsCounts && opts.p.categoryTagsCounts[cat]) || {};
                var pairs = Object.keys(counts).map(function (k) { return [k, counts[k]]; });
                pairs.sort(function (a, b) { return b[1] - a[1]; });
                pairs = pairs.slice(0, 15);

                var canvasId = chart.id;
                var el = document.getElementById(canvasId);
                var color = PALETTE[chart.typeIdx % PALETTE.length];
                if (!el) return;

                var chartType = self.getCategoryChartType(cat);
                var labels = pairs.map(function (p) { return p[0]; });
                var dataVals = pairs.map(function (p) { return p[1]; });

                if (self.charts[canvasId] && self.charts[canvasId].config && self.charts[canvasId].config.type === chartType && self.charts[canvasId].ctx && self.charts[canvasId].ctx.canvas === el) {
                    self.charts[canvasId].data.labels = labels;
                    self.charts[canvasId].data.datasets[0].data = dataVals;
                    if (chartType === "doughnut") {
                        self.charts[canvasId].data.datasets[0].backgroundColor = getDistinctColors(labels.length);
                    }
                    self.charts[canvasId].update();
                } else {
                    if (self.charts[canvasId]) self.charts[canvasId].destroy();

                    if (chartType === "bar") {
                        self.charts[canvasId] = new Chart(el, {
                            type: "bar",
                            data: {
                                labels: labels,
                                datasets: [{ label: "Competitions", data: dataVals, backgroundColor: color, borderWidth: 0 }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                legend: { display: false },
                                scales: {
                                    yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                    xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: false, maxRotation: 45, minRotation: 20, fontSize: 11, fontColor: "#334155" } }]
                                }
                            }
                        });
                    } else if (chartType === "doughnut") {
                        self.charts[canvasId] = new Chart(el, {
                            type: "doughnut",
                            data: {
                                labels: labels,
                                datasets: [{
                                    label: "Competitions",
                                    data: dataVals,
                                    backgroundColor: getDistinctColors(labels.length)
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                cutoutPercentage: 55,
                                legend: { position: "right", labels: { boxWidth: 12, fontSize: 11 } }
                            }
                        });
                    } else {
                        self.charts[canvasId] = new Chart(el, {
                            type: "horizontalBar",
                            data: {
                                labels: labels,
                                datasets: [{ label: "Competitions", data: dataVals, backgroundColor: color, borderWidth: 0 }]
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
                }
            });
        };

        self.renderCumTagsChart = function () {
            var el = self.refs.chCumTags || document.getElementById("chCumTags");
            if (!el) return;

            var available = (opts.p && opts.p.categoriesWithTags && opts.p.categoriesWithTags.length > 0) ? opts.p.categoriesWithTags : ((opts.p && opts.p.availableCategories) || []);
            if (!self.selectedCumCat || !available.includes(self.selectedCumCat)) {
                self.selectedCumCat = available[0] || null;
            }

            var cat = self.selectedCumCat;
            if (!cat) {
                if (self.charts.chCumTags) {
                    self.charts.chCumTags.destroy();
                    delete self.charts.chCumTags;
                }
                return;
            }

            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var compsWithDate = rows.filter(function (c) {
                return c.created_when && !isNaN(new Date(c.created_when).getTime());
            });

            if (compsWithDate.length === 0) {
                if (self.charts.chCumTags) {
                    self.charts.chCumTags.destroy();
                    delete self.charts.chCumTags;
                }
                return;
            }

            var tagTotals = {};
            compsWithDate.forEach(function (c) {
                var tags = (c.tagsByCategory && c.tagsByCategory[cat]) || [];
                tags.forEach(function (t) {
                    tagTotals[t] = (tagTotals[t] || 0) + 1;
                });
            });

            var topTags = Object.keys(tagTotals).sort(function (a, b) {
                return tagTotals[b] - tagTotals[a];
            }).slice(0, 10);

            if (topTags.length === 0) {
                if (self.charts.chCumTags) {
                    self.charts.chCumTags.destroy();
                    delete self.charts.chCumTags;
                }
                return;
            }

            var dates = compsWithDate.map(function (c) { return new Date(c.created_when); });
            var minDate = new Date(Math.min.apply(null, dates));
            var maxDate = new Date(Math.max.apply(null, dates));

            var months = [];
            var curY = minDate.getUTCFullYear();
            var curM = minDate.getUTCMonth();
            var endY = maxDate.getUTCFullYear();
            var endM = maxDate.getUTCMonth();

            while (curY < endY || (curY === endY && curM <= endM)) {
                months.push(curY + "-" + (curM + 1 < 10 ? "0" : "") + (curM + 1));
                curM++;
                if (curM > 11) {
                    curM = 0;
                    curY++;
                }
            }

            var monthlyCounts = {};
            compsWithDate.forEach(function (c) {
                var d = new Date(c.created_when);
                var mStr = d.getUTCFullYear() + "-" + (d.getUTCMonth() + 1 < 10 ? "0" : "") + (d.getUTCMonth() + 1);
                if (!monthlyCounts[mStr]) monthlyCounts[mStr] = {};
                var tags = (c.tagsByCategory && c.tagsByCategory[cat]) || [];
                tags.forEach(function (t) {
                    monthlyCounts[mStr][t] = (monthlyCounts[mStr][t] || 0) + 1;
                });
            });

            var datasets = topTags.map(function (t, idx) {
                var col = CUM_PALETTE[idx % CUM_PALETTE.length];
                var running = 0;
                var series = months.map(function (m) {
                    running += (monthlyCounts[m] && monthlyCounts[m][t]) ? monthlyCounts[m][t] : 0;
                    return running;
                });
                return {
                    label: t + " (" + tagTotals[t] + ")",
                    data: series,
                    borderColor: col,
                    backgroundColor: col,
                    borderWidth: 2,
                    pointRadius: months.length > 36 ? 0 : 2,
                    pointHoverRadius: 4,
                    pointBackgroundColor: col,
                    fill: false,
                    lineTension: 0
                };
            });

            if (self.charts.chCumTags && self.charts.chCumTags.ctx && self.charts.chCumTags.ctx.canvas === el) {
                self.charts.chCumTags.data.labels = months;
                self.charts.chCumTags.data.datasets = datasets;
                self.charts.chCumTags.update();
            } else {
                if (self.charts.chCumTags) self.charts.chCumTags.destroy();
                self.charts.chCumTags = new Chart(el, {
                    type: "line",
                    data: { labels: months, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        elements: { line: { tension: 0 } },
                        legend: { display: true, position: "right", labels: { boxWidth: 12, fontSize: 11 } },
                        tooltips: { mode: "index", intersect: false },
                        scales: {
                            xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: true, maxTicksLimit: 12, maxRotation: 45, minRotation: 0 } }],
                            yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }]
                        }
                    }
                });
            }
        };

        function getBluesColor(pct) {
            if (pct <= 0) return "#f8fafc";
            var r = Math.round(240 - pct * (240 - 8));
            var g = Math.round(249 - pct * (249 - 81));
            var b = Math.round(255 - pct * (255 - 156));
            return "rgb(" + r + "," + g + "," + b + ")";
        }

        self.renderHeatmapChart = function () {
            var el = self.refs.chHeatmap || document.getElementById("chHeatmap");
            if (!el) return;

            var available = (opts.p && opts.p.categoriesWithTags && opts.p.categoriesWithTags.length > 0) ? opts.p.categoriesWithTags : ((opts.p && opts.p.availableCategories) || []);
            if (!self.heatmapCat1 || !available.includes(self.heatmapCat1)) {
                self.heatmapCat1 = available[0] || null;
            }
            if (!self.heatmapCat2 || !available.includes(self.heatmapCat2)) {
                self.heatmapCat2 = available[1] || available[0] || null;
            }

            var cat1 = self.heatmapCat1;
            var cat2 = self.heatmapCat2;
            if (!cat1 || !cat2) {
                if (self.charts.chHeatmap) {
                    self.charts.chHeatmap.destroy();
                    delete self.charts.chHeatmap;
                }
                return;
            }

            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var matrix = {};
            var rowCounts = {};
            var colCounts = {};

            rows.forEach(function (c) {
                var tags1 = (c.tagsByCategory && c.tagsByCategory[cat1]) || [];
                var tags2 = (c.tagsByCategory && c.tagsByCategory[cat2]) || [];
                if (tags1.length === 0 || tags2.length === 0) return;

                tags1.forEach(function (t1) {
                    rowCounts[t1] = (rowCounts[t1] || 0) + 1;
                    if (!matrix[t1]) matrix[t1] = {};
                    tags2.forEach(function (t2) {
                        colCounts[t2] = (colCounts[t2] || 0) + 1;
                        matrix[t1][t2] = (matrix[t1][t2] || 0) + 1;
                    });
                });
            });

            var rowOrder = Object.keys(rowCounts).sort(function (a, b) { return rowCounts[b] - rowCounts[a]; }).slice(0, 18);
            var colOrder = Object.keys(colCounts).sort(function (a, b) { return colCounts[b] - colCounts[a]; }).slice(0, 18);

            if (rowOrder.length === 0 || colOrder.length === 0) {
                if (self.charts.chHeatmap) {
                    self.charts.chHeatmap.destroy();
                    delete self.charts.chHeatmap;
                }
                return;
            }

            var maxVal = 1;
            rowOrder.forEach(function (r) {
                colOrder.forEach(function (c) {
                    var v = (matrix[r] && matrix[r][c]) || 0;
                    if (v > maxVal) maxVal = v;
                });
            });

            var rowSums = {};
            rowOrder.forEach(function (r) {
                var s = 0;
                colOrder.forEach(function (c) { s += (matrix[r] && matrix[r][c]) || 0; });
                rowSums[r] = s;
            });

            var desiredHeight = Math.max(380, rowOrder.length * 28 + 90);
            if (el.parentElement) {
                el.parentElement.style.height = desiredHeight + "px";
            }

            function updateHeatmapTooltip(clientX, clientY) {
                var chart = self.charts.chHeatmap;
                if (!chart || !chart.chartArea) return;
                var chartArea = chart.chartArea;
                var rect = el.getBoundingClientRect();
                var mouseX = clientX - rect.left;
                var mouseY = clientY - rect.top;

                if (mouseX >= chartArea.left && mouseX <= chartArea.right &&
                    mouseY >= chartArea.top && mouseY <= chartArea.bottom) {
                    var colW = (chartArea.right - chartArea.left) / colOrder.length;
                    var rowH = (chartArea.bottom - chartArea.top) / rowOrder.length;
                    var cIdx = Math.floor((mouseX - chartArea.left) / colW);
                    var rIdx = Math.floor((mouseY - chartArea.top) / rowH);

                    if (rIdx >= 0 && rIdx < rowOrder.length && cIdx >= 0 && cIdx < colOrder.length) {
                        var rTag = rowOrder[rIdx];
                        var cTag = colOrder[cIdx];
                        var val = (matrix[rTag] && matrix[rTag][cTag]) || 0;
                        var rSum = rowSums[rTag] || 0;
                        var pctStr = rSum > 0 ? ((val / rSum) * 100).toFixed(1) + "%" : "0%";
                        el.title = rTag + " × " + cTag + ": " + val + " (" + pctStr + ")";
                        return;
                    }
                }
                el.title = "";
            }

            el.onmousemove = function (evt) {
                updateHeatmapTooltip(evt.clientX, evt.clientY);
            };

            el.onmouseleave = function () {
                el.title = "";
            };

            el.ontouchstart = function (evt) {
                if (evt.touches && evt.touches.length > 0) {
                    updateHeatmapTooltip(evt.touches[0].clientX, evt.touches[0].clientY);
                }
            };

            el.ontouchmove = function (evt) {
                if (evt.touches && evt.touches.length > 0) {
                    updateHeatmapTooltip(evt.touches[0].clientX, evt.touches[0].clientY);
                }
            };

            var heatmapPlugin = {
                id: "heatmapCellRenderer",
                afterDraw: function (chart) {
                    var ctx = chart.ctx;
                    var chartArea = chart.chartArea;
                    if (!chartArea) return;
                    var numCols = colOrder.length;
                    var numRows = rowOrder.length;
                    if (numCols === 0 || numRows === 0) return;

                    var cellW = (chartArea.right - chartArea.left) / numCols;
                    var cellH = (chartArea.bottom - chartArea.top) / numRows;

                    ctx.save();
                    for (var r = 0; r < numRows; r++) {
                        var rTag = rowOrder[r];
                        var rSum = rowSums[rTag] || 0;
                        for (var c = 0; c < numCols; c++) {
                            var cTag = colOrder[c];
                            var val = (matrix[rTag] && matrix[rTag][cTag]) || 0;
                            var x = chartArea.left + c * cellW;
                            var y = chartArea.top + r * cellH;

                            var intensity = 0;
                            if (self.heatmapNormalize) {
                                intensity = rSum > 0 ? (val / rSum) : 0;
                            } else {
                                intensity = maxVal > 0 ? (val / maxVal) : 0;
                            }

                            ctx.fillStyle = getBluesColor(intensity);
                            ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);

                            ctx.strokeStyle = "#e2e8f0";
                            ctx.lineWidth = 1;
                            ctx.strokeRect(x + 1, y + 1, cellW - 2, cellH - 2);

                            if (cellW > 24 && cellH > 14) {
                                ctx.fillStyle = intensity > 0.55 ? "#ffffff" : "#1e293b";
                                ctx.font = "bold " + Math.min(11, Math.floor(cellH * 0.55)) + "px sans-serif";
                                ctx.textAlign = "center";
                                ctx.textBaseline = "middle";
                                var label = "";
                                if (self.heatmapNormalize) {
                                    label = (intensity * 100).toFixed(0) + "%";
                                } else {
                                    label = val > 0 ? String(val) : "0";
                                }
                                ctx.fillText(label, x + cellW / 2, y + cellH / 2);
                            }
                        }
                    }
                    ctx.restore();
                }
            };

            if (self.charts.chHeatmap) {
                self.charts.chHeatmap.destroy();
            }

            self.charts.chHeatmap = new Chart(el, {
                type: "bubble",
                data: { datasets: [{ data: [] }] },
                plugins: [heatmapPlugin],
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: { display: false },
                    tooltips: { enabled: false },
                    scales: {
                        xAxes: [{
                            type: "category",
                            position: "top",
                            labels: colOrder,
                            gridLines: { display: false },
                            ticks: { autoSkip: false, maxRotation: 45, minRotation: 30, fontSize: 11, fontColor: "#334155" }
                        }],
                        yAxes: [{
                            type: "category",
                            position: "left",
                            labels: rowOrder,
                            gridLines: { display: false },
                            ticks: { autoSkip: false, fontSize: 11, fontColor: "#334155" }
                        }]
                    }
                }
            });
        };

        function initDropdowns() {
            var drops = [
                {
                    ref: 'cumCatDropdown',
                    getVal: function () { return self.selectedCumCat; },
                    setVal: function (v) {
                        self.selectedCumCat = v;
                        self.renderCumTagsChart();
                    }
                },
                {
                    ref: 'heatmapCat1Dropdown',
                    getVal: function () { return self.heatmapCat1; },
                    setVal: function (v) {
                        self.heatmapCat1 = v;
                        self.renderHeatmapChart();
                    }
                },
                {
                    ref: 'heatmapCat2Dropdown',
                    getVal: function () { return self.heatmapCat2; },
                    setVal: function (v) {
                        self.heatmapCat2 = v;
                        self.renderHeatmapChart();
                    }
                }
            ];

            drops.forEach(function (item) {
                var el = self.refs[item.ref];
                if (!el) return;
                var $dd = $(el);
                if (!$dd.data('module-dropdown')) {
                    $dd.dropdown({
                        onChange: function (val) {
                            if (val && val !== item.getVal()) {
                                item.setVal(val);
                            }
                        }
                    });
                } else {
                    $dd.dropdown('refresh');
                }
                var cur = item.getVal();
                if (cur) {
                    $dd.dropdown('set selected', cur);
                }
            });
        }

        self.destroyAllCharts = function () {
            Object.keys(self.charts).forEach(function (id) {
                if (self.charts[id]) self.charts[id].destroy();
            });
            self.charts = {};
        };

        self.lastFilteredRows = null;
        self.lastActiveTab = null;
        self.lastCardsLen = null;
        self.lastShowCum = null;
        self.lastShowHeat = null;

        self.on('mount', function () {
            initDropdowns();
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            self.lastFilteredRows = rows;
            self.lastActiveTab = opts.p && opts.p.activeTab;
            self.lastCardsLen = (opts.p && opts.p.chartCards && opts.p.chartCards.length) || 0;
            self.lastShowCum = Boolean(opts.p && opts.p.showCumTagsChart);
            self.lastShowHeat = Boolean(opts.p && opts.p.showHeatmapChart);
            self.renderCharts();
        });

        self.on('updated', function () {
            initDropdowns();
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var activeTab = opts.p && opts.p.activeTab;
            var cardsLen = (opts.p && opts.p.chartCards && opts.p.chartCards.length) || 0;
            var showCum = Boolean(opts.p && opts.p.showCumTagsChart);
            var showHeat = Boolean(opts.p && opts.p.showHeatmapChart);

            if (self.lastFilteredRows !== rows ||
                self.lastActiveTab !== activeTab ||
                self.lastCardsLen !== cardsLen ||
                self.lastShowCum !== showCum ||
                self.lastShowHeat !== showHeat) {
                self.lastFilteredRows = rows;
                self.lastActiveTab = activeTab;
                self.lastCardsLen = cardsLen;
                self.lastShowCum = showCum;
                self.lastShowHeat = showHeat;
                self.renderCharts();
            }
        });

        self.on('unmount', function () {
            var el = self.refs.chHeatmap || document.getElementById("chHeatmap");
            if (el) {
                el.onmousemove = null;
                el.onmouseleave = null;
                el.ontouchstart = null;
                el.ontouchmove = null;
            }
            self.destroyAllCharts();
        });
    </script>
</dashboard-tags-stats>
