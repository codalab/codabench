<profile-detail>
    <!------------------------------------------ HTML ------------------------------------------->
    <div class="background">
        <div id="profile_wrapper" class="ui two column doubling stackable grid container">
            <div class="column">
                <div if="{!selected_user.photo}"><img id="avatar" class="ui centered small rounded image" src="/static/img/user-avatar.png"></div>
                <div if="{selected_user.photo}"><img id="avatar" class="ui centered small rounded image" src="{selected_user.photo}"></div>

<!--                &lt;!&ndash; Competition Divider &ndash;&gt;-->
<!--                <div class="ui horizontal divider">Competitions</div>-->

<!--                &lt;!&ndash; Competition Cards &ndash;&gt;-->
<!--                <div class="ui fluid card">-->
<!--                    <div class="comp_card center aligned image">-->
<!--                        <div  class="comp_header center aligned header content">-->
<!--                            <div class="comp_name">Competition Name</div>-->
<!--                            <img class="ui centered circular image"-->
<!--                                 src="http://via.placeholder.com/50x50">-->
<!--                        </div>-->
<!--                    </div>-->
<!--                    <div class="content">-->
<!--                        <div class="description">-->
<!--                            <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Adipisci asperiores atque-->
<!--                                distinct...</p>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                    <div class="right aligned extra content">-->
<!--                        <a class="status">-->
<!--                            <i class="exchange icon"></i>-->
<!--                            In Progress-->
<!--                        </a>-->
<!--                    </div>-->
<!--                </div>-->
<!--                <div class="ui fluid card">-->
<!--                    <div class="comp_card center aligned image">-->
<!--                        <div  class="comp_header center aligned header content">-->
<!--                            <div class="comp_name">Competition Name</div>-->
<!--                            <img class="ui centered circular image"-->
<!--                                 src="http://via.placeholder.com/50x50">-->
<!--                        </div>-->
<!--                    </div>-->
<!--                    <div class="content">-->
<!--                        <div class="description">-->
<!--                            <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Adipisci asperiores atque-->
<!--                                distinct...</p>-->
<!--                        </div>-->
<!--                    </div>-->
<!--                    <div class="right aligned extra content">-->
<!--                        <a class="status">-->
<!--                            <i class="exchange icon"></i>-->
<!--                            In Progress-->
<!--                        </a>-->
<!--                    </div>-->
<!--                </div>-->
<!--                <button class="ui basic fluid button">-->
<!--                    See More Competitions...-->
<!--                </button>-->
<!--            </div>-->

                <!-- Competition Divider -->
                <div class="ui horizontal divider">Organizations</div>

                <!-- Competition Cards -->
                <div each="{org in selected_user.organizations}" class="ui fluid card">
                    <div class="comp_card center aligned image">
                        <div  class="comp_header center aligned header content">
                            <div class="comp_name">{org.name}</div>
                            <img class="ui centered mini circular image"
                                 src="{org.photo}">
                        </div>
                    </div>
                    <div class="content">
                        <div class="description">
                            <p>{ org.description.length > 225 ? org.description.substring(0, 222) + "..." : org.description}</p>
                        </div>
                    </div>
                    <div class="right aligned extra content">
                        <a class="status" href="/profiles/organization/{org.id}/">
                            View Organization
                            <i class="angle right icon"></i>
                        </a>
                    </div>
                </div>
            </div>

            <!-- Second Column -->
            <div class="eight wide column">
                <!--  Name  -->
                <span class="header content">{selected_user.first_name} {selected_user.last_name}</span>
                
                <!--  About  -->
                <div id="horiz-margin" class="ui horizontal divider">About</div>
                <div class="about-block">
                    <i class="marker icon"></i>
                    <span if="{!selected_user.location}" class="text-placeholder">Location</span>
                    <span if="{selected_user.location}">{selected_user.location}</span>
                </div>
                <div  class="about-block">
                    <i class="user icon"></i>
                    <span if="{!selected_user.title}" class="text-placeholder">Job Title</span>
                    <span if="{selected_user.title}">{selected_user.title}</span>
                </div>

                <!--  Bio  -->
                <div id="horiz-margin" class="ui horizontal divider">Bio</div>
                <span if="{!selected_user.biography}" class="text-placeholder">No bio found! Update your profile to show your bio here.</span>
                <div if="{selected_user.biography}"  class="ui justified container">{selected_user.biography}</div>
                
                <!--  Links  -->
                <div id="horiz-margin" class="ui horizontal divider">Links</div>
                <div id="grid-margin" class="ui grid">
                    <div class="social-block">
                        <span class="three wide column"><i class="world icon"></i>Website:</span>
                        <a if="{selected_user.personal_url}" href="{selected_user.personal_url}" class="thirteen wide column">{selected_user.personal_url}</a>
                    </div>
                    <div class="social-block">
                        <span class="three wide column"><i class="github icon"></i>GitHub:</span>
                        <a if="{selected_user.github_url}" href="https://github.com/" class="thirteen wide column">{selected_user.github_url}</a>
                    </div>
                    <div class="social-block">
                        <span class="three wide column"><i class="linkedin icon"></i>LinkedIn:</span>
                        <a if="{selected_user.linkedin_url}" href="https://linkedin.com/" class="thirteen wide column">{selected_user.linkedin_url}</a>
                    </div>
                    <div class="social-block">
                        <span class="three wide column"><i class="twitter icon"></i>Twitter:</span>
                        <a if="{selected_user.twitter_url}" href="https://twitter.com/" class="thirteen wide column">{selected_user.twitter_url}</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        self.selected_user = selected_user
        console.log('orgs', self.selected_user.organizations)
    </script>
    <!------------------------------------------ CSS Styling ------------------------------------>
    <style type="text/stylus">
        :scope
            margin-top 20px

        #avatar
            border solid 1px black
            max-height 200px
            max-width 200px

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

        .ui.justified.container
            margin-top 30px
            font-size 12px

        .two.wide.column
            margin-bottom -5px
            font-weight bold

        .fourteen.wide.column
            margin-bottom -5px

        #horiz-margin
            margin-top 30px

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
        
        .social-block
            margin-bottom 10px
            margin-top 5px

        .about-block
            margin-top 10px

        .text-placeholder
            color #9e9e9e
    </style>
</profile-detail>
