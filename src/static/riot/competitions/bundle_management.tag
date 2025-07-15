<bundle-management>
    <!--  Search -->
    <div class="ui icon input">
        <input type="text" placeholder="Search..." ref="search" onkeyup="{ filter.bind(this, undefined) }">
        <i class="search icon"></i>
    </div>
    <button class="ui red right floated labeled icon button {disabled: marked_datasets.length === 0}" onclick="{delete_datasets}">
        <i class="icon delete"></i>
        Delete Selected
    </button>

    <!-- Data Table -->
    <table id="bundlesTable" class="ui {selectable: datasets.length > 0} celled compact sortable table">
        <thead>
            <tr>
                <th>File Name</th>
                <th>Benchmark</th>
                <th width="175px">Size</th>
                <th width="125px">Uploaded</th>
                <th width="50px" class="no-sort">Delete?</th>
                <th width="25px" class="no-sort"></th>
            </tr>
        </thead>

        <tbody>
            <tr each="{ dataset, index in datasets }"
                class="dataset-row"
                onclick="{show_info_modal.bind(this, dataset)}">
                <td>{ dataset.name }</td>
                <td>
                    <div if="{dataset.competition}" class="ui fitted">
                        <a id="competitionLink" href="{URLS.COMPETITION_DETAIL(dataset.competition.id)}" target="_blank">{dataset.competition.title}</a>
                    </div>
                </td>
                <td>{ pretty_bytes(dataset.file_size) }</td>
                <td>{ timeSince(Date.parse(dataset.created_when)) } ago</td>
                <td class="center aligned">
                    <button show="{dataset.created_by === CODALAB.state.user.username}" class="ui mini button red icon" onclick="{ delete_dataset.bind(this, dataset) }">
                        <i class="icon delete"></i>
                    </button>
                </td>
                <td class="center aligned">
                    <div show="{dataset.created_by === CODALAB.state.user.username}" class="ui fitted checkbox">
                        <input type="checkbox" name="delete_checkbox" onclick="{ mark_dataset_for_deletion.bind(this, dataset) }">
                        <label></label>
                    </div>
                </td>
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

    <!--  Dataset Detail Model  -->
    <div ref="info_modal" class="ui modal">
        <div class="header">
            {selected_row.name}
        </div>
        <div class="content">
            <h3>Details</h3>
            <table class="ui basic table">
                <thead>
                    <tr>
                        <th>Key</th>
                        <th>Created By</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{selected_row.key}</td>
                        <td><a href="/profiles/user/{selected_row.created_by}/" target=_blank>{selected_row.owner_display_name}</a></td>
                        <td>{pretty_date(selected_row.created_when)}</td>
                    </tr>
                </tbody>
            </table>
            <virtual if="{!!selected_row.description}">
                <div>Description:</div>
                <div class="ui segment">
                    {selected_row.description}
                </div>
            </virtual>
            <div show="{!!_.get(selected_row.in_use, 'length')}"><strong>Used by:</strong>
                <div class="ui bulleted list">
                    <div class="item" each="{comp in selected_row.in_use}">
                        <a href="{URLS.COMPETITION_DETAIL(comp.pk)}" target="_blank">{comp.title}</a>
                    </div>
                </div>
            </div>
        </div>
        <div class="actions">
            <a href="{URLS.DATASET_DOWNLOAD(selected_row.key)}" class="ui green icon button">
                <i class="download icon"></i>Download File
            </a>
            <button class="ui cancel button">Close</button>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/

        self.datasets = []
        self.marked_datasets = []
        self.selected_row = {}
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

        self.delete_dataset = function (dataset, e) {
            if (confirm(`Are you sure you want to delete '${dataset.name}'?`)) {
                CODALAB.api.delete_dataset(dataset.id)
                    .done(function () {
                        self.update_datasets()
                        toastr.success("Dataset deleted successfully!")
                        CODALAB.events.trigger('reload_quota_cleanup')
                    })
                    .fail(function (response) {
                        toastr.error(response.responseJSON['error'])
                    })
            }
            event.stopPropagation()
        }

        self.delete_datasets = function () {
            if (confirm(`Are you sure you want to delete multiple datasets?`)) {
                CODALAB.api.delete_datasets(self.marked_datasets)
                    .done(function () {
                        self.update_datasets()
                        toastr.success("Dataset deleted successfully!")
                        self.marked_datasets = []
                        CODALAB.events.trigger('reload_quota_cleanup')
                    })
                    .fail(function (response) {
                        for (e in response.responseJSON) {
                            toastr.error(`${e}: '${response.responseJSON[e]}'`)
                        }
                    })
            }
            event.stopPropagation()
        }

        self.mark_dataset_for_deletion = function(dataset, e) {
            if (e.target.checked) {
                self.marked_datasets.push(dataset.id)
            }
            else {
                self.marked_datasets.splice(self.marked_datasets.indexOf(dataset.id), 1)
            }
        }

        self.show_info_modal = function (row, e) {
            // Return here so the info modal doesn't pop up when a checkbox is clicked
            if (e.target.type === 'checkbox' || e.target.id === 'competitionLink') {
                return
            }
            self.selected_row = row
            self.update()
            $(self.refs.info_modal).modal('show')
        }


    </script>

</bundle-management>