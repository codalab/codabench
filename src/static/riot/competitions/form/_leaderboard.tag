<competition-leaderboards>
    <button class="ui primary button modal-button" ref="modal_button">
        <i class="add circle icon"></i> Add leaderboard
    </button>

    <h1>Leaderboard</h1>
    <table class="ui compact celled stackable small table table-bordered definition">
        <thead>
        <tr>
            <th class="right aligned" width="175px">

            </th>
            <!--<th>
                <button class="ui tiny blue icon button" onclick="{ add_column }">
                    <i class="add square icon"></i> Add column
                </button>
            </th>-->
            <th each="{ column, index in columns }" class="center aligned" width="175px">
                <i class="left floated chevron left icon" show="{ !column.editing && index > 0 }" onclick="{ move_left.bind(this, index) }"></i>


                <span show="{ !column.editing }" onclick="{ edit_column_name.bind(this, column, index) }">
                <!--<span onclick="{ column.editing = true }">-->
                    <i class="icon pencil small"></i> { column.name }
                </span>

                <div class="ui input" show="{ column.editing }">
                    <input id="column_input_{ index }" type="text" value="{ column.name }" onkeydown="{ edit_column_name_submit.bind(this, column) }">
                </div>

                <i class="right floated chevron right icon" show="{ !column.editing && index + 1 < columns.length }" onclick="{ move_right.bind(this, index) }"></i>
                <!--<select>
                    <option selected>
                        ------
                    </option>
                    <option></option>
                </select>-->
            </th>
            <th></th>
        </tr>
        </thead>
        <tbody>
        <tr class="ui aligned right">
            <td>Primary Column?</td>
            <td each="{ columns }" class="center aligned">
                <input type="radio">
            </td>
            <td></td> <!-- Empty cell so it cuts off nicely at the end of rows -->
        </tr>

        <tr class="ui aligned right">
            <td>
                <span data-tooltip="This operation is applied to every other column" data-inverted="" data-position="right center">
                    Applied computation <i class="help icon circle"></i>
                </span>
            </td>
            <td each="{ column, index in columns }" class="center aligned">
                <div class="ui field">
                    <select class="ui fluid small dropdown" onchange="{ edit_column_type.bind(this, column) }">
                        <option selected>
                            ------
                        </option>
                        <option>Average</option>
                    </select>
                </div>
                <div class="ui field" show="{ column.computation }">
                    <label>Apply to:</label>
                    <select class="ui fluid small multiselect" multiple="">
                        <option each="{ inner_column, inner_index in columns }" show="{ index != inner_index }"> { inner_column.name }</option>
                    </select>
                </div>
            </td>
            <td></td>
        </tr>

        <tr class="ui aligned right">
            <td>Sorting</td>
            <td each="{ columns }" class="center aligned">
                <select class="ui fluid small dropdown">
                    <option selected>Descending</option>
                    <option>Ascending</option>
                </select>
            </td>
            <td></td>
        </tr>
        </tbody>

        <tfoot class="full-width">
        <tr>
            <th></th>
            <th colspan="{ columns.length + 1}">
                <button class="ui  small primary labeled icon button" onclick="{ add_column }">
                    <i class="add square icon"></i> Add column
                </button>
            </th>
        </tr>
        </tfoot>
    </table>

    <script>
        var self = this

        self.columns = [
            {name: "Score"}
        ]

        self.one("mount", function () {
            //$(".tooltip").popup()
            $(".dropdown").dropdown()
        })

        self.on("update", function () {
            // Force refresh of dropdown on update, otherwise they don't show new elements and
            // don't reflect new names
            //$(".dropdown").dropdown("refresh")
        })

        self.add_column = function () {
            self.columns.push({name: "Score2"})
            self.update()
            $(".dropdown").dropdown("refresh")
        }

        self.edit_column_name = function (column, index) {
            column.editing = true
            self.update()
            $("#column_input_" + index).focus()
        }

        self.edit_column_type = function (column, event) {
            column.computation = event.target.value
        }

        self.edit_column_name_submit = function (column, event) {
            if (event.keyCode === 13) {
                column.name = event.target.value
                column.editing = false
                console.log(column.name)
            }
        }

        self.move_left = function (index) {
            self.move(index, -1)
        }

        self.move_right = function (index) {
            self.move(index, 1)
        }
        self.move = function (index, offset) {
            var data_to_move = self.columns[index]

            // Remove the item
            self.columns.splice(index, 1)

            // Add 1 item offset up OR down
            self.columns.splice(index + offset, 0, data_to_move)

            self.update()
        }
    </script>

    <style>
        :scope {

        }

        .multiselect {
            width: 100%;
            margin-top: 5px;
            padding: 5px;
            border: 1px solid rgba(34, 36, 38, .15);
            border-radius: .28571429rem;
        }

        .chevron.icon {
            color: rgba(34, 36, 38, .25);
            cursor: pointer;
        }

        .chevron.icon:hover {
            color: rgba(34, 36, 38, .55);
        }

        .chevron.floated.left {
            float: left;
        }

        .chevron.floated.right {
            float: right;
        }
    </style>
</competition-leaderboards>