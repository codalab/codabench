<profile-detail>
    <!-- One big card: it shows the details, and Edit switches all of it to the form -->
    <div class="profile-card">
        <!-- View mode -->
        <div if="{!editing}">
            <div class="profile-header">
                <!-- First letter of the name when there is no photo -->
                <div class="bc-logo profile-photo">
                    <img if="{selected_user.photo}" src="{selected_user.photo}" alt="">
                    <span if="{!selected_user.photo}">{photo_letter}</span>
                </div>

                <div class="profile-identity">
                    <h1 if="{profile_name}" class="profile-name">{profile_name} <span if="{bracket_name}" class="profile-display-name">({bracket_name})</span></h1>
                    <p if="{selected_user.email}" class="profile-email"><i class="bi bi-envelope"></i>{selected_user.email}</p>
                    <p class="profile-username"><i class="bi bi-person"></i>{selected_user.username}</p>

                    <div if="{has_links}" class="profile-links">
                        <a if="{selected_user.personal_url}" href="{selected_user.personal_url}" target="_blank" title="Website" aria-label="Website"><i class="bi bi-globe"></i></a>
                        <a if="{selected_user.github_url}" href="{selected_user.github_url}" target="_blank" title="GitHub" aria-label="GitHub"><i class="bi bi-github"></i></a>
                        <a if="{selected_user.linkedin_url}" href="{selected_user.linkedin_url}" target="_blank" title="LinkedIn" aria-label="LinkedIn"><i class="bi bi-linkedin"></i></a>
                        <a if="{selected_user.twitter_url}" href="{selected_user.twitter_url}" target="_blank" title="X" aria-label="X"><i class="bi bi-twitter-x"></i></a>
                    </div>
                </div>

                <div class="profile-actions">
                    <!-- Why the slug: the public page finds users by slug, which can differ from the username -->
                    <a class="settings-button settings-button-secondary" href="/user/{selected_user.slug}/" target="_blank" rel="noopener">View public profile</a>
                    <button type="button" class="settings-button" onclick="{start_editing}">Edit Profile</button>
                </div>
            </div>

            <div if="{has_details}" class="profile-details">
                <div if="{selected_user.title}" class="profile-row">
                    <span class="profile-row-label">Job title</span>
                    <span>{selected_user.title}</span>
                </div>
                <div if="{selected_user.location}" class="profile-row">
                    <span class="profile-row-label">Location</span>
                    <span>{selected_user.location}</span>
                </div>
                <div if="{selected_user.biography}" class="profile-row">
                    <span class="profile-row-label">Bio</span>
                    <span class="profile-bio">{selected_user.biography}</span>
                </div>
            </div>

            <!-- Shown when nothing is filled in -->
            <div if="{is_empty}" class="profile-details">
                <button type="button" class="profile-add-button" onclick="{start_editing}">Complete your profile</button>
            </div>
        </div>

        <!-- Edit mode -->
        <div if="{editing}">
            <profile-edit></profile-edit>
        </div>
    </div>

    <!-- Script -->
    <script>
        var self = this
        self.selected_user = selected_user

        // Full name if set, otherwise the display name. Empty when the user has neither.
        const full_name = [selected_user.first_name, selected_user.last_name].filter(Boolean).join(' ')
        self.profile_name = full_name || selected_user.display_name || ''

        // Shown when there is no photo. Why the username: a user may have no name
        self.photo_letter = (self.profile_name || selected_user.username).charAt(0).toUpperCase()

        // The display name goes in brackets after the full name, for example: Jane Doe (jdoe)
        // Why the check: without a full name the heading is already the display name.
        const display_name = selected_user.display_name
        self.bracket_name = display_name && display_name !== self.profile_name ? display_name : ''

        self.has_details = !!(selected_user.title || selected_user.location || selected_user.biography)
        self.has_links = !!(selected_user.personal_url || selected_user.github_url || selected_user.linkedin_url || selected_user.twitter_url)
        self.is_empty = !self.has_details && !self.has_links

        self.editing = false

        self.start_editing = function () {
            self.editing = true
            self.update()
        }

        // Called by the Cancel button in profile-edit
        self.stop_editing = function () {
            self.editing = false
            self.update()
        }
    </script>

    <!-- Why these rules stay: Riot styles apply to every page, and other pages use these class names.
         The new styles of this page are in stylus/components/my_profile.styl -->
    <style type="text/stylus">
        .ui.horizontal.divider
            color #9e9e9e !important

        .terminal
            color #9e9e9e

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

        .label
            width 100px
            color: #999

        .value
            font-size 15px
            margin-left 10px

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
