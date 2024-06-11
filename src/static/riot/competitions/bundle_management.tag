<bundle-management>
    <!--  Search -->
    <div class="ui icon input">
        <input type="text" placeholder="Search..." ref="search" onkeyup="{ filter.bind(this, undefined) }">
        <i class="search icon"></i>
    </div>

    <!-- Data Table -->
    <table id="bundlesTable" class="ui {selectable: datasets.length > 0} celled compact sortable table">
        <thead>
            <tr>
                <th>File Name</th>
                <th width="175px">Size</th>
                <th width="125px">Uploaded</th>
            </tr>
        </thead>

        <tbody>
            <tr each="{ dataset, index in datasets }" class="dataset-row">
                <td>{ dataset.name }</td>
                <td>{ format_file_size(dataset.file_size) }</td>
                <td>{ timeSince(Date.parse(dataset.created_when)) } ago</td>
            </tr>
            <tr if="{datasets.length === 0}">
                <td class="center aligned" colspan="6">
                    <em>No Datasets Yet!</em>
                </td>
            </tr>
        </tbody>

        <tfoot>
            <!-- Pagination -->
            <tr>
                <th colspan="8" if="{datasets.length > 0}">
                    <div class="ui right floated pagination menu" if="{datasets.length > 0}">
                        <a show="{!!_.get(pagination, 'previous')}" class="icon item" onclick="{previous_page}">
                            <i class="left chevron icon"></i>
                        </a>
                        <div class="item">
                            <label>{page}</label>
                        </div>
                        <a show="{!!_.get(pagination, 'next')}" class="icon item" onclick="{next_page}">
                            <i class="right chevron icon"></i>
                        </a>
                    </div>
                </th>
            </tr>
        </tfoot>
    </table>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/

        self.datasets = []
        self.page = 1

        self.one("mount", function () {
            $(".ui.dropdown", self.root).dropdown()
            $(".ui.checkbox", self.root).checkbox()
            $('#bundlesTable').tablesort()
            self.update_datasets()
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/

        self.pretty_date = date => luxon.DateTime.fromISO(date).toLocaleString(luxon.DateTime.DATE_FULL)

        self.filter = function (filters) {
            filters = filters || {}
            _.defaults(filters, {
                search: $(self.refs.search).val(),
                page: 1,
            })
            self.page = filters.page
            self.update_datasets(filters)
        }

        self.next_page = function () {
            if (!!self.pagination.next) {
                self.page += 1
                self.filter({page: self.page})
            } else {
                alert("No valid page to go to!")
            }
        }

        self.previous_page = function () {
            if (!!self.pagination.previous) {
                self.page -= 1
                self.filter({page: self.page})
            } else {
                alert("No valid page to go to!")
            }
        }

        self.update_datasets = function (filters) {
            filters = filters || {}
            filters._type = "bundle"
            CODALAB.api.get_datasets(filters)
                .done(function (data) {
                    self.datasets = data.results
                    self.pagination = {
                        "count": data.count,
                        "next": data.next,
                        "previous": data.previous
                    }
                    self.update()
                })
                .fail(function (response) {
                    toastr.error("Could not load datasets...")
                })
        }

        // Function to format file size 
        self.format_file_size = function(file_size) {
            // parse file size from string to float
            try {
                n = parseFloat(file_size)
            }
            catch(err) {
                // return empty string if parsing fails
                return ""
            }
            // a file_size of -1 indicated an error
            if(n < 0) {
                return ""
            }
            // constant units to show with files size
            // file size is in KB, converting it to MB and GB 
            const units = ['KB', 'MB', 'GB']
            // loop incrementer for selecting desired unit
            let i = 0
            // loop over n until it is greater than 1000
            while(n >= 1000 && ++i){
                n = n/1000;
            }
            // restrict file size to 1 decimal number concatinated with unit
            return(n.toFixed(1) + ' ' + units[i]);
        }

    </script>

</bundle-management>