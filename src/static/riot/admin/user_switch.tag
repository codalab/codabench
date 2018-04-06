<user_switch>
    <!------------------------------------------ HTML ------------------------------------------->
    <div id="user_switch_modal" class="ui mini modal">
        <i class="close icon"></i>
        <div class="header">Change User</div>
        <div class="content">
            <div class="field-container">
                <form class="ui form" method="POST" action="/su/" ref="form">
                    <input type="hidden" value="{CSRF_TOKEN}">
                    <input ref="user_id" class="ui input focus" placeholder="User ID">
                </form>
            </div>
        </div>
        <div class="actions">
            <div class="ui grey basic deny button">Cancel</div>
            <div class="ui positive right labeled icon button" onclick="{ submit_form }">
                Switch User
                <i class="checkmark icon"></i>
            </div>
        </div>
    </div>
    <!------------------------------------------ JavaScript ------------------------------------->
    <script>
        var self = this
        self.on('mount', function(){
            $('#user_switch_modal').modal()
        })
        self.submit_form = function() {
            self.refs.form.submit()
        }
    </script>
    <!------------------------------------------ CSS Styling ------------------------------------>
    <style type="text/stylus">
    </style>
</user_switch>
