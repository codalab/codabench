<user-profile>
    <!------------------------------------------ HTML ------------------------------------------->
    <div class="background">
        <div id="profile_wrapper" class="ui two column doubling stackable grid container">
            <div class="column">
                <div><img id="avatar" class="ui centered rounded image" src="http://via.placeholder.com/150x150"></div>

                <!-- Competition Divider -->
                <div class="ui horizontal divider">Competitions</div>

                <!-- Competition Cards -->
                <div class="ui fluid card">
                    <div class="comp_card center aligned image">
                        <div  class="comp_header center aligned header content">
                            <div class="comp_name">Competition Name</div>
                            <img class="ui centered circular image"
                                 src="http://via.placeholder.com/50x50">
                        </div>
                    </div>
                    <div class="content">
                        <div class="description">
                            <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Adipisci asperiores atque
                                distinct...</p>
                        </div>
                    </div>
                    <div class="right aligned extra content">
                        <a class="status">
                            <i class="exchange icon"></i>
                            In Progress
                        </a>
                    </div>
                </div>
                <div class="ui fluid card">
                    <div class="comp_card center aligned image">
                        <div  class="comp_header center aligned header content">
                            <div class="comp_name">Competition Name</div>
                            <img class="ui centered circular image"
                                 src="http://via.placeholder.com/50x50">
                        </div>
                    </div>
                    <div class="content">
                        <div class="description">
                            <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Adipisci asperiores atque
                                distinct...</p>
                        </div>
                    </div>
                    <div class="right aligned extra content">
                        <a class="status">
                            <i class="exchange icon"></i>
                            In Progress
                        </a>
                    </div>
                </div>
                <button class="ui basic fluid button">
                    See More Competitions...
                </button>
            </div>
            <!-- Second Column -->
            <div class="eight wide column">
                <span class="header content">John Doe</span>
                <i class="marker alternate icon"></i>
                <span id="location">Spokane, WA</span>
                <div id="job_title">Backend Engineer</div>
                <div class="ui justified container">
                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque sit amet sapien eleifend,
                        aliquam mauris quis, aliquam turpis. Donec eget risus vitae neque faucibus pulvinar. Curabitur
                        mollis enim vel lacus venenatis aliquet. Donec porta, turpis ut dapibus ultricies, libero sapien
                        egestas nisi, id tristique nisl nunc ut nisi. Ut molestie commodo dolor, non ultrices eros. Vivamus
                        sollicitudin metus ligula, ac pharetra urna faucibus eu. Maecenas varius sem nec tellus semper, in
                        porttitor libero iaculis. Proin nibh elit, ultrices at nisi vitae, mattis laoreet risus. Fusce et
                        commodo nisi. </p>
                    <p>Praesent ut leo venenatis magna iaculis laoreet quis in diam. Curabitur tristique nisi volutpat risus
                        venenatis, non semper magna convallis. Nulla ac pharetra nulla, in ultrices massa. Donec non consectetur
                        odio. Praesent vel nisl vitae libero vulputate pulvinar. Donec sagittis, risus ac consectetur mollis,
                        eros nunc rutrum purus, vitae viverra...</p>
                </div>
                <div id="horiz-margin" class="ui horizontal divider"><i class="user icon"></i>About Me</div>
                <div id="grid-margin" class="ui grid">
                    <span class="three wide column"><i class="world icon"></i>Website:</span>
                    <a href="https://google.com/" class="thirteen wide column">https://myweb.site/</a>
                    <span class="three wide column"><i class="github icon"></i>GitHub:</span>
                    <a href="https://github.com/" class="thirteen wide column">https://github.com/my/</a>
                    <span class="three wide column"><i class="linkedin icon"></i>LinkedIn:</span>
                    <a href="https://linkedin.com/" class="thirteen wide column">https://linkedin.com/my/</a>
                    <span class="three wide column"><i class="twitter icon"></i>Twitter:</span>
                    <a href="https://twitter.com/" class="thirteen wide column">https://twitter.com/my/</a>
                </div>
            </div>
        </div>
    </div>
    <!------------------------------------------ CSS Styling ------------------------------------>
    <style type="text/stylus">
        :scope
            margin-top 20px

        #avatar
            border solid 1px black

        .ui.horizontal.divider
            color #9e9e9e !important

        .terminal
            color #9e9e9e

        .comp_header
            margin 5px

        .comp_card
            background green

        .comp_name
            font-weight bold
            font-size 24px
            vertical-align -15px
            text-align center
            margin 10px 0

        .exchange
            color green

        .status
            color green !important

        .ui.basic.fluid.button
            margin-bottom 10px

        .header.content
            font-size 30px
            font-weight bolder

        .marker.alternate.icon
            margin-left 5px
            font-size 14px
            margin-right -5px
            color #9e9e9e

        #location
            color #9e9e9e

        #job_title
            color darkblue
            font-size 14px
            font-weight bold
            margin-top 5px

        .ui.justified.container
            margin-top 30px
            font-size 12px

        .two.wide.column
            margin-bottom -5px
            font-weight bold

        .fourteen.wide.column
            margin-bottom -5px

        #horiz-margin
            margin-top 20px

        #grid-margin
            margin-top 20px

        .world.icon
            color grey

        .twitter.icon
            color #1DA1F2

        .github.icon
            color #6e5494

        .linkedin.icon
            color #0077B5
    </style>
</user-profile>
