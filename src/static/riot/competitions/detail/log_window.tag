<log_window>
    <div if="{!opts.split_logs}">
        <!-- We have to have this on a gross line so Pre formatting stays nice -->
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
    <div class="graph-container" show="{opts.show_graph && opts.detailed_result_url}">
        <iframe src="{opts.detailed_result_url}" class="graph-frame"></iframe>
        <!--<canvas class="output-chart" height="200" ref="chart"></canvas>-->
    </div>
    <script>
        let self = this
        // TODO: Decide what to do with this code relevant to chart.js settings. Not being used. Pull?
        // self.graph_config = {
        //     type: 'line',
        //     data: {
        //         datasets: []
        //     },
        //     options: {
        //         maintainAspectRatio: false,
        //         responsive: true,
        //         animation: {
        //             duration: 100,
        //             easing: 'easeInCirc'
        //         },
        //         tooltips: {
        //             mode: 'index',
        //             intersect: false,
        //         },
        //         scales: {
        //             xAxes: [{
        //                 type: 'time',
        //             }],
        //             yAxes: [{
        //                 ticks: {
        //                     suggestedMin: 0,
        //                     suggestedMax: 1,
        //                     display: true
        //                 }
        //             }]
        //         }
        //     }
        // }
        // self.on('mount', function () {
        //     self.chart = new Chart(self.refs.chart, self.graph_config)
        // })
        // self.on('update', function () {
        //     self.chart.data.datasets = self.opts.data ? [self.opts.data] : []
        //     self.chart.update()
        // })
    </script>
    <style type="text/stylus">
        .graph-frame
            width 100%
            height 70vh
            border none
            overflow scroll

        .submission_output
            height 400px
            padding 15px !important
            overflow auto
    </style>
</log_window>
