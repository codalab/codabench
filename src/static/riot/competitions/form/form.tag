<competition-form>
    <div class="ui middle aligned stackable grid container">
        <div class="row centered">
            <div class="twelve wide column">
                <div class="ui top pointing secondary menu">
                    <a class="active item" data-tab="competition_details">
                        <i class="checkmark box icon green" show="{ sections.details.valid }"></i> Competition details
                    </a>
                    <a class="item" data-tab="pages">
                        <i class="checkmark box icon green" show="{ sections.pages.valid }"></i> Pages
                    </a>
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
                    <competition-leaderboards-form></competition-leaderboards-form>
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

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.competition = {}
        self.sections = {
            'details': {valid: false},
            'pages': {valid: false},
            'phases': {valid: false},
            'leaderboard': {valid: false},
            'collaborators': {valid: false}
        }

        self.one("mount", function(){
            // tabs
            $('.menu .item').tab()
        })

        self.save = function() {
            console.log("MAIN FORM SAVING")
        }

        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_data_update', function(data) {
            Object.assign(self.competition, data)
            self.update()
        })
        CODALAB.events.on('competition_is_valid_update', function(name, is_valid) {
            console.log(name + " is_valid -> " + is_valid)
            self.sections[name].valid = is_valid
            self.update()
        })
    </script>
</competition-form>