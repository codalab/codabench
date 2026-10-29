<dashboard-tags-heatmap>
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

    <script>
        var self = this;
        self.chart = null;
        self.heatmapCat1 = null;
        self.heatmapCat2 = null;
        self.heatmapNormalize = false;

        function getBluesColor(pct) {
            if (pct <= 0) return "#f8fafc";
            var r = Math.round(240 - pct * (240 - 8));
            var g = Math.round(249 - pct * (249 - 81));
            var b = Math.round(255 - pct * (255 - 156));
            return "rgb(" + r + "," + g + "," + b + ")";
        }

        function clearCanvasListeners(el) {
            if (!el) return;
            el.onmousemove = null;
            el.onmouseleave = null;
            el.ontouchstart = null;
            el.ontouchmove = null;
            el.title = "";
        }

        self.onHeatmapNormalizeChange = function (e) {
            if (e) e.preventUpdate = true;
            self.heatmapNormalize = Boolean(e && e.target && e.target.checked);
            self.renderHeatmapChart();
        };

        self.destroyChart = function () {
            var el = self.refs.chHeatmap || document.getElementById("chHeatmap");
            clearCanvasListeners(el);
            if (self.chart) {
                self.chart.destroy();
                self.chart = null;
            }
        };

        self.renderHeatmapChart = function () {
            if (!opts.p || opts.p.activeTab !== 'tags' || !opts.p.showHeatmapChart) {
                self.destroyChart();
                return;
            }

            var el = self.refs.chHeatmap || document.getElementById("chHeatmap");
            if (!el) return;

            var available = (opts.p && opts.p.categoriesWithTags && opts.p.categoriesWithTags.length > 0)
                ? opts.p.categoriesWithTags
                : ((opts.p && opts.p.availableCategories) || []);
            if (!self.heatmapCat1 || !available.includes(self.heatmapCat1)) {
                self.heatmapCat1 = available[0] || null;
            }
            if (!self.heatmapCat2 || !available.includes(self.heatmapCat2)) {
                self.heatmapCat2 = available[1] || available[0] || null;
            }

            var cat1 = self.heatmapCat1;
            var cat2 = self.heatmapCat2;
            if (!cat1 || !cat2) {
                self.destroyChart();
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
                self.destroyChart();
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
                var chart = self.chart;
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
                        el.title = rTag + " \u00D7 " + cTag + ": " + val + " (" + pctStr + ")";
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

            if (self.chart) {
                self.chart.destroy();
            }

            self.chart = new Chart(el, {
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

            if (opts.p && opts.p.initDropdowns) {
                opts.p.initDropdowns(self, drops);
            }
        }

        self.lastFilteredRows = null;
        self.lastActiveTab = null;
        self.lastShowHeat = null;

        self.on('mount', function () {
            initDropdowns();
            self.lastFilteredRows = (opts.p && opts.p.filteredCompetitions) || [];
            self.lastActiveTab = opts.p && opts.p.activeTab;
            self.lastShowHeat = Boolean(opts.p && opts.p.showHeatmapChart);
            self.renderHeatmapChart();
        });

        self.on('updated', function () {
            initDropdowns();
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var activeTab = opts.p && opts.p.activeTab;
            var showHeat = Boolean(opts.p && opts.p.showHeatmapChart);

            if (self.lastFilteredRows !== rows ||
                self.lastActiveTab !== activeTab ||
                self.lastShowHeat !== showHeat) {
                self.lastFilteredRows = rows;
                self.lastActiveTab = activeTab;
                self.lastShowHeat = showHeat;
                self.renderHeatmapChart();
            }
        });

        self.on('unmount', function () {
            self.destroyChart();
        });
    </script>
</dashboard-tags-heatmap>
