<public-list>
    <h1>comps</h1>
    <div each="{competition in competitions}">
        <a class="link-no-deco" href="../{competition.id}">
            <div class="tile-wrapper">
                <div class="ui square tiny bordered image img-wrapper">
                    <img src="{competition.logo}">
                </div>
                <div class="comp-info">
                    <h4 class="heading">
                        {competition.title}
                    </h4>
                    <p class="comp-description">
                        { pretty_description(competition.description)}
                    </p>
                    <p class="organizer">
                        <em>Organized by: <strong>{competition.created_by}</strong></em>
                    </p>
                </div>
                <div class="comp-stats">
                    {pretty_date(competition.created_when)}
                    <div class="ui divider"></div>
                    <strong>{competition.participant_count}</strong> Participants
                </div>
            </div>
        </a>
    </div>
<script>
    var self = this
    self.competitions = {}

    self.one("mount", function () {
        self.update_competitions_list()
        console.log("self.comps", self.competitions)
    })


    self.update_competitions_list = function () {
        return CODALAB.api.get_competitions({"published": true})
            .fail(function (response) {
                toastr.error("Could not load competition list")
            })
            .done(function (response){
                toastr.success("Competition list found")
                console.log(response)
                self.competitions = response
                self.update()
            })
    }

    self.pretty_date = function (date_string) {
        if (!!date_string) {
            return luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL)
        } else {
            return ''
        }
    }

    self.pretty_description = function(description){
        if (description) {
            description = render_markdown(description)
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

</public-list>
