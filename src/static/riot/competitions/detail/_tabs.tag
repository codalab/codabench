<comp-tabs>
    <div class="ui grid comp-tabs">
        <!-- Tab menu -->
        <div class="ui tiny fluid four secondary pointing tabular menu details-menu">
            <div class="item" data-tab="learn_the_details_tab">Details</div>
            <div class="item" data-tab="phases_tab">Phases</div>
            <div class="active item" data-tab="participate_tab">Submissions</div>
            <div class="item" data-tab="results_tab">Leader Boards</div>
            <div class="item" data-tab="admin_tab">Admin</div> <!-- TODO make this only show if user is comp creator or collaborator or super?-->
        </div>
        <div class="ui tab" data-tab="learn_the_details_tab">
            <div class="ui grid">
                <div class="row">
                    <div class="sixteen wide column">
                        <div class="ui side green tabular secondary menu">
                            <div class="active item" data-tab="_tab_overview">Overview</div>
                            <div class="item" data-tab="_tab_terms">Terms And Conditions</div>
                            <div class="item" data-tab="_tab_faq">FAQ</div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="sixteen wide column">
                        <div class="ui active tab" data-tab="_tab_overview">
                            <!-- Tab Content !-->
                            <p>
                                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse consectetur
                                elit est, quis consequat sapien elementum a. Etiam tempor, lorem cursus gravida
                                ultrices, diam nunc vulputate urna, nec euismod purus urna non mi. Nunc vehicula
                                quam vel tellus iaculis, eu fringilla eros consequat. Suspendisse malesuada lobortis
                                velit, id tincidunt est dignissim in. Morbi elementum quis ipsum vitae lacinia.
                                Sed imperdiet pellentesque rutrum. In commodo tempus mauris at accumsan.
                                Vestibulum hendrerit sodales enim eu auctor. Phasellus consectetur, mi eget blandit
                                luctus,
                                sem ligula bibendum est, id lobortis felis velit ut est. Sed quam risus,
                                suscipit quis lacus id, fermentum sagittis massa. Morbi posuere orci arcu, id varius
                                lorem hendrerit sed. In gravida elit eu justo molestie, nec pellentesque elit
                                finibus. Aliquam ante mi, pharetra vel nisi quis, sollicitudin condimentum ipsum.
                            </p>
                            <div class="comp-data-containers">
                                <comp-run-info competition={competition}></comp-run-info>
                                <comp-stats competition={competition}></comp-stats>
                                <comp-tags competition={competition}></comp-tags>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="_tab_terms">
                            <!-- Tab Content !-->
                            <div class="ui">
                                <p>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam hendrerit
                                    porttitor ligula, in aliquam ligula imperdiet nec. Suspendisse et mattis
                                    lorem. Morbi dapibus consectetur purus et faucibus. Nam sed mi ut felis
                                    malesuada convallis. Nulla facilisi. Nunc elit eros, viverra non semper
                                    a, pretium molestie ligula. Curabitur tellus libero, semper id convallis
                                    in, ultrices in augue. Donec congue euismod tellus, ac dignissim magna
                                    dignissim ut. Etiam elit sapien, interdum vestibulum posuere et,
                                    facilisis at neque. Praesent id sagittis leo, ut placerat turpis. Mauris
                                    pellentesque ac tellus id tristique. Nulla commodo urna malesuada tellus
                                    tincidunt cursus. In at nisi lectus. Nunc ornare sit amet diam at
                                    gravida.
                                </p>
                                <p>
                                    Aenean at iaculis leo, vel luctus diam. Quisque hendrerit orci sed
                                    bibendum mollis. Morbi diam leo, luctus eget suscipit ac, hendrerit sit
                                    amet ex. Duis lectus erat, ornare quis justo ut, pulvinar consectetur
                                    lacus. Duis molestie sem diam, vitae dapibus leo tristique vel.
                                    Suspendisse rhoncus iaculis lacinia. Sed quis elit mauris. Phasellus
                                    ornare posuere molestie. Aliquam vestibulum commodo enim a iaculis.
                                </p>
                                <p>
                                    Vestibulum in ultricies sapien, eu lacinia ante. Orci varius natoque
                                    penatibus et magnis dis parturient montes, nascetur ridiculus mus.
                                    Phasellus malesuada ipsum sed orci varius, et finibus felis lobortis.
                                    Aliquam commodo turpis ut augue volutpat pulvinar. Etiam vel mollis
                                    diam. Sed eu elit imperdiet, aliquam leo sit amet, pulvinar elit. Fusce
                                    vitae elementum odio. Curabitur tristique aliquam nisi, ut rhoncus ipsum
                                    consectetur in. Nunc at leo dolor.
                                </p>
                            </div>
                        </div>

                        <div class="ui tab" data-tab="_tab_faq">
                            <!-- Tab Content !-->
                            <div class="ui ">
                                <p>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam hendrerit
                                    porttitor ligula, in aliquam ligula imperdiet nec. Suspendisse et mattis
                                    lorem. Morbi dapibus consectetur purus et faucibus. Nam sed mi ut felis
                                    malesuada convallis. Nulla facilisi. Nunc elit eros, viverra non semper
                                    a, pretium molestie ligula. Curabitur tellus libero, semper id convallis
                                    in, ultrices in augue. Donec congue euismod tellus, ac dignissim magna
                                    dignissim ut. Etiam elit sapien, interdum vestibulum posuere et,
                                    facilisis at neque. Praesent id sagittis leo, ut placerat turpis. Mauris
                                    pellentesque ac tellus id tristique. Nulla commodo urna malesuada tellus
                                    tincidunt cursus. In at nisi lectus. Nunc ornare sit amet diam at
                                    gravida.
                                </p>

                                <p>
                                    Vestibulum in ultricies sapien, eu lacinia ante. Orci varius natoque
                                    penatibus et magnis dis parturient montes, nascetur ridiculus mus.
                                    Phasellus malesuada ipsum sed orci varius, et finibus felis lobortis.
                                    Aliquam commodo turpis ut augue volutpat pulvinar. Etiam vel mollis
                                    diam. Sed eu elit imperdiet, aliquam leo sit amet, pulvinar elit. Fusce
                                    vitae elementum odio. Curabitur tristique aliquam nisi, ut rhoncus ipsum
                                    consectetur in. Nunc at leo dolor.
                                </p>
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
                            <div class="ui">
                                <p>
                                    { phase.description }
                                </p>
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
                <submission-manager></submission-manager>
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
        <div class="admin-tab ui tab" data-tab="admin_tab">
            <div class="ui side green tabular secondary menu">
                <div class="active item" data-tab="_tab_submission_management">
                    Submission Management
                </div>
                <div class="item" data-tab="_tab_participant_management">
                    Participant Management
                </div>
            </div>
            <div class="ui active tab" data-tab="_tab_submission_management">
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
                self.update()
                $('.tabular.menu .item').tab();
            })
            //self.competition = opts.competition

            // Handling tabs
            self.tabs = ["learn_details", "phases", "participate", "results"]
            self.active_tab = self.tabs[0]

            // Dynamic based on which `tab` object is active
            self.active_tab_active_subtab = {}
            self.active_tab_subtabs = {}

            // handling pages if we're on learn the details
            if (self.competition.pages) {
                self.active_page = self.competition.pages[0]
            }

            self.one("mount", function () {
                // tabs
                $('.tabular.menu .item').tab(); // Activate tabs
                // $('.menu .item').tab()
            })

            self.set_active_tab = function (index) {
                // On set active, we need to remove the current active_tab's `active` class, and add it to the new tab
                self.active_tab = self.tabs[index]
            }

            self.tab_string_to_index = function (string_tab_id) {
                for (i = 0; i < self.tabs.length; i++) {
                    if (self.tabs[i] === string_tab_id) {
                        return i
                    }
                }
            }
            self.phase_selected = function(event, data) {
                // Really gross way of getting phase from the <select>'s <option each={ phase in phases}> jazz
                CODALAB.events.trigger('phase_selected', self.refs.phase.options[self.refs.phase.selectedIndex]._tag.phase)
            }

        </script>

</comp-tabs>