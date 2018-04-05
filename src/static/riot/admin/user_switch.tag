<user_switch>

    <!------------------------------------------ HTML ------------------------------------------->
    <div id="user_switch_modal" class="ui modal">
        <i class="close icon"></i>
        <div class="header">
            Change User
        </div>
        <div class="content">
            <!--<label for="user_id" id="login_as">Login as:</label>-->
            <div class="field-container">
                <form class="ui form" method="POST" action="/su/" ref="form">
                    <input type="hidden" value="{CSRF_TOKEN}">
                    <input ref="user_id" class="ui input focus" placeholder="User ID">
                </form>
            </div>
        </div>
        <div class="actions">
            <div class="ui grey basic deny button">
                Cancel
            </div>
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
            $('.ui.modal').modal({
                detachable: false
            })
        });

        self.submit_form = function() {
            self.refs.form.submit()
        }
    </script>
    <!------------------------------------------ CSS Styling ------------------------------------>

    <style type="text/stylus">

        #user_switch_modal
            width 450px !important
            margin -225px 0 0 -225px  !important

    </style>

</user_switch>
