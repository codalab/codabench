<analytics>
    <h1>Analytics</h1>


    <div class='date-selection'>
        <div class='date-pickers'>
            <p>Start Date <input type='text' class='date-picker' id='start-date-picker' placeholder="{start_date}"></p>
            <p>End Date <input type='text' class='date-picker' id='end-date-picker' placeholder="{end_date}"></p>
        </div>
        <div class='date-submit'>
            <button id='update-data'>Update Data</button>
        </div>
    </div>

    <h2>Competition Data</h2>

    <table>
        <tr>
            <th>Competitions</th>
            <th>Published Competitions</th>
        </tr>
        <tr>
            <td>{competitions}</td>
            <td>{competitions_published}</td>
        </tr>
    </table>

    <div each="{year, y in competitions_monthly}">
        <h3>{y}</h3>
        <table>
            <tr>
                <th each="{month_count, month in year}">{month}</th>
            </tr>
            <tr>
                <td each="{month_count, month in year}">{month_count}</th>
            </tr>
        </table>
    </div>


    <h2>User Data</h2>

    <table>
        <tr>
            <th>Users</th>
        </tr>
        <tr>
            <td>{users_total}</td>
        </tr>
    </table>

    <div each="{year, y in users_monthly}">
        <h3>{y}</h3>
        <table>
            <tr>
                <th each="{month_count, month in year}">{month}</th>
            </tr>
            <tr>
                <td each="{month_count, month in year}">{month_count}</th>
            </tr>
        </table>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.errors = []


        self.one("mount", function () {
            console.log("analytics mounted")
            // Make semantic elements work
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()

            $('.date-picker').datepicker();

            // init
            start_date = {
                year: 2010,
                month: 0
            }

            self.update_analytics(start_date, null)

        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/

        self.update_analytics= function (start, end) {

            var start_date = new Date(start.year, start.month)
            if (end) {
                var end_date = new Date(end.year, end.month)
            } else {
                var end_date = new Date()
                end_date.setDate(end_date.getDate() + 1)
            }


            console.log(start_date.toJSON().slice(0,10))
            console.log(end_date.toJSON().slice(0,10))

            CODALAB.api.get_analytics(start_date.toJSON().slice(0,10), end_date.toJSON().slice(0,10))
                .done(function (data) {
                    console.log(data)
                    self.update({
                    users_monthly: data.monthly_total_users_joined,
                    users_total: data.registered_user_count,
                    competitions: data.competition_count,
                    competitions_monthly: data.monthly_competitions_created,
                    competitions_published: data.competitions_published_count,
                    start_date: data.start_date,
                    end_date: data.end_date,
                    })
                })
                .fail(function (response) {
                    toastr.error("Could not load analytics data...")
                })
        }

        $(document).on('click', '#update-data', function() {
            let start = $('#start-date-picker').val().split('/')
            let end = $('#end-date-picker').val().split('/')

            if (start.length == 3) {
                console.log('start exists')
                console.log(start)

                let start_date = {
                    year: parseInt(start[2]),
                    month: parseInt(start[0]),
                }

                if (end.length == 3) {
                    console.log('end exists')

                    var end_date = {
                        year: parseInt(end[2]),
                        month: parseInt(end[0]),
                    }
                } else {
                    var end_date = null;
                }
                console.log(start_date)
                console.log(end_date)
                self.update_analytics(start_date, end_date)
            }
        });


    </script>
    <style>
        th {
            border-bottom: 2px solid grey;
        }

        table {
            margin-bottom: 50px;
        }

        h1, h2 {
            margin-bottom: 20px;
            margin-top: 80px;
        }

        .date-selection {
            display: flex;
            align-items: start;
            flex-direction: column
        }
        .date-pickers {
            display: flex;
        }

        .date-pickers p {
            margin-right: 15px;
        }

        .date-submit {
            margin-top: 15px;
        }

        .date-submit button {
            border-radius: 3px;
            margin-top: 200px;
            height: 35px;
        }

        .black-bg {
            background: #000;
        }
    </style>

</analytics>
