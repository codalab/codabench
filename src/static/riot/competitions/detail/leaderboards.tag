<leaderboards>
    <table each="{ leaderboard in opts.leaderboards }" class="ui celled selectable inverted table">
        <thead>
        <tr>
            <th colspan="100%" style="text-align: center;">
                { leaderboard.title }
            </th>
        </tr>
        <tr>
            <th>#</th>
            <th each="{ column in leaderboard.columns }">{ column.title }</th>
            <th class="right aligned">Status</th>
        </tr>
        </thead>
        <tbody>
        <tr>
            <td class="collapsing">
                1
            </td>
            <td>1.0</td>
            <td class="right aligned collapsing">Submitting</td>
        </tr>
        </tbody>
    </table>
    <script>
        var self = this
    </script>
    <style type="text/stylus">
        .ui.inverted.table
            background #44586b
    </style>
</leaderboards>