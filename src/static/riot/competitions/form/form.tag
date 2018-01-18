<competition-form>
    <div class="ui middle aligned stackable grid container">
        <div class="row centered">
            <div class="twelve wide column">
                <div class="ui top pointing secondary menu">
                    <a class="active item" data-tab="competition_details">Competition details</a>
                    <a class="item" data-tab="pages">Pages</a>
                    <a class="item" data-tab="phases">Phases</a>
                    <a class="item" data-tab="leaderboard">Leaderboard</a>
                    <a class="item" data-tab="collaborators">Collaborators</a>
                </div>
                <div class="ui bottom active tab" data-tab="competition_details">
                    <competition-details></competition-details>
                </div>

                <div class="ui bottom tab" data-tab="pages">
                    <competition-pages></competition-pages>
                </div>

                <div class="ui bottom tab" data-tab="phases">
                    <competition-phases></competition-phases>
                </div>

                <div class="ui bottom tab" data-tab="leaderboard">
<!--                    <button class="ui primary button modal-button" data-modal-id="page-modal"> -->
<!--                        <i class="add circle icon"></i> Create new leaderboard -->
<!--                    </button> -->

<!--                    {% include "leaderboards/widget.html" %} -->


                    <competition-leaderboards></competition-leaderboards>






                    <!--<leaderboard-widget></leaderboard-widget>-->











                </div>

                <div class="ui bottom tab" data-tab="collaborators">
                    <competition-collaborators></competition-collaborators>
                </div>
            </div>
        </div>

        <div class="row centered">
            <button class="ui primary button disabled">
                Save
            </button>
            <button class="ui button">
                Discard
            </button>
        </div>
    </div>






    <script>
        var self = this

        self.one("mount", function(){
            // tabs
            $('.menu .item').tab()

            /*
            // datetime pickers
            $('.calendar.field').calendar({
                type: 'date',
                popupOptions: {
                    position: 'bottom left',
                    lastResort: 'bottom left',
                    hideOnScroll: false
                }
            })

            // Make dropdowns work
            $('select.dropdown').dropdown()

            // Make modals work
            $('.ui.modal').modal()

            // awesome markdown editor
            $('.markdown-editor').each(function (i, ele) {
                new SimpleMDE({element: ele})
            })

            // modals
            $('.modal-button').click(function () {
                $('#' + $(this).attr('data-modal-id')).modal('show')
            })
            */
        })
    </script>
</competition-form>