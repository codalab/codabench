<dashboard-tags-category-charts>
    <div class="dashboard-charts-grid" if="{ (opts.p.chartCards || []).length > 0 }">
        <!-- Tag Category Card with Type Switcher -->
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
            <div class="canvas-wrap canvas-wrap-expanded { 'canvas-wrap-doughnut': getCategoryChartType(chart.catName) === 'doughnut' }" style="{ getCategoryChartType(chart.catName) === 'doughnut' ? 'height: 320px !important;' : '' }">
                <canvas id="{ chart.id }"></canvas>
            </div>
        </div>
    </div>

    <script>
        var self = this;
        self.charts = {};
        self.categoryChartTypes = {};

        var DISTINCT_COLORS = (opts.p && opts.p.DISTINCT_COLORS) || [];
        function getDistinctColors(count) {
            if (opts.p && opts.p.getDistinctColors) return opts.p.getDistinctColors(count);
            return [];
        }

        self.getCategoryChartType = function (cat) {
            return self.categoryChartTypes[cat] || "horizontalBar";
        };

        self.onChangeCategoryType = function (cat, type, e) {
            if (e) e.preventDefault();
            self.categoryChartTypes[cat] = type;
            self.update();
            self.renderCharts();
        };

        self.destroyAllCharts = function () {
            Object.keys(self.charts).forEach(function (id) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                }
            });
            self.charts = {};
        };

        self.renderCharts = function () {
            if (!opts.p || opts.p.activeTab !== 'tags') {
                self.destroyAllCharts();
                return;
            }
            var rows = opts.p.filteredCompetitions || [];
            var chartCards = opts.p.chartCards || [];
            if (rows.length === 0 || chartCards.length === 0) {
                self.destroyAllCharts();
                return;
            }

            var currentIds = chartCards.map(function (c) { return c.id; });
            Object.keys(self.charts).forEach(function (id) {
                if (!currentIds.includes(id)) {
                    if (self.charts[id]) {
                        self.charts[id].destroy();
                    }
                    delete self.charts[id];
                }
            });

            chartCards.forEach(function (chart) {
                var cat = chart.catName;
                var counts = (opts.p && opts.p.categoryTagsCounts && opts.p.categoryTagsCounts[cat]) || {};
                var pairs = Object.keys(counts).map(function (k) { return [k, counts[k]]; });
                pairs.sort(function (a, b) { return b[1] - a[1]; });

                var chartType = self.getCategoryChartType(cat);
                var maxItems = (chartType === "doughnut") ? 36 : 25;
                pairs = pairs.slice(0, maxItems);

                var canvasId = chart.id;
                var el = document.getElementById(canvasId);
                var color = DISTINCT_COLORS[chart.typeIdx % DISTINCT_COLORS.length];
                if (!el) return;

                var labels = pairs.map(function (p) { return p[0]; });
                var dataVals = pairs.map(function (p) { return p[1]; });

                if (self.charts[canvasId] && self.charts[canvasId].config && self.charts[canvasId].config.type === chartType && self.charts[canvasId].ctx && self.charts[canvasId].ctx.canvas === el) {
                    self.charts[canvasId].data.labels = labels;
                    self.charts[canvasId].data.datasets[0].data = dataVals;
                    if (chartType === "doughnut") {
                        self.charts[canvasId].data.datasets[0].label = "Tag assignments";
                        self.charts[canvasId].data.datasets[0].backgroundColor = getDistinctColors(labels.length);
                    }
                    self.charts[canvasId].update();
                } else {
                    if (self.charts[canvasId]) {
                        self.charts[canvasId].destroy();
                    }

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
                                tooltips: {
                                    callbacks: {
                                        label: function (tooltipItem, data) {
                                            var dataset = data.datasets[tooltipItem.datasetIndex];
                                            var val = dataset.data[tooltipItem.index];
                                            var total = dataset.data.reduce(function (a, b) { return a + Number(b || 0); }, 0);
                                            var pct = total > 0 ? ((val / total) * 100).toFixed(1) + "%" : "0%";
                                            var compLabel = val === 1 ? " Competition" : " Competitions";
                                            return " " + val + compLabel + " (" + pct + ")";
                                        }
                                    }
                                },
                                scales: {
                                    yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                    xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: true, autoSkipPadding: 8, maxTicksLimit: 36, maxRotation: 45, minRotation: 0, fontSize: 11, fontColor: "#334155" } }]
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
                                cutoutPercentage: 50,
                                legend: {
                                    display: true,
                                    position: "right",
                                    labels: {
                                        boxWidth: 10,
                                        fontSize: 10,
                                        padding: 4,
                                        generateLabels: function (chart) {
                                            var data = chart.data;
                                            if (data.labels.length && data.datasets.length) {
                                                var ds = data.datasets[0];
                                                return data.labels.map(function (label, i) {
                                                    var meta = chart.getDatasetMeta(0);
                                                    var arc = (meta && meta.data && meta.data[i]) || {};
                                                    var custom = arc.custom || {};
                                                    var fill = custom.backgroundColor || (ds.backgroundColor && ds.backgroundColor[i]) || "#999";
                                                    var shortLabel = label.length > 20 ? label.substring(0, 18) + "..." : label;
                                                    return {
                                                        text: shortLabel + " (" + (ds.data[i] || 0) + ")",
                                                        fillStyle: fill,
                                                        strokeStyle: fill,
                                                        lineWidth: 0,
                                                        hidden: isNaN(ds.data[i]) || (arc && arc.hidden),
                                                        index: i
                                                    };
                                                }).slice(0, 36);
                                            }
                                            return [];
                                        }
                                    }
                                },
                                tooltips: {
                                    callbacks: {
                                        label: function (tooltipItem, data) {
                                            var dataset = data.datasets[tooltipItem.datasetIndex];
                                            var val = dataset.data[tooltipItem.index];
                                            var total = dataset.data.reduce(function (a, b) { return a + b; }, 0);
                                            var pct = total > 0 ? ((val / total) * 100).toFixed(1) + "%" : "0%";
                                            var label = data.labels[tooltipItem.index] || "";
                                            var compLabel = val === 1 ? " Competition" : " Competitions";
                                            return label + ": " + val + compLabel + " (" + pct + ")";
                                        }
                                    }
                                }
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
                                tooltips: {
                                    callbacks: {
                                        label: function (tooltipItem, data) {
                                            var dataset = data.datasets[tooltipItem.datasetIndex];
                                            var val = dataset.data[tooltipItem.index];
                                            var total = dataset.data.reduce(function (a, b) { return a + Number(b || 0); }, 0);
                                            var pct = total > 0 ? ((val / total) * 100).toFixed(1) + "%" : "0%";
                                            var compLabel = val === 1 ? " Competition" : " Competitions";
                                            return " " + val + compLabel + " (" + pct + ")";
                                        }
                                    }
                                },
                                scales: {
                                    xAxes: [{ ticks: { beginAtZero: true, precision: 0 } }],
                                    yAxes: [{ gridLines: { display: false }, ticks: { fontSize: 11, fontColor: "#334155" } }]
                                }
                            }
                        });
                    }
                }
            });

            setTimeout(function () {
                $(self.root).find('.tag-info-tooltip').popup({
                    position: 'top left',
                    variation: 'inverted',
                    hoverable: true
                });
            }, 0);
        };

        self.lastFilteredRows = null;
        self.lastActiveTab = null;
        self.lastCardsLen = null;

        self.on('mount', function () {
            self.lastFilteredRows = (opts.p && opts.p.filteredCompetitions) || [];
            self.lastActiveTab = opts.p && opts.p.activeTab;
            self.lastCardsLen = (opts.p && opts.p.chartCards && opts.p.chartCards.length) || 0;
            self.renderCharts();
        });

        self.on('updated', function () {
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var activeTab = opts.p && opts.p.activeTab;
            var cardsLen = (opts.p && opts.p.chartCards && opts.p.chartCards.length) || 0;

            if (self.lastFilteredRows !== rows ||
                self.lastActiveTab !== activeTab ||
                self.lastCardsLen !== cardsLen) {
                self.lastFilteredRows = rows;
                self.lastActiveTab = activeTab;
                self.lastCardsLen = cardsLen;
                self.renderCharts();
            }
        });

        self.on('unmount', function () {
            self.destroyAllCharts();
        });
    </script>
</dashboard-tags-category-charts>
