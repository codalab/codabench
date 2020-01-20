<log_window>
    <div if="{!opts.split_logs}">
        <pre class="submission_output"><virtual
                if="{ opts.lines === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                each="{ line in opts.lines }">{ line }</virtual></pre>
    </div>
    <div if="{opts.split_logs}">
        <div>Scoring</div>
        <pre class="submission_output"><virtual
                if="{ _.get(opts.lines, 'program') === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                each="{ line in _.get(opts.lines, 'program', []) }">{ line }</virtual></pre>
        <div>Ingestion</div>
        <pre class="submission_output"><virtual
                if="{ _.get(opts.lines, 'ingestion') === undefined }">Preparing submission... this may take a few moments..</virtual><virtual
                each="{ line in _.get(opts.lines, 'ingestion', []) }">{ line }</virtual></pre>
    </div>
    <div class="graph-container">
        <canvas class="output-chart" height="200" ref="chart"></canvas>
    </div>
    <script>
        let self = this

        self.graph_data = {
            datasets: []
        }

        self.graph_config = {
            type: 'line',
            data: self.graph_data,
            options: {
                maintainAspectRatio: false,
                responsive: true,
                animation: {
                    duration: 100,
                    easing: 'easeInCirc'
                },
                tooltips: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    xAxes: [{
                        type: 'time',
                    }],
                    yAxes: [{
                        ticks: {
                            suggestedMin: 0,
                            suggestedMax: 1,
                            display: true
                        }
                    }]
                }
            }
        }
        self.on('mount', function () {
            self.chart = new Chart(self.refs.chart, self.graph_config)
        })
        self.on('update', function () {
            self.chart.data.datasets = self.opts.data ? [self.opts.data] : []
            self.chart.update()
        })
    </script>
    <style type="text/stylus">
        .submission_output
            height 400px
            padding 15px !important
            overflow auto
    </style>
</log_window>
