<dashboard-charts>
    <div class="ui four column grid kpi-stats">
        <div class="column center aligned">
            <div class="ui mini statistic">
                <div class="value">{ opts.p.filteredCompetitions.length }</div>
                <div class="label">Competitions</div>
            </div>
        </div>
        <div class="column center aligned">
            <div class="ui mini statistic">
                <div class="value">{ opts.p.kpis.distinctOrganizers }</div>
                <div class="label">Organizers</div>
            </div>
        </div>
        <div class="column center aligned">
            <div class="ui mini statistic">
                <div class="value">{ opts.p.kpis.participants }</div>
                <div class="label">Participants</div>
            </div>
        </div>
        <div class="column center aligned">
            <div class="ui mini statistic">
                <div class="value">{ opts.p.kpis.submissions }</div>
                <div class="label">Submissions</div>
            </div>
        </div>
    </div>

    <div class="ui stackable two column grid">
        <div class="column" if="{ opts.p.showOrgsChart }">
            <div class="ui segment chart-card">
                <h4 class="ui header">Top Organizers</h4>
                <div class="canvas-wrap">
                    <canvas id="chOrgs" ref="chOrgs"></canvas>
                </div>
            </div>
        </div>
        <div class="column" if="{ opts.p.showCompsChart }">
            <div class="ui segment chart-card">
                <h4 class="ui header">Most Popular Competitions</h4>
                <div class="canvas-wrap">
                    <canvas id="chComps" ref="chComps"></canvas>
                </div>
            </div>
        </div>
        <div class="column" each="{ chart, idx in opts.p.chartCards }">
            <div class="ui segment chart-card">
                <h4 class="ui header">By { chart.catName }</h4>
                <div class="canvas-wrap">
                    <canvas id="{ chart.id }" ref="dynamicCharts"></canvas>
                </div>
            </div>
        </div>
    </div>
    <script>
        var self = this;
        function syncRefs() {
            if (opts.p && opts.p.refs) {
                opts.p.refs.chOrgs = self.refs.chOrgs;
                opts.p.refs.chComps = self.refs.chComps;
                opts.p.refs.dynamicCharts = self.refs.dynamicCharts;
            }
        }
        self.on('mount', syncRefs);
        self.on('updated', syncRefs);
    </script>
</dashboard-charts>