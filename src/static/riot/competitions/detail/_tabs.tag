<comp-tabs>
    <div class="ui grid comp-tabs">
        <!-- Tab menu -->
        <div class="ui tiny fluid four secondary pointing tabular menu details-menu">
            <div class="item" data-tab="details_tab">Details</div>
            <div class="item" data-tab="phases_tab">Phases</div>
            <div class="active item" data-tab="participate_tab">Submissions</div>
            <div class="item" data-tab="results_tab">Leader Boards</div>
            <div class="item" data-tab="admin_tab" if="{competition.is_admin}">Admin</div>
        </div>
        <div class="ui tab" data-tab="details_tab">
            <div class="ui grid">
                <div class="row">
                    <div class="sixteen wide column">
                        <div class="ui side green tabular secondary menu">
                            <div each="{page, index in competition.pages}" class="item {active: index === 0}" data-tab="page_{index}">
                                {page.title}
                            </div>
                            <div class="item" data-tab="_tags_placeholder">Cool tags (placeholders)</div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="sixteen wide column">
                        <div each="{page, index in competition.pages}" class="ui tab {active: index === 0}" data-tab="page_{index}" id="page_{index}">
                        </div>
                        <div class="ui tab" data-tab="_tags_placeholder">
                            <div class="comp-data-containers">
                                <comp-run-info competition={competition}></comp-run-info>
                                <comp-stats competition={competition}></comp-stats>
                                <comp-tags competition={competition}></comp-tags>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="_tab_terms">
                            <div class="ui">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!--phases tab-->
        <div class="phases-tab ui tab" data-tab="phases_tab">
            <div class="ui relaxed grid">
                <div class="row">
                    <div class="four wide column">
                        <div class="ui side green vertical tabular menu">
                            <div each="{ phase, i in competition.phases }" class="{active: i == 0} item" data-tab="_tab_phase{phase.index}">
                                { phase.name }
                            </div>
                        </div>
                    </div>
                    <div class="twelve wide column">
                        <div each="{ phase, i in competition.phases }" class="ui {active: i == 0} tab" data-tab="_tab_phase{phase.index}">
                            <div class="ui" id="phase_{i}">

                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!--participate tab-->
        <div class="submission-tab ui active tab" data-tab="participate_tab">
            <!-- Tab Content !-->
            <select class="ui dropdown" ref="phase" onchange="{ phase_selected }">
                <option each="{ phase in competition.phases }" value="{ phase.id }">Phase: { phase.name }</option>
            </select>
            <div>
                <submission-upload phases="{ competition.phases }"></submission-upload>
            </div>
            <div>
                <submission-manager competition="{ competition }"></submission-manager>
            </div>
        </div>

        <!--results tab-->
        <div class="leaderboard-tab ui tab" data-tab="results_tab">
            <!-- Tab Content !-->
            <div>
                <leaderboards competition_pk="{ competition.id }"
                              leaderboards="{ competition.leaderboards }"></leaderboards>
            </div>
        </div>
        <div if="{competition.is_admin}" class="admin-tab ui tab" data-tab="admin_tab">
            <div class="ui side green tabular secondary menu">
                <div class="active item" data-tab="_tab_competition_management">
                    Competition Management
                </div>
                <div class="item" data-tab="_tab_submission_management">
                    Submission Management
                </div>
                <div class="item" data-tab="_tab_participant_management">
                    Participant Management
                </div>
            </div>
            <div class="ui active tab" data-tab="_tab_competition_management">
                <a href="{window.URLS.COMPETITION_EDIT(competition.id)}" class="ui blue button">Edit competition</a>
                <button class="ui button published icon { grey: !competition.published, green: competition.published }"
                        onclick="{ toggle_competition_publish }">
                    <i class="icon file"></i> {competition.published ? "Published" : "Draft"}
                </button>
            </div>
            <div class="ui tab" data-tab="_tab_submission_management">
                <div class="ui">
                    <submission-manager admin="true" competition="{ competition }"></submission-manager>
                </div>
            </div>
            <div class="ui tab" data-tab="_tab_participant_management">
                <div class="ui">
                    <h3>Stuff for managing participants</h3>
                </div>
            </div>
        </div>
    </div>
        <style type="text/stylus">
            .comp-tabs
                margin-top 1em !important

            .ui.secondary.pointing.menu .active.item
                border-color rgba(42, 68, 88, .5)
                color rgb(42, 68, 88)

            .ui.secondary.pointing.menu .active.item:hover
                border-color rgba(42, 68, 88, .5)
                color rgb(42, 68, 88)

            .details-menu
                width 100%

            .details-menu .active.item, .details-menu .item
                margin -2px auto !important

            .submission-tab
                margin 0 auto
                width 100%
                @media screen and (min-width 768px)
                    width 85%

            .leaderboard-tab
                margin 0 auto
                width 100%
                @media screen and (min-width 768px)
                    width 85%

            .phases-tab
                margin 0 auto
                width 100%
                @media screen and (min-width 768px)
                    width 85%

            .admin-tab
                margin 0 auto
                width 100%
                @media screen and (min-width 768px)
                    width 85%

        </style>
        <script>
            $('.tabular.menu .item').tab(); // Activate tabs

            var self = this

            self.competition = {}

            CODALAB.events.on('competition_loaded', function (competition) {
                self.competition = competition
                self.competition.is_admin = CODALAB.state.user.has_competition_admin_privileges(competition)
                self.update()
                $('.tabular.menu .item').tab();
                _.forEach(competition.pages, (page, index) => {
                    $(`#page_${index}`)[0].innerHTML = render_markdown(page.content)
                })
                _.forEach(competition.phases, (phase, index) => {
                    $(`#phase_${index}`)[0].innerHTML = render_markdown(phase.description)
                })
            })

            self.one("mount", function () {

            })

            self.toggle_competition_publish = function () {
                CODALAB.api.toggle_competition_publish(self.competition.id)
                    .done(function (data) {
                        var published_state = data.published ? "published" : "unpublished"
                        toastr.success(`Competition has been ${published_state} successfully`)
                        self.update()
                        CODALAB.api.get_competition(self.competition.id)
                            .done((competition) => {
                                CODALAB.events.trigger('competition_loaded', competition)
                            })
                    })
            }
            self.phase_selected = function(event, data) {
                // Really gross way of getting phase from the <select>'s <option each={ phase in phases}> jazz
                CODALAB.events.trigger('phase_selected', self.refs.phase.options[self.refs.phase.selectedIndex]._tag.phase)
            }

        </script>

</comp-tabs>