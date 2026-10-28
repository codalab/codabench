<dashboard-tags-cumulative>
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
        <div class="canvas-wrap canvas-wrap-cum">
            <canvas id="chCumTags" ref="chCumTags"></canvas>
        </div>
    </div>

    <script>
        var self = this;
        self.chart = null;
        self.selectedCumCat = null;

        var DISTINCT_COLORS = (opts.p && opts.p.DISTINCT_COLORS) || [];

        function escapeHtml(str) {
            if (str === null || str === undefined) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        function sanitizeColor(col) {
            if (!col) return "#999";
            var s = String(col).trim();
            if (/^#([0-9a-fA-F]{3,8})$/.test(s) || /^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+(\s*,\s*[\d.]+\s*)?\)$/.test(s)) {
                return s;
            }
            return "#999";
        }

        function removeCumTagsTooltip() {
            var el = document.getElementById("chCumTags-tooltip");
            if (el && el.parentNode) {
                el.parentNode.removeChild(el);
            }
        }

        function cumTagsCustomTooltip(tooltipModel) {
            var tooltipEl = document.getElementById("chCumTags-tooltip");

            if (!tooltipModel || tooltipModel.opacity === 0) {
                if (tooltipEl) {
                    tooltipEl.style.opacity = "0";
                }
                return;
            }

            var chart = this._chart;
            var canvas = chart ? chart.canvas : (self.refs.chCumTags || document.getElementById("chCumTags"));
            if (!canvas) return;
            var wrap = canvas.parentNode;
            if (!wrap) return;

            if (!tooltipEl) {
                tooltipEl = document.createElement("div");
                tooltipEl.id = "chCumTags-tooltip";
                tooltipEl.className = "chartjs-html-tooltip";
                wrap.appendChild(tooltipEl);
            }

            if (tooltipModel.body) {
                var title = (tooltipModel.title && tooltipModel.title[0]) || "";
                var innerHtml = '<div class="tooltip-title">' + escapeHtml(title) + '</div>';
                innerHtml += '<div class="tooltip-body">';

                tooltipModel.body.forEach(function (bodyItem, i) {
                    var line = (bodyItem.lines && bodyItem.lines[0]) || "";
                    var rawColor = (tooltipModel.labelColors && tooltipModel.labelColors[i]) ? tooltipModel.labelColors[i].backgroundColor : "#999";
                    var color = sanitizeColor(rawColor);

                    innerHtml += '<div class="tooltip-row">';
                    innerHtml += '<span class="tooltip-color-box" style="background-color:' + color + '"></span>';
                    innerHtml += '<span class="tooltip-label">' + escapeHtml(line) + '</span>';
                    innerHtml += '</div>';
                });

                innerHtml += '</div>';
                tooltipEl.innerHTML = innerHtml;
            }

            tooltipEl.style.opacity = "1";

            var wrapWidth = wrap.offsetWidth || canvas.offsetWidth || 800;
            var wrapHeight = wrap.offsetHeight || canvas.offsetHeight || 360;
            var ttWidth = tooltipEl.offsetWidth;
            var ttHeight = tooltipEl.offsetHeight;

            var left = tooltipModel.caretX + 12;
            if (left + ttWidth > wrapWidth - 10) {
                left = tooltipModel.caretX - ttWidth - 12;
            }
            if (left < 10) {
                left = 10;
            }

            var top = tooltipModel.caretY - ttHeight / 2;
            if (top + ttHeight > wrapHeight - 10) {
                top = wrapHeight - ttHeight - 10;
            }
            if (top < 10) {
                top = 10;
            }

            tooltipEl.style.left = left + "px";
            tooltipEl.style.top = top + "px";
        }

        self.onCumTooltipLeave = function () {
            var t = document.getElementById("chCumTags-tooltip");
            if (t) t.style.opacity = "0";
        };

        self.destroyChart = function () {
            removeCumTagsTooltip();
            if (self.chart) {
                self.chart.destroy();
                self.chart = null;
            }
        };

        self.renderCumTagsChart = function () {
            if (!opts.p || opts.p.activeTab !== 'tags' || !opts.p.showCumTagsChart) {
                self.destroyChart();
                return;
            }

            var el = self.refs.chCumTags || document.getElementById("chCumTags");
            if (!el) return;

            if (!el._hasCumTooltipLeave) {
                el.addEventListener("mouseleave", self.onCumTooltipLeave);
                el._hasCumTooltipLeave = true;
            }

            var available = (opts.p && opts.p.categoriesWithTags && opts.p.categoriesWithTags.length > 0)
                ? opts.p.categoriesWithTags
                : ((opts.p && opts.p.availableCategories) || []);
            if (!self.selectedCumCat || !available.includes(self.selectedCumCat)) {
                self.selectedCumCat = available[0] || null;
            }

            var cat = self.selectedCumCat;
            if (!cat) {
                self.destroyChart();
                return;
            }

            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var compsWithDate = rows.filter(function (c) {
                return c.created_when && !isNaN(new Date(c.created_when).getTime());
            });

            if (compsWithDate.length === 0) {
                self.destroyChart();
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
            });

            if (topTags.length === 0) {
                self.destroyChart();
                return;
            }

            var months = (opts.p && opts.p.getCompetitionsMonthRange) ? opts.p.getCompetitionsMonthRange(compsWithDate) : [];

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
                var col = DISTINCT_COLORS[idx % DISTINCT_COLORS.length];
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

            if (self.chart && self.chart.ctx && self.chart.ctx.canvas === el) {
                self.chart.data.labels = months;
                self.chart.data.datasets = datasets;
                self.chart.options.tooltips.enabled = false;
                self.chart.options.tooltips.custom = cumTagsCustomTooltip;
                self.chart.update();
            } else {
                if (self.chart) self.chart.destroy();
                self.chart = new Chart(el, {
                    type: "line",
                    data: { labels: months, datasets: datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        elements: { line: { tension: 0 } },
                        legend: { display: true, position: "right", labels: { boxWidth: 12, fontSize: 11 } },
                        tooltips: {
                            enabled: false,
                            mode: "index",
                            intersect: false,
                            custom: cumTagsCustomTooltip
                        },
                        scales: {
                            xAxes: [{ gridLines: { display: false }, ticks: { autoSkip: true, maxTicksLimit: 12, maxRotation: 45, minRotation: 0 } }],
                            yAxes: [{ ticks: { beginAtZero: true, precision: 0 } }]
                        }
                    }
                });
            }
        };

        function initDropdown() {
            var el = self.refs.cumCatDropdown;
            if (!el) return;
            var $dd = $(el);
            if (!$dd.data('module-dropdown')) {
                $dd.dropdown({
                    onChange: function (val) {
                        if (val && val !== self.selectedCumCat) {
                            self.selectedCumCat = val;
                            self.renderCumTagsChart();
                        }
                    }
                });
            } else {
                $dd.dropdown('refresh');
            }
            if (self.selectedCumCat) {
                $dd.dropdown('set selected', self.selectedCumCat);
            }
        }

        self.lastFilteredRows = null;
        self.lastActiveTab = null;
        self.lastShowCum = null;

        self.on('mount', function () {
            initDropdown();
            self.lastFilteredRows = (opts.p && opts.p.filteredCompetitions) || [];
            self.lastActiveTab = opts.p && opts.p.activeTab;
            self.lastShowCum = Boolean(opts.p && opts.p.showCumTagsChart);
            self.renderCumTagsChart();
        });

        self.on('updated', function () {
            initDropdown();
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            var activeTab = opts.p && opts.p.activeTab;
            var showCum = Boolean(opts.p && opts.p.showCumTagsChart);

            if (self.lastFilteredRows !== rows ||
                self.lastActiveTab !== activeTab ||
                self.lastShowCum !== showCum) {
                self.lastFilteredRows = rows;
                self.lastActiveTab = activeTab;
                self.lastShowCum = showCum;
                self.renderCumTagsChart();
            }
        });

        self.on('unmount', function () {
            var el = self.refs.chCumTags || document.getElementById("chCumTags");
            if (el && el._hasCumTooltipLeave) {
                el.removeEventListener("mouseleave", self.onCumTooltipLeave);
                delete el._hasCumTooltipLeave;
            }
            self.destroyChart();
        });
    </script>
</dashboard-tags-cumulative>
