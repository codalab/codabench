<analytics-storage-users-usage>
    <div class="flex-row">
        <select class="ui search multiple selection dropdown" multiple ref="users_dropdown">
            <i class="dropdown icon"></i>
            <div class="default text">Select Users</div>
            <div class="menu">
                <option each="{ user in usersDropdownOptions }" value="{ user.id }">{ user.name }</div> 
            </div>
        </select>
        <button class="ui button" onclick={selectTopFiveBiggestUsers}>Select top 5 biggest users</button>
        <button class="ui green button" onclick={downloadUsersHistory}>
            <i class="icon download"></i>Download as CSV
        </button>
        <h4 style="margin: 0 0 0 auto">{lastSnapshotDate ? "Last snaphost date: " + pretty_date(lastSnapshotDate) : "No snapshot has been taken yet"}</h4>
    </div>
    <div class='chart-container'>
        <canvas class="big" ref="storage_users_usage_chart"></canvas>
    </div>
    <div class="ui calendar" ref="users_table_date_calendar">
        <div class="ui input left icon">
            <i class="calendar icon"></i>
            <input type="text">
        </div>
    </div>
    <div style="display: flex; flex-direction: row">
        <div class='chart-container' style="width: 60%">
            <canvas ref="storage_users_usage_pie"></canvas>
        </div>
        <div class='chart-container' style="width: 40%; padding-left: 30px">
            <canvas ref="storage_users_usage_pie_details"></canvas>
        </div>
    </div>
    <button class="ui green button" onclick={downloadUsersTable}>
        <i class="icon download"></i>Download as CSV
    </button>
    <table id="storageUsersTable" class="ui selectable sortable celled table">
        <thead>
            <tr>
                <th is="su-th" data-sort-method="alphanumeric">User</th>
                <th is="su-th" class="date" data-sort-method="date">Joined at</th>
                <th is="su-th" class="bytes" data-sort-method="numeric">Datasets</th>
                <th is="su-th" class="bytes" data-sort-method="numeric">Submissions</th>
                <th is="su-th" class="bytes default-sort"data-sort-method="numeric">Total</th>
            </tr>
        </thead>
        <tbody>
            <tr each="{ userUsage in usersUsageTableData }">
                <td>{ userUsage.name }</td>
                <td>{ formatDate(userUsage.date_joined) }</td>
                <td>{ pretty_bytes(userUsage.datasets) }</td>
                <td>{ pretty_bytes(userUsage.submissions) }</td>
                <td>{ pretty_bytes(userUsage.datasets + userUsage.submissions) }</td>
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
        self.usersUsageData = null;
        self.usersDropdownOptions = [];
        self.usersTableSelectedDate = null;
        self.selectedUsers = [];
        self.usersColor = {};
        self.colors = ["#36a2eb", "#ff6384", "#4bc0c0", "#ff9f40", "#9966ff", "#ffcd56", "#c9cbcf"];
        self.storageUsersUsageChart;
        self.storageUsersUsagePieChart;
        self.storageUsersUsageDetailedPieChart;
        self.usersUsageTableData = [];
        self.selectedUserId = null;

        self.one("mount", function () {
            self.state.startDate = opts.start_date;
            self.state.endDate = opts.end_date;
            self.state.resolution = opts.resolution;

            // Semantic UI
            $(self.refs.users_dropdown).dropdown({
                onAdd: self.addUserToSelection,
                onRemove: self.removeUserFromSelection,
                clearable: true,
                preserveHTML: false,
            });

            $('#storageUsersTable').tablesort();
            $('#storageUsersTable thead th.date').data('sortBy', function(th, td, tablesort) {
                return new Date(td.text());
            });
            $('#storageUsersTable thead th.bytes').data('sortBy', function(th, td, tablesort) {
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
            let users_table_date_specific_options = {
                onChange: function(date, text) {
                    self.usersTableSelectedDate = date;
                    self.updateUsersTable();
                    self.updateUsersPieChart();
                }
            };
            let users_table_date_calendar_options = _.assign({}, general_calendar_options, users_table_date_specific_options);
            $(self.refs.users_table_date_calendar).calendar(users_table_date_calendar_options);

            // Line chart
            let storageUsersUsageConfig = {
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

            self.storageUsersUsageChart = new Chart($(self.refs.storage_users_usage_chart), storageUsersUsageConfig);

            // Pie chart
            let storageUsersUsagePieConfig = {
                type: 'pie',
                data: {
                    labels: [],
                    usersId: [],
                    datasets: [
                        {
                            label: 'Users distribution',
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
                        }
                    },
                    title: {
                        display: true,
                        text: 'Users distribution'
                    },
                    tooltips: {
                        callbacks: {
                            label: function(tooltipItem, data) {
                                const label = data.labels[tooltipItem.index];
                                const value = pretty_bytes(data.datasets[0].data[tooltipItem.index]);
                                return " " + label + ": " + value;
                            }
                        }
                    },
                    onClick: self.onStorageUsersUsagePieChartClick
                }
            };

            self.storageUsersUsagePieChart = new Chart($(self.refs.storage_users_usage_pie), storageUsersUsagePieConfig);

            // Detail pie chart
            const storageUsersDetailedUsagePieConfig = {
                type: 'pie',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'User details',
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
                            position: 'top',
                        }
                    },
                    title: {
                        display: true,
                        text: 'User details'
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
            self.storageUsersUsageDetailedPieChart = new Chart($(self.refs.storage_users_usage_pie_details), storageUsersDetailedUsagePieConfig);
        });

        self.on("update", function () {
            if (opts.is_visible && (self.state.startDate != opts.start_date || self.state.endDate != opts.end_date || self.state.resolution != opts.resolution)) {
                self.state.startDate = opts.start_date;
                self.state.endDate = opts.end_date;
                self.state.resolution = opts.resolution;
                self.get_users_usage(self.state.startDate, self.state.endDate, self.state.resolution);
            }
        });

        self.get_users_usage = function(start_date, end_date, resolution) {
            let parameters = {
                start_date: start_date,
                end_date: end_date,
                resolution: resolution
            };
            CODALAB.api.get_users_usage(parameters)
                .done(function(data) {
                    self.usersUsageData = data["users_usage"];
                    self.lastSnapshotDate = data["last_storage_calculation_date"];
                    self.update({lastSnapshotDate: data["last_storage_calculation_date"]});
                    self.updateUsersSelectionDropdown();
                    self.updateUsersTableCalendar(data["users_usage"]);
                    self.updateUsersChart();
                    self.updateUsersPieChart();
                    self.updateUsersTable();
                })
                .fail(function(error) {
                    toastr.error("Could not load storage analytics data");
                });
        }

        self.updateUsersSelectionDropdown = function () {
            // Update the options
            let usersOptions = [];
            if(Object.keys(self.usersUsageData).length > 0) {
                const users = Object.values(self.usersUsageData)[0];
                usersOptions = Object.entries(users).map(([id, { name }]) => ({ id, name }));
            }

            // Save
            self.usersDropdownOptions = usersOptions;
            $(self.refs.users_dropdown).dropdown('change values', usersOptions); // This triggers a reset of selected values
            self.update({usersDropdownOptions: usersOptions});
        }

        self.updateUsersTableCalendar = function(data) {
            // Set the min and max date of the calendar
            const minDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) < new Date(cur) ? acc : cur, '9999-12-31'));
            const maxDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur, '0000-00-00'));
            $(self.refs.users_table_date_calendar).calendar('setting', 'minDate', minDate);
            $(self.refs.users_table_date_calendar).calendar('setting', 'maxDate', maxDate);

            // Select the most current date available
            self.usersTableSelectedDate = maxDate;
            $(self.refs.users_table_date_calendar).calendar('set date', maxDate);
            $(self.refs.users_table_date_calendar).calendar('refresh');
        }

        self.addUserToSelection = function(value, text, $addedItem) {
            if(Object.keys(self.usersUsageData).length > 0) {
                self.selectedUsers.push(value);
                let userUsage = [];
                for (let [dateString, users] of Object.entries(self.usersUsageData)) {
                    for (let [userId, user] of Object.entries(users)) {
                        if (userId == value) {
                            userUsage.push({x: new Date(dateString), y: user.datasets * 1024});
                        }
                    }
                }
                const users = Object.values(self.usersUsageData)[0];
                const userName = users[value].name;
                if(!self.usersColor.hasOwnProperty(value)) {
                    self.usersColor[value] = self.colors[Object.keys(self.usersColor).length % self.colors.length];
                }
                const color = self.usersColor[value];

                // Update chart
                self.storageUsersUsageChart.data.datasets.push({
                    userId: value,
                    label: userName,
                    data: userUsage,
                    backgroundColor: color,
                    borderWidth: 1,
                    lineTension: 0,
                    fill: false
                });
                self.storageUsersUsageChart.update();

                // Update pie chart
                let selectedDate = self.usersTableSelectedDate;
                if (!selectedDate) {
                    selectedDate = new Date(Object.keys(self.usersUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
                }
                const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
                const closestOlderDateString = Object.keys(self.usersUsageData).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
                const usersAtSelectedDate = self.usersUsageData[closestOlderDateString];
                const selectedUsers = Object.keys(usersAtSelectedDate).filter(date => self.selectedUsers.includes(date)).reduce((user, date) => ({ ...user, [date]: usersAtSelectedDate[date] }), {});
                
                const {labels, usersId, data} = self.formatDataForUsersPieChart(selectedUsers);
                self.storageUsersUsagePieChart.data.labels = labels;
                self.storageUsersUsagePieChart.data.usersId = usersId;
                self.storageUsersUsagePieChart.data.datasets[0].data = data;
                self.storageUsersUsagePieChart.data.datasets[0].labels = labels;
                self.storageUsersUsagePieChart.data.datasets[0].backgroundColor = self.listOfColors(data.length);
                self.storageUsersUsagePieChart.update();
            }
        }

        self.formatDataForUsersPieChart = function (data) {
            var labels = [];
            var usersId = [];
            var formattedData = [];

            const userArray = Object.entries(data).map(([key, value]) => ({ ...value, id: key }));
            userArray.sort((a, b) => (b.datasets + b.submissions) - (a.datasets + a.submissions));
            for (const user of userArray) {
                labels.push(user.name);
                usersId.push(user.id);
                formattedData.push((user.datasets + user.submissions) * 1024);
            }

            return {labels: labels, usersId: usersId, data: formattedData};
        }

        self.listOfColors = function(arrayLength) {
            return Array.apply(null, Array(arrayLength)).map(function (x, i) { return self.colors[i%self.colors.length]; })
        }

        self.removeUserFromSelection = function(value, text, $removedItem) {
            // Remove from selection
            const indexToRemoveInSelected = self.selectedUsers.findIndex(userId => userId == value);
            if (indexToRemoveInSelected !== -1) {
                self.selectedUsers.splice(indexToRemoveInSelected, 1);
            }

            // Reassign users color
            self.usersColor = {};
            for(const userId of self.selectedUsers) {
                self.usersColor[userId] = self.colors[Object.keys(self.usersColor).length % self.colors.length];
            }

            // Remove from user usage chart
            let indexToRemove = self.storageUsersUsageChart.data.datasets.findIndex(dataset => dataset.userId == value);
            if (indexToRemove !== -1) {
                self.storageUsersUsageChart.data.datasets.splice(indexToRemove, 1);
                for(let dataset of self.storageUsersUsageChart.data.datasets) {
                    dataset.backgroundColor = self.usersColor[dataset.userId];
                }
                self.storageUsersUsageChart.update();
            }

            // Remove from user pie chart
            indexToRemove = self.storageUsersUsagePieChart.data.usersId.findIndex(id => id == value);
            if (indexToRemove !== -1) {
                self.storageUsersUsagePieChart.data.labels.splice(indexToRemove, 1);
                self.storageUsersUsagePieChart.data.usersId.splice(indexToRemove, 1);
                self.storageUsersUsagePieChart.data.datasets[0].data.splice(indexToRemove, 1);
                self.storageUsersUsagePieChart.data.datasets[0].backgroundColor.splice(indexToRemove, 1);
                self.storageUsersUsagePieChart.data.datasets[0].backgroundColor = self.storageUsersUsagePieChart.data.usersId.map(userId => self.usersColor[userId]);
                self.storageUsersUsagePieChart.update();
            }
        }

        self.selectTopFiveBiggestUsers = function () {
            let selectUsers = [];
            if (Object.keys(self.usersUsageData).length > 0) {
                const mostRecentDateString = Object.keys(self.usersUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur );
                let users = Object.entries(self.usersUsageData[mostRecentDateString]);
                users.sort((a, b) => (b[1].datasets + b[1].submissions) - (a[1].datasets + a[1].submissions));
                selectUsers = users.slice(0, 5).map(([id]) => id);
            }
            for(const userId of selectUsers) {
                $(self.refs.users_dropdown).dropdown('set selected', userId);
            }
        }

        self.updateUsersChart = function() {
            if(Object.keys(self.usersUsageData).length > 0) {
                const selectedUsers = Object.fromEntries(
                    Object.entries(self.usersUsageData).map(([dateString, users]) => [
                        dateString,
                        Object.fromEntries(
                            Object.entries(users).filter(([userId]) => self.selectedUsers.includes(userId))
                        )
                    ])
                );
                
                const usersUsage = {};
                for (let [dateString, users] of Object.entries(selectedUsers)) {
                    for (let [userId, user] of Object.entries(users)) {
                        if (!usersUsage.hasOwnProperty(userId)) {
                            usersUsage[userId] = [];
                        }
                        usersUsage[userId].push({x: new Date(dateString), y: user.datasets * 1024});
                    }
                }

                self.storageUsersUsageChart.data.datasets = [];
                let index = 0;
                for(let [userId, dataset] of Object.entries(usersUsage)) {
                    const color = self.colors[index % self.colors.length];
                    const name = Object.values(self.usersUsageData)[0][userId].name;
                    self.storageUsersUsageChart.data.datasets.push({
                        userId: userId,
                        label: name,
                        data: dataset,
                        backgroundColor: color,
                        borderWidth: 1,
                        lineTension: 0,
                        fill: false
                    });
                    index++;
                }

                self.storageUsersUsageChart.update();
            }
        }

        self.updateUsersPieChart = function() {
            let selectedDate = self.usersTableSelectedDate;
            if (!selectedDate) {
                selectedDate = new Date(Object.keys(self.usersUsageData).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
            }
            const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
            const closestOlderDateString = Object.keys(self.usersUsageData).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
            const usersAtSelectedDate = self.usersUsageData[closestOlderDateString];
            const selectedUsers = Object.keys(usersAtSelectedDate).filter(date => self.selectedUsers.includes(date)).reduce((user, date) => ({ ...user, [date]: usersAtSelectedDate[date] }), {});

            const {labels, usersId, data} = self.formatDataForUsersPieChart(selectedUsers);
            self.storageUsersUsagePieChart.data.labels = labels;
            self.storageUsersUsagePieChart.data.usersId = usersId;
            self.storageUsersUsagePieChart.data.datasets[0].data = data;
            self.storageUsersUsagePieChart.data.datasets[0].labels = labels;
            self.storageUsersUsagePieChart.data.datasets[0].backgroundColor = self.listOfColors(data.length);
            self.storageUsersUsagePieChart.update();
        }

        self.updateUsersTable = function() {
            const data = self.usersUsageData;
            let usersUsageTableData = [];
            if (Object.keys(data).length > 0) {
                let selectedDate = self.usersTableSelectedDate;
                if (!selectedDate) {
                    selectedDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
                }
                const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
                const closestOlderDateString = Object.keys(data).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
                const users = data[closestOlderDateString];
                Object.entries(users).forEach(keyValue => {
                    const [userId, user] = keyValue;
                    usersUsageTableData.push({
                        'id': userId,
                        'name': user.name,
                        'date_joined': new Date(user.date_joined),
                        'datasets': user.datasets * 1024,
                        'submissions': user.submissions * 1024
                    });
                });
                self.update({usersUsageTableData: usersUsageTableData});
            }
        }

        self.onStorageUsersUsagePieChartClick = function(event, activeElements) {
            if (activeElements.length > 0) {
                const userId = self.storageUsersUsagePieChart.data.usersId[activeElements[0]._index];
                if (self.selectedUserId != userId) {
                    const data = self.usersUsageData;
                    let selectedDate = self.usersTableSelectedDate;
                    if (!selectedDate) {
                        selectedDate = new Date(Object.keys(data).reduce((acc, cur) => new Date(acc) > new Date(cur) ? acc : cur , '0000-00-00'));
                    }
                    const selectedDateString = selectedDate.getUTCFullYear() + "-" + (selectedDate.getUTCMonth()+1) + "-" + selectedDate.getUTCDate();
                    const closestOlderDateString = Object.keys(data).reduce((acc, cur) => (Math.abs(new Date(selectedDateString) - new Date(cur)) < Math.abs(new Date(selectedDateString) - new Date(acc)) && (new Date(selectedDateString) - new Date(cur) >= 0)) ? cur : acc, '9999-12-31');
                    const users = data[closestOlderDateString];
                    const userData = users[userId];
                    const datasets_data = [
                        userData.datasets * 1024,
                        userData.submissions * 1024,
                    ];
                    const labels = [
                        "datasets",
                        "submissions"
                    ];
                    self.storageUsersUsageDetailedPieChart.data.labels = labels;
                    self.storageUsersUsageDetailedPieChart.data.datasets[0].data = datasets_data;
                    self.storageUsersUsageDetailedPieChart.data.datasets[0].labels = labels;
                    self.storageUsersUsageDetailedPieChart.data.datasets[0].backgroundColor = ["#36a2eb", "#ff6384"];
                    self.storageUsersUsageDetailedPieChart.options.title = {display: true, text: userData.name};
                    self.selectedUserId = userId;
                    self.storageUsersUsageDetailedPieChart.update();
                }
            }
        }

        self.formatDate = function(date) {
            return datetime.fromJSDate(date).toISODate();
        }

        self.downloadUsersHistory = function() {
            var csv = [];

            // Categories
            const users = Object.values(self.usersUsageData)[0];
            const users_id = Object.entries(users).map(([id, { name }]) => (id));
            const users_name = Object.entries(users).map(([id, { name }]) => (name));
            csv.push("," + users_id.join(","));
            csv.push("," + users_name.join(","));

            // Data points
            sorted_dates = Object.keys(self.usersUsageData).sort(function(a, b) {return new Date(a) - new Date(b)});
            for (const date of sorted_dates) {
                let points = [date];
                for (const id of users_id) {
                    points.push((self.usersUsageData[date][id]['datasets'] + self.usersUsageData[date][id]['submissions']) * 1024);
                }
                csv.push(points.join(","));
            }

            // Save
            const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
            saveAs(blob, "users_usage_history.csv");
        }

        self.downloadUsersTable = function() {
            var csv = [];

            // Categories
            let categories = ['User', 'Joined at', 'Datasets', 'Submissions', 'Total'];
            csv.push(categories.join(","));

            // Data points
            for (const user of self.usersUsageTableData) {
                const points = [
                    user.name,
                    user.date_joined.toLocaleString(),
                    user.datasets * 1024,
                    user.submissions * 1024,
                    (user.datasets + user.submissions) * 1024
                ];
                csv.push(points.join(","));
            }

            // Save
            const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
            saveAs(blob, "users_table.csv");
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
</analytics-storage-users-usage>