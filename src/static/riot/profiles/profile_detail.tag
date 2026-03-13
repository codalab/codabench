<profile-detail>
    <!--  HTML  -->
    <div class="background">
        <div id="profile_wrapper" class="ui two column doubling stackable grid container">

            <!-- First Column -->
            <div class="column">
                <div if="{!selected_user.photo}"><img id="avatar" class="ui centered small rounded image" src="/static/img/user-avatar.png"></div>
                <div if="{selected_user.photo}"><img id="avatar" class="ui centered small rounded image" src="{selected_user.photo}"></div>

                <!-- Organizations -->
                <div if="{selected_user.organizations && selected_user.organizations.length}">
                    <div class="ui horizontal divider">Organizations</div>

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

                <!-- Competitions Organized -->
                <div if="{selected_user.competitions_organized && selected_user.competitions_organized.length}">
                    <div class="ui horizontal divider">Competitions Organized</div>

                    <div each="{competition in selected_user.competitions_organized}">
                    <!-- tile-wrapper from public-list.tag -->
                        <div class="tile-wrapper">
                            <div class="ui square tiny bordered image img-wrapper">
                                <img src="{competition.logo_icon ? competition.logo_icon : competition.logo}" loading="lazy">
                            </div>
                            <a class="link-no-deco" href="/competitions/{competition.id}">
                                <div class="comp-info">
                                <h4 class="heading">{competition.title}</h4>
                                <p class="comp-description">{ pretty_description(competition.description) }</p>
                                </div>
                            </a>
                            <div class="comp-stats">
                                {pretty_date(competition.created_when)}
                                <div if="{!competition.reward && ! competition.report}" class="ui divider"></div>
                                <div>
                                <span if="{competition.reward}"><img width="30" height="30" src="/static/img/trophy.png"></span>
                                <span if="{competition.report}"><a href="{competition.report}" target="_blank"><img width="30" height="30" src="/static/img/paper.png"></a></span>
                                </div>
                                <strong>{competition.participants_count}</strong> Participants
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Second Column -->
            <div class="eight wide column">

                <!--  Section Personal Info  -->
                <div id="horiz-margin" class="ui horizontal divider">Personal Info</div>
                
                <!-- Name -->
                <div if="{ selected_user.first_name && selected_user.last_name}" class="about-block">
                    <div class="flex-container">
                        <div class="label">Name</div>
                        <div class="value">{selected_user.first_name} {selected_user.last_name}</div>
                    </div>
                </div>

                <!--  Do not show to other users  -->
                <div if="{selected_user.id === CODALAB.state.user.id}">
                    <!-- Email -->
                    <div if="{ selected_user.email }" class="about-block">
                        <div class="flex-container">
                            <div class="label">Email</div>
                            <div class="value">{selected_user.email}</div>
                        </div>
                    </div>

                    <!-- Username -->
                    <div if="{ selected_user.username }" class="about-block">
                        <div class="flex-container">
                            <div class="label">Username</div>
                            <div class="value">{selected_user.username}</div>
                        </div>
                    </div>

                    <!-- Display Name -->
                    <div if="{ selected_user.display_name }" class="about-block">
                        <div class="flex-container">
                            <div class="label">Display Name</div>
                            <div class="value">{selected_user.display_name}</div>
                        </div>
                    </div>
                </div>
                
                <!--  Section About  -->
                <div id="horiz-margin" class="ui horizontal divider">About</div>

                <!-- Location -->
                <div if="{ selected_user.location }" class="about-block">
                    <div class="flex-container">
                        <div class="label"></i>Location</div>
                        <div class="value">{selected_user.location}</div>
                    </div>
                </div>

                <!-- Job title -->
                <div if="{ selected_user.title }" class="about-block">
                    <div class="flex-container">
                        <div class="label">Job Title</div>
                        <div class="value">{selected_user.title}</div>
                    </div>
                </div>

                <!--  Empty About Message  -->
                <span if="{!selected_user.location && !selected_user.title}" class="text-placeholder">Update your profile to show your job title and location here.</span>
                

                <!--  Section Bio  -->
                <div id="horiz-margin" class="ui horizontal divider">Bio</div>
                <!-- Bio  -->
                <div if="{selected_user.biography}"  class="ui justified container">{selected_user.biography}</div>
                
                <!--  Empty Bio Message   -->
                <span if="{!selected_user.biography}" class="text-placeholder">Update your profile to show your bio here.</span>
                
                
                <!--  Section Links  -->
                <div id="horiz-margin" class="ui horizontal divider">Links</div>

                <!--  Website   -->
                <div if="{ selected_user.personal_url }" class="about-block">
                    <div class="flex-container">
                        <div class=""><i class="world icon"></i>Website:</div>
                        <div class="value">
                            <a href="{selected_user.personal_url}" target="_blank">{selected_user.personal_url}</a>
                        </div>
                    </div>
                </div>

                <!--  GitHub   -->
                <div if="{ selected_user.github_url }" class="about-block">
                    <div class="flex-container">
                        <div class=""><i class="github icon"></i>GitHub:</div>
                        <div class="value">
                            <a href="{ selected_user.github_url }" target="_blank">{selected_user.github_url}</a>
                        </div>
                    </div>
                </div>

                <!--  LinkedIn   -->
                <div if="{ selected_user.linkedin_url }" class="about-block">
                    <div class="flex-container">
                        <div class=""><i class="linkedin icon"></i>LinkedIn:</div>
                        <div class="value">
                            <a href="{ selected_user.linkedin_url }" target="_blank">{selected_user.linkedin_url}</a>
                        </div>
                    </div>
                </div>

                <!--  Twitter   -->
                <div if="{ selected_user.twitter_url }" class="about-block">
                    <div class="flex-container">
                        <div class=""><i class="twitter icon"></i>Twitter:</div>
                        <div class="value">
                            <a href="{ selected_user.twitter_url }" target="_blank">{selected_user.twitter_url}</a>
                        </div>
                    </div>
                </div>

                <!--  Empty Links Message   -->
                <span if="{!selected_user.personal_url && !selected_user.github_url && !selected_user.linkedin_url && !selected_user.twitter_url}" class="text-placeholder">Update your profile to show your social links here.</span>
                

            </div>
        </div>
    </div>

    <!-- Script -->
    <script>
        var self = this
        self.selected_user = selected_user

        self.pretty_date = function (date_string) {
            return !!date_string ? luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL) : ''
        }

        self.pretty_description = function (description) {
            return description.substring(0, 120) + (description.length > 120 ? '...' : '') || ''
        }
    </script>
  
    <!--  CSS Styling   -->
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
            display flex
            flex-direction column

        .flex-container
            display flex
            flex-direction row

        .text-placeholder
            color #9e9e9e
        
        .label 
            width 100px
            color: #999
        .value
            font-size 15px
            margin-left 10px

        /* Competition cards (from public-list.tag) */
        .link-no-deco
            all unset
            text-decoration none
            cursor pointer
            width 100%

        .tile-wrapper
            border solid 1px gainsboro
            display inline-flex
            background-color #fff
            transition all 75ms ease-in-out
            color #909090
            width 100%
            margin-bottom 6px

        .tile-wrapper:hover
            box-shadow 0 3px 4px -1px #cac9c9ff
            transition all 75ms ease-in-out
            background-color #e6edf2
            border solid 1px #a5b7c5

        .comp-stats
            background-color #344d5e
            transition background-color 75ms ease-in-out

        .img-wrapper
            padding 5px
            align-self center

        .img-wrapper img
            max-height 60px !important
            max-width 60px !important
            margin 0 auto

        .comp-info
            flex 1
            padding 0 10px

        .comp-info .heading
            text-align left
            padding 5px
            color #1b1b1b
            margin-bottom 0

        .comp-info .comp-description
            text-align left
            font-size 13px
            line-height 1.15em
            margin 0.35em

        .organizer
            font-size 13px
            text-align left
            margin 0.35em

        .comp-stats
            background #405e73
            color #e8e8e8
            padding 10px
            text-align center
            font-size 12px
            width 140px

        .loading-indicator
            display flex
            align-items center
            padding 10px 0
            width 100%
            margin 0 auto

        .spinner
            border 4px solid rgba(0,0,0,.1)
            width 28px
            height 28px
            border-radius 50%
            border-top-color #3498db
            animation spin 1s ease-in-out infinite

        @keyframes spin
            0%
                transform rotate(0deg)
            100%
                transform rotate(360deg)
    </style>
</profile-detail>
