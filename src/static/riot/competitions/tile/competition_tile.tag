<competition-tile>
    <a class="link-no-deco" href="./competitions/{id}">
        <div class="tile-wrapper">
            <div class="ui square tiny bordered image img-wrapper">
                <img src="{logo}">
            </div>
            <div class="comp-info">
                <h4 class="heading">
                    {title}
                </h4>
                <p class="comp-description">
                    {pretty_description(description)}
                </p>
                <p class="organizer">
                    <em>Organized by: <strong>{created_by}</strong></em>
                </p>
            </div>
            <div class="comp-stats">
                {pretty_date(created_when)}
                <div class="ui divider"></div>
                <strong>{participant_count}</strong> Participants
            </div>
        </div>
    </a>

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
            if (description) {
                return description.substring(0,90) + (description.length > 90 ? '...' : '')
            } else {
                return ''
            }
        }
    </script>

    <style type="text/stylus">
        :scope
            display block
            margin-bottom 5px
            cursor pointer

        .link-no-deco
            text-decoration none

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
