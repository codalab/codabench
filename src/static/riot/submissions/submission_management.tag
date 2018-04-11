<submission_management>
    <!-- HTML -->
    <h1>Submission Management</h1>
    <div class="ui divider"></div>
    <div class="stackable ui menu">
        <div class="item">
            <div class="ui icon input">
                <input type="text" placeholder="Search Users...">
                <i class="user icon"></i>
            </div>
        </div>
        <div class="ui right pushed search item">
            <div class="ui icon input">
                <input class="prompt" type="text" placeholder="Search Competitions...">
                <i class="search icon"></i>
            </div>
            <div class="results"></div>
        </div>
    </div>
    <div id="horizButtons" class="ui horizontal icon buttons">
        <button class="ui button" data-tooltip="Re-run Selected" data-position="top left">
            <i class="refresh icon"></i>
        </button>
        <button class="ui button" data-tooltip="Stop Selected">
            <i class="minus circle icon"></i>
        </button>
        <button class="ui button" data-tooltip="Delete Selected">
            <i class="trash icon"></i>
        </button>
    </div>
    <div class="ui">
        <div id="leftRail" class="ui left rail">
            <div class="ui sticky">
                <div class="ui vertical icon buttons">
                    <button class="ui right icon button" data-tooltip="Re-run Selected" data-position="top left">
                        <i class="refresh icon"></i>
                    </button>
                    <button class="ui right icon button" data-tooltip="Stop Selected" data-position="bottom left">
                        <i class="minus circle icon"></i>
                    </button>
                    <button class="ui right icon button" data-tooltip="Delete Selected" data-position="bottom left">
                        <i class="trash icon"></i>
                    </button>
                </div>
            </div>
        </div>
        <table class="ui compact celled unstackable table">
            <thead>
            <tr>
                <th>
                    <div class="ui checkbox">
                        <input type="checkbox"><label></label>
                    </div>
                </th>
                <th>File Name</th>
                <th>File Size</th>
                <th>Submitted at</th>
                <th>Processing Start</th>
                <th>Processing End</th>
                <th>Compute Worker</th>
                <th>Queue</th>
                <th>Docker Image</th>
            </tr>
            </thead>
            <tbody>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"><label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"><label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox"> <label></label>
                    </div>
                </td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            </tbody>
            <tfoot class="full-width">
            <tr>
                <th colspan="11">
                    <div class="ui right floated pagination menu">
                        <a class="icon item"><i class="left chevron icon"></i></a>
                        <a class="item">1</a>
                        <a class="item">2</a>
                        <a class="item">3</a>
                        <a class="item">4</a>
                        <a class="icon item"><i class="right chevron icon"></i></a>
                    </div>
                </th>
            </tr>
            </tfoot>
        </table>
    </div>
    <!-- Javascript -->
    <script>
        $(document).ready(function () {
            $('.ui.sticky')
                .sticky({
                    context: '.ui.compact.celled.table',
                    offset: 75
                })
        })
    </script>
    <!-- CSS -->
    <style type="text/stylus">
        submission_management
            width 100%
            overflow-y auto
            white-space wrap

        .ui.left.rail
            padding-top 144px
            width 2%

        @media all and (max-width: 1200px)
            #leftRail
                display none
            #horizButtons
                display block

        @media all and (min-width: 1200px)
            #leftRail
                display block
            #horizButtons
                display none
    </style>
</submission_management>
