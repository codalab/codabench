<competition-tile>
    <a class="link-no-deco" href="https://google.com">
        <div class="tile-wrapper">
            <div class="ui square tiny bordered image img-wrapper">
                <img src="{logo}">
            </div>
            <div class="comp-info">
                <h4 class="heading">
                    {title}
                </h4>
                <p class="comp-description">
                    {phases.description}
                    Yo we got a description my dudes! Test this bad boi out
                </p>
                <p class="organizer">
                    <em>Organized by: <strong>A person!</strong></em>
                </p>
            </div>
            <div class="comp-stats">
                Dec 12, 2018
                <div class="ui divider"></div>
                <strong>1293</strong> Participants
            </div>
        </div>
    </a>


    <!-- <div class="ui grid">
        <div class="ui middle aligned attached message stretched row main-wrapper">
            <div class="four wide column">
                <div class="ui square bordered small image">
                    <img src="https://i.imgur.com/n2XUSxU.png">
                    <img src="{ logo }">
                </div>
            </div>
            <div class="nine wide column">
                <div class="ui row">
                    <div class="twelve wide column">
                        <h1 class="ui large header">
                            {title}
                        </h1>
                        <p class="comp-tile-paragraph">
                            A competition description
                            {description}
                        </p>
                    </div>
                    <div class="four wide right justify left align column">
                        <div align="right" class="content">
                            <i>Organized by: <b>Someone</b></i>
                        </div>
                    </div>
                </div>
                <div class="ui row">
                    <div class="sixteen wide column">
                        <div class="content">
                        </div>
                    </div>
                </div>
                <div class="ui row">
                    <div class="sixteen wide column">
                        <div class="content">
                            Tags: <b>Beginner</b>, <b>AutoML</b>
                            <br>
                            Admins: <b>tthomas63</b>
                        </div>
                    </div>
                </div>
            </div>
            <div class="three wide blue column center aligned comp-tile-full-height">
                <i>Comp deadline:</i>
                <i>August 14 2018</i>
                <div class="ui divider"></div>
                <i>Phase deadline:</i>
                <i>April 14 2018</i>
                <div class="ui divider"></div>
                <i>17 participants</i>
            </div>
        </div>
    </div>-->

    <script>

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
            background-color #f4f4f4
            transition all 75ms ease-in-out
            color #909090

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

        .organizer
            font-size 13px
            text-align left
            margin 0.35em
    </style>

    <!--<style type="text/stylus">
        :scope
            display block
            margin-bottom 35px !important

        .main-wrapper
            border-left 5px solid #c7402d
            border-top-left-radius 6px !important
            border-bottom-left-radius 6px !important

        .comp-tile-paragraph
            font-size 14px !important

        .comp-tile-full-height
            border-top-right-radius 3px

        .ui.grid > .row > .blue.column
            background-color #4a6778 !important


    </style> -->
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
