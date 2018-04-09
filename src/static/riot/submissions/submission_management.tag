<submission_management>
    <!-- HTML -->
    <h1>Submission Management</h1>
    <div class="ui divider"></div>
    <div class="ui menu">
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
    <div class="ui">
        <div class="ui left rail">
            <div class="ui sticky">
                <div class="ui vertical labeled icon buttons">
                    <button class="ui button">
                        <i class="refresh icon"></i>
                        Re-run Selected
                    </button>
                    <button class="ui button">
                        <i class="minus circle icon"></i>
                        Stop Selected
                    </button>
                    <button class="ui button">
                        <i class="trash icon"></i>
                        Delete Selected
                    </button>
                </div>
                <div class="ui compact hidden info message">
                    <i class="close icon"></i>
                    <div class="header">
                        Success!
                    </div>
                    <ul class="list">
                        <li>Deleted x files</li>
                        <li>Stopped x files</li>
                        <li>Re-running x files</li>
                    </ul>
                </div>
        </div>
    </div>
    <table class="ui compact celled table">
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

            $('.ui.button')
                .on('click', function () {
                    $('.ui.compact.info.message')
                        .closest('.message')
                        .transition('fade in')
                })

            $('.ui.compact.info.message .close')
                .on('click', function () {
                    $(this)
                        .closest('.message')
                        .transition('fade')
                })
        })
    </script>
    <!-- CSS -->
    <style type="text/stylus">
        submission_management
            width 100%

        .ui.left.rail
            width 120px
            text-align right
            padding-top 144px

        .ui.compact.info.message
            width 131px
            text-align left
    </style>
</submission_management>