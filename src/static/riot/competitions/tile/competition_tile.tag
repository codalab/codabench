<competition-tile>
    
        <div class="tile-wrapper {is_featured ? 'featured' : ''}">
            <div class="ui square tiny bordered image img-wrapper">
                <img src="{logo_icon ? logo_icon : logo}">
            </div>
            <a class="link-no-deco" href="./competitions/{id}">
            <div class="comp-info">
                <h4 class="heading">
                    {title}
                    <span if="{is_featured}" class="featured-badge">Featured</span>
                </h4>
                <p class="comp-description">
                    {pretty_description(description)}
                </p>
                <p class="organizer">
                    <em>Organized by: <strong>{created_by}</strong></em>
                </p>
            </div>
            </a>
            <div class="comp-stats" id="compStats">
                {pretty_date(created_when)}
                <div if="{!reward && !report}" class="ui divider"></div>
                <div>
                    <span if="{reward}"><img width="30" height="30" src="/static/img/trophy.png"></span>
                    <span if="{report}"><a href="{report}" target="_blank"><img width="30" height="30" src="/static/img/paper.png"></a></span>
                </div>
                <strong>{participants_count}</strong> Participants
            </div>
        </div>

    <script>
        var self = this

        self.pretty_date = function (date_string) {
            if (!!date_string) {
                return luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL)
            } else {
                return ''
            }
        }

        self.pretty_description = function(description){
            return description.substring(0,90) + (description.length > 90 ? '...' : '') || ''
        }

    </script>

    <style type="text/stylus">
        :scope
            display block
            margin-bottom 5px

        .link-no-deco
            all unset
            text-decoration none
            cursor pointer

        .tile-wrapper
            border solid 1px gainsboro
            display inline-grid
            grid-template-columns 0.1fr 3fr 1.3fr
            min-width 425px
            background-color #fff
            transition all 75ms ease-in-out
            color #909090
            width 100%

        .tile-wrapper:hover
            box-shadow 0 3px 4px -1px #9c9c9c
            transition all 75ms ease-in-out
            background-color #e8e8e8
            border solid 1px #b9b9b9

            .comp-stats
                background-color #344d5e
                transition background-color 75ms ease-in-out
       
        .tile-wrapper.featured
            border solid 2px gold
            background-color #fffbea  /* Light yellow */
            box-shadow 0 0 10px rgba(255, 215, 0, 0.6)

        .img-wrapper
            padding 5px
            align-self center

            img
                max-height 60px !important
                max-width 60px !important
                margin 0 auto

        .comp-info .heading
            text-align left
            padding 5px
            color #1b1b1b
            margin-bottom 0

        .featured-badge
            background-color gold
            color #222
            font-size 12px
            font-weight 600
            padding 2px 7px
            border-radius 5px
            margin-left 8px
            display inline-block

        .comp-info .comp-description
            text-align: left;
            font-size 13px
            line-height 1.15em
            margin 0.35em

        .comp-stats
            background #405e73
            color #e8e8e8
            padding 10px
            text-align center
            font-size 12px

        .organizer
            font-size 13px
            text-align left
            margin 0.35em
    </style>

</competition-tile>

<competition-card>
    <div class="image">
        <img src="https://i.imgur.com/n2XUSxU.png">
    </div>
    <div class="content">
        <a class="header">{ title }</a>
        <div class="meta">
            <span class="date">Joined in 2013</span>
        </div>
        <div class="description">
            Kristy is an art director living in New York.
        </div>
    </div>
    <div class="extra content">
        <a>
            <i class="user icon"></i>
            22 Friends
        </a>
    </div>

    <script>
    </script>

    <style type="text/stylus">
        :self
            display block
    </style>
</competition-card>
