<comp-tabs>
    <div class="ui container relaxed center aligned grid comp-tabs">
        <div class="row">
            <div class="ui fourteen wide column">
                <div class="container">
                    <!-- Tab menu -->
                    <div class="ui blue secondary pointing inverted tabular menu">
                        <div class="item header">
                            Competition Navigation:
                        </div>
                        <div class="active item" data-tab="learn_the_details_tab">Learn The Details</div>
                        <div class="item" data-tab="phases_tab">Phases</div>
                        <div class="item" data-tab="participate_tab">Participate</div>
                        <div class="item" data-tab="results_tab">Results</div>
                        <div class="right menu">
                            <div class="item header">
                                Admin features:
                            </div>
                            <div class="item">Admin</div>
                        </div>
                    </div>
                    <div class="ui active tab" data-tab="learn_the_details_tab">
                        <div class="ui relaxed grid">
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
                                            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
                                            consectetur
                                            elit est, quis consequat sapien elementum a. Etiam tempor, lorem cursus
                                            gravida
                                            ultrices, diam nunc vulputate urna, nec euismod purus urna non mi. Nunc
                                            vehicula
                                            quam vel tellus iaculis, eu fringilla eros consequat. Suspendisse
                                            malesuada
                                            lobortis
                                            velit, id tincidunt est dignissim in. Morbi elementum quis ipsum vitae
                                            lacinia.
                                            Sed
                                            imperdiet pellentesque rutrum. In commodo tempus mauris at accumsan.
                                            Vestibulum
                                            hendrerit sodales enim eu auctor. Phasellus consectetur, mi eget blandit
                                            luctus,
                                            sem
                                            ligula bibendum est, id lobortis felis velit ut est. Sed quam risus,
                                            suscipit
                                            quis
                                            lacus id, fermentum sagittis massa. Morbi posuere orci arcu, id varius
                                            lorem
                                            hendrerit sed. In gravida elit eu justo molestie, nec pellentesque elit
                                            finibus.
                                            Aliquam ante mi, pharetra vel nisi quis, sollicitudin condimentum ipsum.
                                        </p>
                                        <comp-run-info competition={competition}></comp-run-info>
                                        <comp-stats competition={competition}></comp-stats>
                                        <comp-tags competition={competition}></comp-tags>
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
                    <div class="ui tab" data-tab="phases_tab">
                        <div class="ui relaxed grid">
                            <div class="row">
                                <div class="four wide column">

                                    <!--<div class="ui message">-->
                                    <!--<p>Show pages here</p>-->
                                    <div class="ui side green vertical tabular menu">
                                        <div class="active item" data-tab="_tab_phase2">Phase 1</div>
                                        <div class="item" data-tab="_tab_phase1">Phase 2</div>
                                    </div>
                                </div>
                                <!--</div>-->
                                <div class="twelve wide column">
                                    <div class="ui active tab" data-tab="_tab_phase1">
                                        <!-- Tab Content !-->
                                        <div class="ui ">
                                            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
                                            consectetur
                                            elit est, quis consequat sapien elementum a. Etiam tempor, lorem cursus
                                            gravida
                                            ultrices, diam nunc vulputate urna, nec euismod purus urna non mi. Nunc
                                            vehicula
                                            quam vel tellus iaculis, eu fringilla eros consequat. Suspendisse
                                            malesuada
                                            lobortis
                                            velit, id tincidunt est dignissim in. Morbi elementum quis ipsum vitae
                                            lacinia.
                                            Sed
                                            imperdiet pellentesque rutrum. In commodo tempus mauris at accumsan.
                                            Vestibulum
                                            hendrerit sodales enim eu auctor. Phasellus consectetur, mi eget blandit
                                            luctus,
                                            sem
                                            ligula bibendum est, id lobortis felis velit ut est. Sed quam risus,
                                            suscipit
                                            quis
                                            lacus id, fermentum sagittis massa. Morbi posuere orci arcu, id varius
                                            lorem
                                            hendrerit sed. In gravida elit eu justo molestie, nec pellentesque elit
                                            finibus.
                                            Aliquam ante mi, pharetra vel nisi quis, sollicitudin condimentum ipsum.
                                        </div>
                                    </div>

                                    <div class="ui tab" data-tab="_tab_phase2">
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

                                </div>
                            </div>
                        </div>
                    </div>

                    <!--participate tab-->
                    <div class="ui tab" data-tab="participate_tab">
                        <!-- Tab Content !-->
                        <div class="ui ">
                            <p>Ask to participate? Make submissions etc</p>
                            <submission-management></submission-management>
                        </div>
                    </div>

                    <!--results tab-->
                    <div class="ui tab" data-tab="results_tab">
                        <!-- Tab Content !-->
                        <div class="ui ">
                            <p>View results</p>
                        </div>
                    </div>
                </div>
            </div>
            <style type="text/stylus">
                .comp-tabs
                    margin 3vh !important
            </style>
            <script>
                $('.tabular.menu .item').tab(); // Activate tabs

                var self = this
                self.competition = opts.competition

                // Handling tabs
                self.tabs = ["learn_details", "phases", "participate", "results"]
                self.active_tab = self.tabs[0]

                // Dynamic based on which `tab` object is active
                self.active_tab_active_subtab = {}
                self.active_tab_subtabs = {}

                // handling pages if we're on learn the details
                self.active_page = self.competition.pages[0]

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

            </script>
</comp-tabs>