<analytics-storage-usage-history>
    <div class='chart-container'>
        <canvas ref="storage_usage_history_chart"></canvas>
    </div>

    <script>
        var self = this;

        self.state = {
            startDate: null,
            endDate: null,
            resolution: null
        };
        self.storageUsageHistoryData = null;
        self.storageUsageChart = null;

        self.one("mount", function () {
            self.state.startDate = opts.start_date;
            self.state.endDate = opts.end_date;
            self.state.resolution = opts.resolution;

            // Chart
            let storageUsageConfig = {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Total usage',
                            data: [],
                            borderColor: 'rgb(255, 99, 132)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Competitions usage',
                            data: [],
                            borderColor: 'rgb(255, 164, 74)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Users usage',
                            data: [],
                            borderColor: 'rgb(54, 162, 235)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Administration usage',
                            data: [],
                            borderColor: 'rgb(153, 102, 255)',
                            borderWidth: 1,
                            lineTension: 0
                        },
                        {
                            label: 'Orphaned files usage',
                            data: [],
                            borderColor: 'rgb(228, 229, 231)',
                            borderWidth: 1,
                            lineTension: 0
                        }
                    ],
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    },
                    scales: {
                        xAxes: [{
                            type: 'time',
                            ticks: {
                                source: 'auto'
                            }
                        }],
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                stepSize: 'auto',
                                callback: function(value, index, values) {
                                    return pretty_bytes(value);
                                }
                            }
                        }]
                    },
                    tooltips: {
                        mode: 'index',
                        intersect: false,
                        position: 'nearest',
                        callbacks: {
                            label: function(tooltipItem, data) {
                                return pretty_bytes(tooltipItem.yLabel);
                            }
                        }
                    }
                }
            };
            self.storageUsageChart = new Chart($(self.refs.storage_usage_history_chart), storageUsageConfig);
        });

        self.on("update", function () {
            if (opts.is_visible && (self.state.startDate != opts.start_date || self.state.endDate != opts.end_date || self.state.resolution != opts.resolution)) {
                self.state.startDate = opts.start_date;
                self.state.endDate = opts.end_date;
                self.state.resolution = opts.resolution;
                self.get_storage_usage_history(self.state.startDate, self.state.endDate, self.state.resolution);
            }
        });

        self.get_storage_usage_history = function(start_date, end_date, resolution) {
            let parameters = {
                start_date: start_date,
                end_date: end_date,
                resolution: resolution
            };
            CODALAB.api.get_storage_usage_history(parameters)
                .done(function(data) {
                    self.storageUsageHistoryData = data;
                    self.update_storage_usage_history_chart(data);
                })
                .fail(function(error) {
                    toastr.error("Could not load storage analytics data");
                });
        }

        self.update_storage_usage_history_chart = function(data) {
            var list_usages = {};
            for (let [date, usages] of Object.entries(data)) {
                for (let [usage_label, usage] of Object.entries(usages)) {
                    if (!list_usages.hasOwnProperty(usage_label)) {
                        list_usages[usage_label] = [];
                    }
                    list_usages[usage_label].push({x: new Date(date), y: usage * 1024});
                }
            }
            for (const [index, usage_label] of Object.entries(Object.keys(list_usages))) {
                list_usages[usage_label].sort(function(a, b) {return a.x - b.x;});
                self.storageUsageChart.data.datasets[index].data = list_usages[usage_label];
            }
            self.storageUsageChart.update();
        }
    </script>

    <style>
        .chart-container {
            min-height: 450px;
        }
    </style>
</analytics-storage-usage-history>