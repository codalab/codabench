<competition-tile>

    <div class="ui grid">
        <div class="ui middle aligned attached message stretched row main-wrapper">
            <div class="four wide column">
                <div class="ui square bordered small image">
                    <img src="https://i.imgur.com/n2XUSxU.png">
                    <!--<img src="{ logo }">-->
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
                            <!--Tags?-->
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
    </div>

    <script>
    </script>

    <style type="text/stylus">
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

        .ui.grid>.row>.blue.column
            background-color #4a6778!important


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
