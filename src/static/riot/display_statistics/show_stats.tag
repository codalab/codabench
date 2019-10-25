<show-stats>
    <div class="ui six column grid">
        <div class="column" each="{ stat in general_stats }" no-reorder>
            <div class="ui six small statistics">
                <div class="statistic">
                    <div class="value">
                        { stat.count }
                    </div>
                    <div class="label">
                        { stat.label }
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this
        self.show_stats = false
        self.general_stats = {}

        self.on("mount", function () {
            $(".tooltip", self.root).popup()
            self.get_general_stats()
        })

        self.get_general_stats = function () {
            CODALAB.api.by_the_numbers()
                .done(function (data) {
                    self.general_stats = _.map(data, stat => {
                        stat.count = self.num_formatter(stat.count)
                        return stat
                    })
                    self.update()
                })
        }


        self.num_formatter = function(num, digits) {
            var si = [
                {value: 1, symbol: ""},
                {value: 1E3, symbol: "K"},
                {value: 1E6, symbol: "M"},
                {value: 1E9, symbol: "G"},
                {value: 1E12, symbol: "T"},
                {value: 1E15, symbol: "P"},
                {value: 1E18, symbol: "E"}
            ]
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/
            var i
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break
                }
            }
            return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol
        }
    </script>

    <style type="text/stylus">
        :scope

            .ui.statistics > .statistic
                flex 1 1 auto

                .value
                    font-weight 800

                .label
                    font-weight 100
    </style>
</show-stats>