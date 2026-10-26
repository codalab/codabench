<dashboard-table>
    <div class="ui segment table-card">
        <div class="table-top-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 class="ui header" style="margin: 0;">
                Competitions ({ opts.p.filteredCompetitions.length })
            </h3>
            <button class="ui green button" onclick="{ downloadCSV }">
                <i class="icon download"></i>Download as CSV
            </button>
        </div>

        <div class="table-scroll-wrap" style="max-height: 480px; overflow-y: auto; overflow-x: auto; -webkit-overflow-scrolling: touch;">
            <table class="ui celled compact striped selectable table">
                <thead>
                    <tr>
                        <th onclick="{ sortTableId }" style="cursor: pointer; width: 60px;">ID <i class="{ opts.p.state.sortKey === 'id' ? (opts.p.state.sortDir === 1 ? 'sort down' : 'sort up') : 'sort' } icon"></i></th>
                        <th onclick="{ sortTableTitle }" style="cursor: pointer;">Title <i class="{ opts.p.state.sortKey === 'title' ? (opts.p.state.sortDir === 1 ? 'sort down' : 'sort up') : 'sort' } icon"></i></th>
                        <th onclick="{ sortTableOrg }" style="cursor: pointer; width: 140px;">Organizer <i class="{ opts.p.state.sortKey === 'organizer' ? (opts.p.state.sortDir === 1 ? 'sort down' : 'sort up') : 'sort' } icon"></i></th>
                        <th each="{ cat in opts.p.availableCategories }">{ cat }</th>
                        <th style="width: 70px; text-align: center;">Link</th>
                    </tr>
                </thead>
                <tbody>
                    <tr each="{ comp in opts.p.pagedCompetitions }">
                        <td>{ comp.id }</td>
                        <td>
                            <strong><a href="{ comp.url }">{ comp.title }</a></strong>
                            <i if="{ comp.has_reward }" class="trophy yellow icon" title="Reward: { comp.reward }"></i>
                        </td>
                        <td>{ comp.organizer }</td>
                        <td each="{ colStr in comp.categoryColumns }">
                            <span if="{ colStr }" style="color: #1678c2; font-weight: bold; font-size: 12px;">{ colStr }</span>
                            <span if="{ !colStr }" style="color: #888;">—</span>
                        </td>
                        <td class="center aligned">
                            <a href="{ comp.url }" class="ui mini primary icon button" target="_blank" title="View Competition">
                                <i class="external alternate icon"></i>
                            </a>
                        </td>
                    </tr>
                    <tr if="{ opts.p.filteredCompetitions.length === 0 }">
                        <td colspan="{ 4 + opts.p.availableCategories.length }" class="center aligned" style="padding: 20px; color: #888;">
                            <em>No competitions match the selected filters.</em>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="pagination-footer" if="{ opts.p.totalPages > 1 }" style="display: flex; justify-content: center; align-items: center; margin-top: 12px; gap: 10px;">
            <div class="ui secondary compact menu">
                <a class="item { disabled: opts.p.currentPage === 1 }" onclick="{ changePagePrev }">
                    <i class="chevron left icon"></i> Prev
                </a>
                <div class="item">Page { opts.p.currentPage } of { opts.p.totalPages }</div>
                <a class="item { disabled: opts.p.currentPage === opts.p.totalPages }" onclick="{ changePageNext }">
                    Next <i class="chevron right icon"></i>
                </a>
            </div>
        </div>
    </div>

    <script>
        var self = this;
        self.downloadCSV = (e) => {
            opts.p.downloadCSV(e);
        };
        self.sortTableId = (e) => {
            opts.p.sortTableId(e);
        };
        self.sortTableTitle = (e) => {
            opts.p.sortTableTitle(e);
        };
        self.sortTableOrg = (e) => {
            opts.p.sortTableOrg(e);
        };
        self.changePagePrev = (e) => {
            opts.p.changePagePrev(e);
        };
        self.changePageNext = (e) => {
            opts.p.changePageNext(e);
        };
    </script>

    <style type="text/stylus">
        dashboard-table
            display block
            width 100%
            margin-top 20px

        .table-card
            background #fff !important
            margin-top 20px !important

        .table-scroll-wrap
            width 100%
            overflow-x auto
            -webkit-overflow-scrolling touch
    </style>
</dashboard-table>