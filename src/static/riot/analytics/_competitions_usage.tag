<analytics-storage-competitions-usage>
    <div class="flex-row">
        <select class="ui search multiple selection dropdown" multiple ref="competitions_dropdown">
            <i class="dropdown icon"></i>
            <div class="default text">Select Competitions</div>
            <div class="menu">
                <option each="{ competition in competitionsDropdownOptions }" value="{ competition.id }">{ competition.title }</div> 
            </div>
        </select>
        <button class="ui button" onclick={selectTopFiveBiggestCompetitions}>Select top 5 biggest competitions</button>
        <button class="ui green button" onclick={downloadCompetitionsHistory}>
            <i class="icon download"></i>Download as CSV
        </button>
        <h4 style="margin: 0 0 0 auto">{lastSnapshotDate ? "Last snaphost date: " + pretty_date(lastSnapshotDate) : "No snapshot has been taken yet"}</h4>
    </div>
    <div class='chart-container'>
        <canvas class="big" ref="storage_competitions_usage_chart"></canvas>
    </div>
    <div class="ui calendar" ref="table_date_calendar">
        <div class="ui input left icon">
            <i class="calendar icon"></i>
            <input type="text">
        </div>
    </div>
    <div class='chart-container'>
        <canvas class="big" ref="storage_competitions_usage_pie"></canvas>
    </div>
    <button class="ui green button" onclick={downloadCompetitionsTable}>
        <i class="icon download"></i>Download as CSV
    </button>
    <table id="storageCompetitionsTable" class="ui selectable sortable celled table">
        <thead>
            <tr>
                <th is="su-th" data-sort-method="alphanumeric">Competition</th>
                <th is="su-th" data-sort-method="alphanumeric">Organizer</th>
                <th is="su-th" class="date" data-sort-method="date">Creation date</th>
                <th is="su-th" class="bytes" data-sort-method="numeric">Datasets</th>
            </tr>
        </thead>
        <tbody>
            <tr each="{ competitionUsage in competitionsUsageTableData }">
                <td><a href="{ URLS.COMPETITION_DETAIL(competitionUsage.id) }">{ competitionUsage.title }</a></td>
                <td>{ competitionUsage.organizer }</td>
                <td>{ formatDate(competitionUsage.created_when) }</td>
                <td>{ pretty_bytes(competitionUsage.datasets) }</td>
            </tr>
        </tbody>
    </table>

    <script>
        var self = this;

        self.state = {
            startDate: null,
            endDate: null,
            resolution: null
        };

        let datetime = luxon.DateTime;

        self.lastSnapshotDate = null;
        self.competitionsUsageData = null;
        self.competitionsDropdownOptions = [];
        self.tableSelectedDate = null;
        self.selectedCompetitions = [];
        self.competitionsColor = {};
        self.colors = ["#36a2eb", "#ff6384", "#4bc0c0", "#ff9f40", "#9966ff", "#ffcd56", "#c9cbcf"];
        self.storageCompetitionsUsageChart;
        self.storageCompetitionsUsagePieChart;
        self.competitionsUsageTableData = [];

        self.one("mount", function () {
            self.state.startDate = opts.start_date;
            self.state.endDate = opts.end_date;
            self.state.resolution = opts.resolution;

            // Semantic UI
            $(self.refs.competitions_dropdown).dropdown({
                onAdd: self.addCompetitionToSelection,
                onRemove: self.removeCompetitionFromSelection,
                clearable: true,
                preserveHTML: false,
            });

            $('#storageCompetitionsTable').tablesort();
            $('#storageCompetitionsTable thead th.date').data('sortBy', function(th, td, tablesort) {
                return new Date(td.text());
            });
            $('#storageCompetitionsTable thead th.bytes').data('sortBy', function(th, td, tablesort) {
                const re = /(\d+.?\d*)(\D+)/;
                const found = td.text().match(re);
                const unitToPower = {
                    'B': 0,
                    'KiB': 1,
                    'MiB': 2,
                    'GiB': 3,
                    'TiB': 4,
                    'PiB': 5,
                    'EiB': 6,
                    'ZiB': 7
                };
                const bytes = found[1] * Math.pow(1024, unitToPower[found[2]]);
                return bytes;
            });

            const general_calendar_options = {
                type: 'date',
                // Sets the format of the placeholder date string to YYYY-MM-DD
                formatter: {
                    date: function (date, settings) {
                        return datetime.fromJSDate(date).toISODate();
                    }
                },
            };
            let table_date_specific_options = {
                onChange: function(date, text) {
                    self.tableSelectedDate = date;
                    self.updateCompetitionsTable();
                    self.updateCompetitionsPieChart();
                }
            };
            let table_date_calendar_options = _.assign({}, general_calendar_options, table_date_specific_options);
            $(self.refs.table_date_calendar).calendar(table_date_calendar_options);

            // Line chart
            let storageCompetitionsUsageConfig = {
                type: 'line',
                data: {
                    datasets: [],
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

            self.storageCompetitionsUsageChart = new Chart($(self.refs.storage_competitions_usage_chart), storageCompetitionsUsageConfig);

            // Pie chart
            let storageCompetitionsUsagePieConfig = {
                type: 'pie',
                data: {
                    labels: [],
                    competitionsId: [],
                    datasets: [
                        {
                            label: 'Competitions distribution',
                            backgroundColor: [],
                            hoverOffset: 4,
                            data: []
                        }
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'left',
                        },
                        title: {
                            display: true,
                            text: 'Competitions distribution'
                        }
                    },
                    tooltips: {
                        callbacks: {
                            label: function(tooltipItem, data) {
                                const label = data.labels[tooltipItem.index];
                                const value = pretty_bytes(data.datasets[0].data[tooltipItem.index]);
                                return " " + label + ": " + value;
                            }
                        }
                    }
                }
            };

            self.storageCompetitionsUsagePieChart = new Chart($(self.refs.storage_competitions_usage_pie), storageCompetitionsUsagePieConfig);
        });

        self.on("update", function () {
            if (opts.is_visible && (self.state.startDate != opts.start_date || self.state.endDate != opts.end_date || self.state.resolution != opts.resolution)) {
                self.state.startDate = opts.start_date;
                self.state.endDate = opts.end_date;
                self.state.resolution = opts.resolution;
                self.get_competitions_usage(self.state.startDate, self.state.endDate, self.state.resolution);
            }
        });

        self.get_competitions_usage = function(start_date, end_date, resolution) {
            let parameters = {
                start_date: start_date,
                end_date: end_date,
                resolution: resolution
            };
            CODALAB.api.get_competitions_usage(parameters)
                .done(function(data) {
                    self.competitionsUsageData = data["competitions_usage"];
                    self.lastSnapshotDate = data["last_storage_calculation_date"];
                    self.update({lastSnapshotDate: data["last_storage_calculation_date"]});
                    self.updateCompetitionsSelectionDropdown();
                    self.updateCompetitionTableCalendar(data["competitions_usage"]);
                    self.updateCompetitionsChart();
                    self.updateCompetitionsPieChart();
                    self.updateCompetitionsTable();
                })
                .fail(function(error) {
                    toastr.error("Could not load storage analytics data");
                });
        }

        self.updateCompetitionsSelectionDropdown = function () {
            // Update the options
            let competitionsOptions = [];
            if(Object.keys(self.competitionsUsageData).length > 0) {
                const competitions = Object.values(self.competitionsUsageData)[0];
                competitionsOptions = Object.entries(competitions).map(([id, { title }]) => ({ id, title }));
            }

            // Save
            self.competitionsDropdownOptions = competitionsOptions;
            $(self.refs.competitions_dropdown).dropdown('change values', competitionsOptions); // This triggers a reset of selected values
            self.update({competitionsDropdownOptions: competitionsOptions});
        }

        self.updateCompetitionTableCalendar = function(data) {
            // Set the min and max date of the calendar
            const minDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) < new Date(cur) ? acc : cur, '9999-12-31'));
            const maxDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur, '0000-00-00'));
            $(self.refs.table_date_calendar).calendar('setting', 'minDate', minDate);
            $(self.refs.table_date_calendar).calendar('setting', 'maxDate', maxDate);

            // Select the most current date available
            self.tableSelectedDate = maxDate;
            $(self.refs.table_date_calendar).calendar('set date', maxDate);
            $(self.refs.table_date_calendar).calendar('refresh');
        }

        self.addCompetitionToSelection = function(value, text, $addedItem) {
            if(Object.keys(self.competitionsUsageData).length > 0) {
                self.selectedCompetitions.push(value);
                let competitionUsage = [];
                for (let [dateString, competitions] of Object.entries(self.competitionsUsageData)) {
                    for (let [competitionId, competition] of Object.entries(competitions)) {
                        if (competitionId == value) {
                            competitionUsage.push({x: new Date(dateString), y: competition.datasets * 1024});
                        }
                    }
                }
                const competitions = Object.values(self.competitionsUsageData)[0];
                const competitionTitle = competitions[value].title;
                if(!self.competitionsColor.hasOwnProperty(value)) {
                    self.competitionsColor[value] = self.colors[Object.keys(self.competitionsColor).length % self.colors.length];
                }
                const color = self.competitionsColor[value];

                // Update chart
                self.storageCompetitionsUsageChart.data.datasets.push({
                    competitionId: value,
                    label: competitionTitle,
                    data: competitionUsage,
                    backgroundColor: color,
                    borderWidth: 1,
                    lineTension: 0,
                    fill: false
                });
                self.storageCompetitionsUsageChart.update();

                // Update pie chart
                let selectedDate = self.tableSelectedDate;
                if (!selectedDate) {
                    selectedDate = new Date(Object.keys(self.competitionsUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
                }
                const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
                const closestOlderDateString = Object.keys(self.competitionsUsageData).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
                const competitionsAtSelectedDate = self.competitionsUsageData[closestOlderDateString];
                const selectedCompetitions = Object.keys(competitionsAtSelectedDate).filter(date => self.selectedCompetitions.includes(date)).reduce((competition, date) => ({ ...competition, [date]: competitionsAtSelectedDate[date] }), {});
                
                const {labels, competitionsId, data} = self.formatDataForCompetitionsPieChart(selectedCompetitions);
                self.storageCompetitionsUsagePieChart.data.labels = labels;
                self.storageCompetitionsUsagePieChart.data.competitionsId = competitionsId;
                self.storageCompetitionsUsagePieChart.data.datasets[0].data = data;
                self.storageCompetitionsUsagePieChart.data.datasets[0].labels = labels;
                self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor = self.listOfColors(data.length);
                self.storageCompetitionsUsagePieChart.update();
            }
        }

        self.formatDataForCompetitionsPieChart = function (data) {
            var labels = [];
            var competitionsId = [];
            var formattedData = [];

            const competitionArray = Object.entries(data).map(([key, value]) => ({ ...value, id: key }));
            competitionArray.sort((a, b) => b.datasets - a.datasets);
            for (const competition of competitionArray) {
                labels.push(competition.title);
                competitionsId.push(competition.id);
                formattedData.push(competition.datasets * 1024);
            }

            return {labels: labels, competitionsId: competitionsId, data: formattedData};
        }

        self.listOfColors = function(arrayLength) {
            return Array.apply(null, Array(arrayLength)).map(function (x, i) { return self.colors[i%self.colors.length]; })
        }

        self.removeCompetitionFromSelection = function(value, text, $removedItem) {
            // Remove from selection
            const indexToRemoveInSelected = self.selectedCompetitions.findIndex(competitionId => competitionId == value);
            if (indexToRemoveInSelected !== -1) {
                self.selectedCompetitions.splice(indexToRemoveInSelected, 1);
            }

            // Reassign competitions color
            self.competitionsColor = {};
            for(const competitionId of self.selectedCompetitions) {
                self.competitionsColor[competitionId] = self.colors[Object.keys(self.competitionsColor).length % self.colors.length];
            }

            // Remove from competition usage chart
            let indexToRemove = self.storageCompetitionsUsageChart.data.datasets.findIndex(dataset => dataset.competitionId == value);
            if (indexToRemove !== -1) {
                self.storageCompetitionsUsageChart.data.datasets.splice(indexToRemove, 1);
                for(let dataset of self.storageCompetitionsUsageChart.data.datasets) {
                    dataset.backgroundColor = self.competitionsColor[dataset.competitionId];
                }
                self.storageCompetitionsUsageChart.update();
            }

            // Remove from competition pie chart
            indexToRemove = self.storageCompetitionsUsagePieChart.data.competitionsId.findIndex(id => id == value);
            if (indexToRemove !== -1) {
                self.storageCompetitionsUsagePieChart.data.labels.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.competitionsId.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.datasets[0].data.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor.splice(indexToRemove, 1);
                self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor = self.storageCompetitionsUsagePieChart.data.competitionsId.map(competitionId => self.competitionsColor[competitionId]);
                self.storageCompetitionsUsagePieChart.update();
            }
        }

        self.selectTopFiveBiggestCompetitions = function () {
            let selectCompetitions = [];
            if (Object.keys(self.competitionsUsageData).length > 0) {
                const mostRecentDateString = Object.keys(self.competitionsUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur );
                let competitions = Object.entries(self.competitionsUsageData[mostRecentDateString]);
                competitions.sort((a, b) => b[1].datasets - a[1].datasets);
                selectCompetitions = competitions.slice(0, 5).map(([id]) => id);
            }
            for(const competitionId of selectCompetitions) {
                $(self.refs.competitions_dropdown).dropdown('set selected', competitionId);
            }
        }

        self.updateCompetitionsChart = function() {
            if(Object.keys(self.competitionsUsageData).length > 0) {
                const selectedCompetitions = Object.fromEntries(
                    Object.entries(self.competitionsUsageData).map(([dateString, competitions]) => [
                        dateString,
                        Object.fromEntries(
                            Object.entries(competitions).filter(([competitionId]) => self.selectedCompetitions.includes(competitionId))
                        )
                    ])
                );
                
                const competitionsUsage = {};
                for (let [dateString, competitions] of Object.entries(selectedCompetitions)) {
                    for (let [competitionId, competition] of Object.entries(competitions)) {
                        if (!competitionsUsage.hasOwnProperty(competitionId)) {
                            competitionsUsage[competitionId] = [];
                        }
                        competitionsUsage[competitionId].push({x: new Date(dateString), y: competition.datasets * 1024});
                    }
                }

                self.storageCompetitionsUsageChart.data.datasets = [];
                let index = 0;
                for(let [competitionId, dataset] of Object.entries(competitionsUsage)) {
                    const color = self.colors[index % self.colors.length];
                    const title = Object.values(self.competitionsUsageData)[0][competitionId].title;
                    self.storageCompetitionsUsageChart.data.datasets.push({
                        competitionId: competitionId,
                        label: title,
                        data: dataset,
                        backgroundColor: color,
                        borderWidth: 1,
                        lineTension: 0,
                        fill: false
                    });
                    index++;
                }

                self.storageCompetitionsUsageChart.update();
            }
        }

        self.updateCompetitionsPieChart = function() {
            let selectedDate = self.tableSelectedDate;
            if (!selectedDate) {
                selectedDate = new Date(Object.keys(self.competitionsUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
            }
            const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
            const closestOlderDateString = Object.keys(self.competitionsUsageData).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
            const competitionsAtSelectedDate = self.competitionsUsageData[closestOlderDateString];
            const selectedCompetitions = Object.keys(competitionsAtSelectedDate).filter(date => self.selectedCompetitions.includes(date)).reduce((competition, date) => ({ ...competition, [date]: competitionsAtSelectedDate[date] }), {});

            const {labels, competitionsId, data} = self.formatDataForCompetitionsPieChart(selectedCompetitions);
            self.storageCompetitionsUsagePieChart.data.labels = labels;
            self.storageCompetitionsUsagePieChart.data.competitionsId = competitionsId;
            self.storageCompetitionsUsagePieChart.data.datasets[0].data = data;
            self.storageCompetitionsUsagePieChart.data.datasets[0].labels = labels;
            self.storageCompetitionsUsagePieChart.data.datasets[0].backgroundColor = self.listOfColors(data.length);
            self.storageCompetitionsUsagePieChart.update();
        }

        self.updateCompetitionsTable = function() {
            const data = self.competitionsUsageData;
            let competitionsUsageTableData = [];
            if (Object.keys(data).length > 0) {
                let selectedDate = self.tableSelectedDate;
                if (!selectedDate) {
                    selectedDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
                }
                const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
                const closestOlderDateString = Object.keys(data).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
                const competitions = data[closestOlderDateString];
                Object.entries(competitions).forEach(keyValue => {
                    const [competitionId, competition] = keyValue;
                    competitionsUsageTableData.push({
                        'id': competitionId,
                        'title': competition.title,
                        'organizer': competition.organizer,
                        'created_when': new Date(competition.created_when),
                        'datasets': competition.datasets * 1024
                    });
                });
                self.update({competitionsUsageTableData: competitionsUsageTableData});
            }
        }

        self.formatDate = function(date) {
            return datetime.fromJSDate(date).toISODate();
        }


        self.downloadCompetitionsHistory = function() {
            var csv = [];

            // Categories
            const competitions = Object.values(self.competitionsUsageData)[0];
            const competitions_id = Object.entries(competitions).map(([id, { title }]) => (id));
            const competitions_name = Object.entries(competitions).map(([id, { title }]) => (title));
            csv.push("," + competitions_id.join(","));
            csv.push("," + competitions_name.join(","));

            // Data points
            sorted_dates = Object.keys(self.competitionsUsageData).sort(function(a, b) {return new Date(a) - new Date(b)});
            for (const date of sorted_dates) {
                let points = [date];
                for (const id of competitions_id) {
                    points.push(self.competitionsUsageData[date][id]['datasets'] * 1024);
                }
                csv.push(points.join(","));
            }

            // Save
            const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
            saveAs(blob, "competitions_usage_history.csv");
        }

        self.downloadCompetitionsTable = function() {
            var csv = [];

            // Categories
            let categories = ['Competition', 'Organizer', 'Creation date', 'Datasets'];
            csv.push(categories.join(","));

            // Data points
            for (const competition of self.competitionsUsageTableData) {
                const points = [
                    competition.title,
                    competition.organizer,
                    competition.created_when.toLocaleString(),
                    competition.datasets * 1024
                ];
                csv.push(points.join(","));
            }

            // Save
            const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
            saveAs(blob, "competitions_table.csv");
        }
    </script>

    <style>
        th {
            border-bottom: 2px solid grey;
        }

        table {
            margin-bottom: 50px;
            width: 1000px;
        }

        canvas.big {
            height: 500px !important;
            width: 1000px !important;
        }

        .date-input {
            display: flex;
            flex-direction: column;
        }

        .start-date-input {
            margin-right: 40px;
        }

        .date-selection {
            display: flex;
            justify-content: space-between;
            flex-direction: row;
            background: #eee;
            margin-top: 30px;
            border-radius: 4px;
            padding: 10px;
            width: fit-content;
        }

        .chart-container {
            min-height: 450px;
        }

        .flex-row {
            display: flex;
            flex-direction: row;
        }
    </style>
</analytics-storage-competitions-usage>