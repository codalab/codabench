<dashboard-competitions-table>
    <div class="ui segment table-card">
        <div class="table-top-bar">
            <h3 class="ui header" style="margin: 0;">
                Competitions ({ (opts.p.filteredCompetitions || []).length })
            </h3>
            <button class="ui green button" onclick="{ downloadCSV }">
                <i class="icon download"></i>Download as CSV
            </button>
        </div>

        <div class="table-scroll-wrap" style="max-height: 480px; overflow-y: auto; overflow-x: auto; -webkit-overflow-scrolling: touch;">
            <table class="ui celled compact striped selectable table">
                <thead>
                    <tr>
                        <th onclick="{ sortTableId }" style="cursor: pointer; width: 60px;">ID <i class="{ sortKey === 'id' ? (sortDir === 1 ? 'sort down' : 'sort up') : 'sort' } icon"></i></th>
                        <th onclick="{ sortTableTitle }" style="cursor: pointer;">Title <i class="{ sortKey === 'title' ? (sortDir === 1 ? 'sort down' : 'sort up') : 'sort' } icon"></i></th>
                        <th onclick="{ sortTableOrg }" style="cursor: pointer; width: 140px;">Organizer <i class="{ sortKey === 'organizer' ? (sortDir === 1 ? 'sort down' : 'sort up') : 'sort' } icon"></i></th>
                        <th each="{ cat in (opts.p.availableCategories || []) }">{ cat }</th>
                        <th style="width: 70px; text-align: center;">Link</th>
                    </tr>
                </thead>
                <tbody>
                    <tr each="{ comp in pagedCompetitions }">
                        <td>{ comp.id }</td>
                        <td>
                            <strong><a href="{ comp.url }">{ comp.title }</a></strong>
                            <i if="{ comp.has_reward }" class="trophy yellow icon" title="Reward: { comp.reward }"></i>
                        </td>
                        <td>{ comp.organizer }</td>
                        <td each="{ colStr in comp.categoryColumns }">
                            <span if="{ colStr }" class="tag-cell-present">{ colStr }</span>
                            <span if="{ !colStr }" class="tag-cell-empty">—</span>
                        </td>
                        <td class="center aligned">
                            <a href="{ comp.url }" class="ui mini primary icon button" target="_blank" title="View Competition">
                                <i class="external alternate icon"></i>
                            </a>
                        </td>
                    </tr>
                    <tr if="{ !opts.p.filteredCompetitions || opts.p.filteredCompetitions.length === 0 }">
                        <td colspan="{ 4 + (opts.p.availableCategories || []).length }" class="center aligned table-empty-row">
                            <em>No competitions match the selected filters.</em>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="pagination-footer" if="{ totalPages > 1 }">
            <div class="ui secondary compact menu">
                <a class="item { disabled: currentPage === 1 }" onclick="{ changePagePrev }">
                    <i class="chevron left icon"></i> Prev
                </a>
                <div class="item">Page { currentPage } of { totalPages }</div>
                <a class="item { disabled: currentPage === totalPages }" onclick="{ changePageNext }">
                    Next <i class="chevron right icon"></i>
                </a>
            </div>
        </div>
    </div>

    <script>
        var self = this;

        // Table Pagination & Sorting State
        self.pageSize = 15;
        self.currentPage = 1;
        self.totalPages = 1;
        self.sortKey = 'id';
        self.sortDir = -1;
        self.pagedCompetitions = [];

        self.sortTableId = function () { self.sortTable('id'); };
        self.sortTableTitle = function () { self.sortTable('title'); };
        self.sortTableOrg = function () { self.sortTable('organizer'); };

        self.sortTable = function (key) {
            if (self.sortKey === key) {
                self.sortDir *= -1;
            } else {
                self.sortKey = key;
                self.sortDir = 1;
            }
            self.update();
        };

        self.changePagePrev = function () {
            if (self.currentPage > 1) {
                self.currentPage--;
                self.update();
            }
        };

        self.changePageNext = function () {
            if (self.currentPage < self.totalPages) {
                self.currentPage++;
                self.update();
            }
        };

        self.applyTableSortAndPage = function () {
            var rows = (opts.p && opts.p.filteredCompetitions) ? opts.p.filteredCompetitions.slice() : [];
            var k = self.sortKey;
            var dir = self.sortDir;

            rows.sort(function (a, b) {
                var va = a[k] || 0;
                var vb = b[k] || 0;
                if (typeof va === 'string') va = va.toLowerCase();
                if (typeof vb === 'string') vb = vb.toLowerCase();
                if (va < vb) return -1 * dir;
                if (va > vb) return 1 * dir;
                return 0;
            });

            self.totalPages = Math.max(1, Math.ceil(rows.length / self.pageSize));
            self.currentPage = Math.min(Math.max(1, self.currentPage), self.totalPages);

            var start = (self.currentPage - 1) * self.pageSize;
            self.pagedCompetitions = rows.slice(start, start + self.pageSize);
        };

        self.downloadCSV = function (e) {
            if (e) e.preventDefault();
            var rows = (opts.p && opts.p.filteredCompetitions) || [];
            if (rows.length === 0) return;
            var esc = (opts.p && opts.p.escapeCsv) || function (v) { return '"' + String(v || '').replace(/"/g, '""') + '"'; };
            var cats = (opts.p && opts.p.availableCategories) || [];
            var headers = ["id", "title", "organizer", "competition_type", "published", "participants_count", "submissions_count", "reward", "created_when"].concat(cats).map(esc);
            var lines = [headers.join(",")];
            rows.forEach(function (c) {
                var rowData = [
                    c.id,
                    esc(c.title),
                    esc(c.organizer),
                    esc(c.competition_type),
                    c.published ? "true" : "false",
                    c.participants_count || 0,
                    c.submissions_count || 0,
                    esc(c.reward || ""),
                    esc(c.created_when ? c.created_when.split("T")[0] : "")
                ];
                cats.forEach(function (cat) {
                    var tArr = (c.tagsByCategory && c.tagsByCategory[cat]) || [];
                    rowData.push(esc(tArr.join("; ")));
                });
                lines.push(rowData.join(","));
            });
            if (opts.p && opts.p.downloadCsv) {
                opts.p.downloadCsv("codabench_competitions_export.csv", lines);
            }
        };

        self.on('mount', function () {
            self.applyTableSortAndPage();
        });

        self.on('update', function () {
            self.applyTableSortAndPage();
        });
    </script>
</dashboard-competitions-table>
