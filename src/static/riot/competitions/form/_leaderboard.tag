<competition-leaderboards-form>
    <button class="ui primary button modal-button" onclick="{ add }">
        <i class="add circle icon"></i> Add leaderboard
    </button>

    <div class="ui fluid styled accordion" show="{leaderboards.length !== 0}">
        <virtual each="{ leaderboard, index in leaderboards }">
            <div class="title { active: leaderboard.is_active }">
                <h1>
                    <span class="trigger"><i class="dropdown icon"></i> { leaderboard.title }</span>
                    <span class="key"> Key: { leaderboard.key }</span>
                    <sorting-chevrons data="{ leaderboards }" index="{ index }" onupdate="{ form_updated }"></sorting-chevrons>
                    <div class="ui right floated buttons">
                        <div class="ui negative button" onclick="{ delete_leaderboard.bind(this, index) }">
                            <i class="delete icon"></i>
                            Delete
                        </div>
                        <div class="ui button" onclick="{ edit.bind(this, index) }">
                            <i class="pencil icon"></i>
                            Edit
                        </div>
                    </div>
                </h1>
            </div>
            <div class="content { active: leaderboard.is_active }">
                <competition-leaderboard-form-table columns="{ leaderboard.columns }" primary_index="{ leaderboard.primary_index }" leaderboard_index="{index}"></competition-leaderboard-form-table>
            </div>
        </virtual>
    </div>

    <div class="ui container center aligned grid" show="{ leaderboards.length == 0 }">
        <div class="row">
            <div class="four wide column">
                <i>No leaderboards added yet, at least 1 is required!</i>
            </div>
        </div>
    </div>

    <div class="ui modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Leaderboard form
        </div>
        <div class="content">
            <form class="ui form" onsubmit="{ save }">
                <div class="field required">
                    <label>Title</label>
                    <input ref="title"/>
                </div>
                <div class="field required">
                    <label>
                        Key
                        <span data-tooltip="This is the key you will use to assign scores to leaderboards in your scoring program" data-inverted="" data-position="right center">
                            <i class="help icon circle"></i>
                        </span>
                    </label>
                    <input ref="key"/>
                </div>
            </form>
        </div>
        <div class="actions">
            <div class="ui button" onclick="{ close_modal }">Cancel</div>
            <div class="ui button primary" onclick="{ save }">Save</div>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Initializing
        ---------------------------------------------------------------------*/
        self.leaderboards = []
        self.selected_leaderboard_index = undefined

        self.on('mount', () => {
            $('.ui.accordion', self.root).accordion({
                selector: {
                    trigger: '.title .trigger'
                }
            })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.add = function () {
            $(self.refs.modal).modal('show')
        }

        self.edit = function (index) {
            $(self.refs.modal).modal('show')
            var leaderboard = self.leaderboards[index]
            self.refs.title.value = leaderboard.title
            self.refs.key.value = leaderboard.key

            self.selected_leaderboard_index = index
        }

        self.close_modal = function () {
            $(self.refs.modal).modal('hide')
            self.clear_form()
        }

        self.delete_leaderboard = function (index) {
            if (confirm("Are you sure you want to delete this?")) {
                self.leaderboards.splice(index, 1)
                self.update()
                self.form_updated()
            }
        }

        self.save = function () {
            var leaderboard_data = {
                title: self.refs.title.value,
                key: self.refs.key.value
            }
            if (self.selected_leaderboard_index === undefined) {
                leaderboard_data['is_active'] = true
                leaderboard_data['columns'] = [{title: "Score", is_primary: true}]
                self.leaderboards.push(leaderboard_data)
            } else {
                Object.assign(self.leaderboards[self.selected_leaderboard_index], leaderboard_data)
            }
            self.clear_form()

            // make sure to init new accordions
            $(".ui.accordion").accordion({
                selector: {
                    trigger: '.title .trigger'
                }
            })

            // then unhide modal
            self.close_modal()
        }

        self.clear_form = function () {
            self.refs.title.value = ''
            self.refs.key.value = ''

            self.selected_leaderboard_index = undefined

            self.form_updated()
            self.update()
        }

        self.form_updated = function () {
            var is_valid = true

            // Make sure we have at least 1 leaderboard
            if (self.leaderboards.length === 0) {
                is_valid = false
            } else {
                // Make sure we have 1 column
                if (self.leaderboards[0].columns.length === 0) {
                    is_valid = false
                }

                // Make sure no columns are currently being edited, have keys, etc.
                self.leaderboards.forEach(function (leaderboard) {
                    leaderboard.columns.forEach(function (column) {
                        if (column.editing) {
                            is_valid = false
                        }
                        if (column.key === '' || column.key === undefined) {
                            is_valid = false
                        }
                        if (column.computation) {
                            if (!column.computation_indexes) {
                                is_valid = false
                            } else if (column.computation_indexes.length === 0) {
                                is_valid = false
                            }
                        }

                    })
                })
            }

            CODALAB.events.trigger('competition_is_valid_update', 'leaderboards', is_valid)

            if (is_valid) {
                // Since we have valid data, let's attach our "index" to the columns
                self.leaderboards.forEach(function (leaderboard) {
                    leaderboard.columns.forEach(function (column, i) {
                        column.index = i
                    })
                })

                CODALAB.events.trigger('competition_data_update', {leaderboards: self.leaderboards})
            }
        }

        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_loaded', function(competition){
            self.leaderboards = competition.leaderboards
            self.form_updated()
        })
    </script>
    <style>
        .modal-button {
            margin-bottom: 20px !important;
        }
        .key {
            font-size: 16px;
            font-style: italic;
        }
    </style>
</competition-leaderboards-form>

<competition-leaderboard-form-table>
    <!-- The form is here for the radio button to work -->
    <form onsubmit="return false">
        <table class="ui compact celled small table table-bordered definition">
            <thead>
            <tr>
                <th class="right aligned" width="175px">

                </th>
                <th each="{ column, index in columns }" class="center aligned" width="175px">
                    <i class="left floated chevron left icon" show="{ !column.editing && index > 0 }" onclick="{ move_left.bind(this, index) }"></i>

                    <span class="column_name" show="{ !column.editing }" onclick="{ edit_column_name.bind(this, index) }">
                        <i class="counterclockwise rotated icon pencil small"></i> { column.title }
                    </span>

                    <div class="ui input" show="{ column.editing }">
                        <input id="column_input_{ index }" type="text" value="{ column.title }" onkeydown="{ edit_column_name_submit.bind(this, index) }">
                    </div>

                    <i class="right floated chevron right icon" show="{ !column.editing && index + 1 < columns.length }" onclick="{ move_right.bind(this, index) }"></i>
                </th>
                <th></th>
            </tr>
            </thead>
            <tbody>
            <tr class="ui aligned right">
                <td>Primary Column?</td>
                <td each="{ column, index in columns }" class="center aligned">
                    <input type="radio" name="primary" checked="{ index === primary_index }" onchange="{ set_primary.bind(this, index) }">
                </td>
                <td></td> <!-- Empty cell so it cuts off nicely at the end of rows -->
            </tr>

            <tr class="ui aligned right">
                <td>
                    <span>
                        Applied computation
                        <span data-tooltip="This operation is applied to every other column" data-inverted="" data-position="right center">
                            <i class="help icon circle"></i>
                        </span>
                    </span>
                </td>
                <td each="{ column, index in columns }" class="center aligned">
                    <div class="ui field">
                        <select class="ui fluid small dropdown" onchange="{ edit_column_type.bind(this, index) }">
                            <option selected="{!column.computation}">
                                ------
                            </option>
                            <option value="avg" selected="{column.computation === 'avg'}">Average</option>
                        </select>
                    </div>
                    <div class="ui field" show="{ column.computation }">
                        <label>Apply to:</label>
                        <select class="ui fluid small multiselect dropdown" multiple="" id="computation_indexes_{index}" onchange="{update_computation_indexes.bind(this, index)}">
                            <option each="{ inner_column, inner_index in columns }" if="{ index != inner_index && !inner_column.editing }" selected="{_.indexOf(column.computation_indexes, inner_index.toString()) != -1}" value="{ inner_index }"> { inner_column.title }</option>
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

            <tr class="ui aligned right">
                <td>
                    <span>
                        Column Key <span class="required">*</span>
                        <span data-tooltip="This is the key you will use to assign scoring columns, along with leaderboard key, in your scoring program" data-inverted="" data-position="right center">
                            <i class="help icon circle"></i>
                        </span>
                    </span>
                </td>
                <td each="{ c, index in columns }" class="center aligned">
                    <div class="ui fluid input">
                        <input type="text" placeholder="Key" value="{c.key}" onkeyup="{ edit_key.bind(this, index) }">
                    </div>
                </td>
                <td></td>
            </tr>

            <tr>
                <td></td>
                <td each="{ c, index in columns }" class="center aligned">
                    <button type="button" class="ui basic icon button mini red remove" onclick="{ remove_column.bind(this, index) }">
                        <i class="icon trash alternate outline"></i>Remove
                    </button>
                </td>
                <td></td>
            </tr>
            </tbody>

            <tfoot class="full-width">
            <tr>
                <th></th>
                <th colspan="{ columns.length + 1}">
                    <button type="button" class="ui small primary labeled icon button" onclick="{ add_column }">
                        <i class="add square icon"></i> Add column
                    </button>
                </th>
            </tr>
            </tfoot>
        </table>
    </form>
    <script>
        var self = this

        /*---------------------------------------------------------------------
         Initializing
        ---------------------------------------------------------------------*/
        self.columns = []

        self.one("mount", function () {
            //$(".tooltip").popup()
            $(".dropdown", self.root).dropdown()


            // *NOTE* Assigning columns this way gets it out of "opts" and makes it namespace properly!
            self.columns = self.opts.columns
            self.primary_index = self.opts.primary_index
            self.selected_leaderboard = self.opts.leaderboard_index
        })

        self.on("update", function () {
            // Force refresh of dropdown on update, otherwise they don't show new elements and
            // don't reflect new names
            let leaderboard_dropdown = $(".dropdown", self.root)
            leaderboard_dropdown.dropdown("refresh")
            setTimeout(() => {
                leaderboard_dropdown.dropdown()
            }, 5)
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.add_column = function () {
            self.columns.push({title: "Score2", key: ''})
            self.update()

            // Automatically start editing the last column we added
            self.edit_column_name(self.columns.length - 1)
        }
        self.update_computation_indexes = index => {
            self.columns[index].computation_indexes = $(`#computation_indexes_${index}`).val()
            self.parent.form_updated()
        }

        self.edit_column_name = function (index) {
            self.columns[index].editing = true
            self.update()
            $("#column_input_" + index).focus()

            // Even though we're just starting editing, we want to change validation so
            // the user knows they have to finish editing or the form will remain invalid
            self.parent.form_updated()
        }

        self.edit_column_type = function (index, event) {
            let value = event.target.value
            if (!value) {
                self.columns[index].computation_indexes = null
                self.columns[index].computation = null
            } else {
                self.columns[index].computation = value
            }

            self.parent.form_updated()
        }

        self.edit_column_name_submit = function (index, event) {
            if (event.keyCode === 13) {
                self.columns[index].title = event.target.value
                self.columns[index].editing = false
                self.parent.form_updated()
            }
        }

        self.edit_key = function (index, event) {
            self.columns[index].key = event.target.value
            self.parent.form_updated()
        }

        self.remove_column = function (index) {
            if (self.columns.length === 1) {
                toastr.error("Each leaderboard must have at least 1 column!")
                return
            }

            self.columns.splice(index, 1)
            self.update()
            self.parent.form_updated()
        }

        self.set_primary = function (index) {
            self.parent.leaderboards[self.selected_leaderboard].primary_index = index
            self.parent.form_updated()
        }

        self.edit_leaderboard_details = function () {
            CODALAB.events.trigger('leaderboard_select_index')
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
            self.parent.form_updated()
        }
    </script>

    <style>
        :scope {
            display: block;
            padding: 20px 0;
            overflow-x: auto;
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

        .column_name {
            cursor: pointer;
            position: relative;
        }

        .column_name:hover .pencil {
            opacity: 1;
        }

        .column_name .pencil {
            position: absolute;
            left: -1.3em;
            opacity: .45;
        }

        .ui.basic.red.button.remove:hover {
            color: white !important;
            background-color: #db2828 !important;
            box-shadow: 0 0 0 1px #db2828 inset!important;
        }

        /* Special class just to color the label for "Key" required asterisk! */
        .required {
            color: #DB2828;
        }
    </style>
</competition-leaderboard-form-table>