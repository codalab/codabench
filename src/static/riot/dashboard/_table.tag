<dashboard-table>
    <div class="dashboard-tab-pane" show="{ opts.p.activeTab === 'explorer' }">
        <dashboard-data-explorer p="{ opts.p }"></dashboard-data-explorer>
        <dashboard-competitions-table p="{ opts.p }"></dashboard-competitions-table>
    </div>
</dashboard-table>