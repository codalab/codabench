<user_management>
    <!------------------------------------------ HTML ------------------------------------------->
    <div class="row">
        <h1 class="ui center aligned header">
            User Management Portal
        </h1>
        <div id="search_bar" class="column">
                <span class="ui search">
                <span class="ui icon input">
                    <input class="prompt" type="text" placeholder="Search Users...">
                    <i class="search icon"></i>
                </span>
                <span class="results"></span>
            </span>
        </div>
        <table class="ui striped table">
            <thead>
            <tr>
                <th class=""></th>
                <th>Name</th>
                <th>Username</th>
                <th>Email</th>
                <th>User Type</th>
            </tr>
            </thead>
            <tr>
                <td class="first_row">
                    <a data-tooltip="Delete User" data-inverted="" href="#"
                       onclick="$('#delete_user_modal').modal('show')">
                        <i class="trash icon"></i>
                    </a>
                </td>
                <td>John Doe</td>
                <td>JDoe40</td>
                <td>john@jdoe.com</td>
                <td>Benchmark Admin</td>
            </tr>
        </table>
        <!-- DELETE USER MODAL -->
        <div id="delete_user_modal" class="ui mini modal">
            <div class="header">Delete User JDoe40?</div>
            <div class="actions">
                <div class="basic grey ui cancel button">Cancel</div>
                <div class="ui red approve button">Delete User</div>
            </div>
        </div>
    </div>
    <!------------------------------------------ JavaScript ------------------------------------->
    <script>
        $(document).ready(function () {
            $('.edit').hover(function () {
                $(this).css('color', 'steelblue')
            }, function () {
                $(this).css('color', 'grey')
            });
            $('.trash').hover(function () {
                $(this).css('color', '#B01C2E')
            }, function () {
                $(this).css('color', 'grey')
            });
            $('#delete_user_modal').modal({
                onApprove: function () {
                    window.alert('User Deleted!')
                }
            })
        })
    </script>
    <!------------------------------------------ CSS Styling ------------------------------------>
    <style type="text/stylus">
        user_management
            width 100%

        h1.ui.center.aligned.header
            margin-top 0.5em

        .ui.search
            align-content right !important

        .first_row
            width 35px

        .edit.icon
            color grey
            padding-top 2px

        .trash.icon
            color grey

        #search_bar
            text-align right

        table.ui.striped.table
            margin-bottom 1em

        .ui.right.aligned.container
            margin-top 1em
    </style>
</user_management>
