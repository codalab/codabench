<public-list>
    <h1>Public Competitions</h1>
    <div class="pagination-nav" hide="{(get_array_length(competitions.results) === competitions.count) || (get_array_length(competitions.results) < 10)}">
        <button show="{competitions.previous}" onclick="{handle_ajax_pages.bind(this, -1)}" class="float-left ui inline button active">Back</button>
        <button hide="{competitions.previous}" disabled="disabled" class="float-left ui inline button disabled">Back</button>
        { current_page } of {Math.ceil(competitions.count/20)}
        <button show="{competitions.next}" onclick="{handle_ajax_pages.bind(this, 1)}" class="float-right ui inline button active">Next</button>
        <button hide="{competitions.next}" disabled="disabled" class="float-right ui inline button disabled">Next</button>
    </div>
    <div each="{competition in competitions.results}">
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
    <div class="pagination-nav" hide="{get_array_length(competitions.results) === competitions.count}">
        <button show="{competitions.previous}" onclick="{handle_ajax_pages.bind(this, -1)}" class="float-left ui inline button active">Back</button>
        <button hide="{competitions.previous}" disabled="disabled" class="float-left ui inline button disabled">Back</button>
        { current_page } of {Math.ceil(competitions.count/20)}
        <button show="{competitions.next}" onclick="{handle_ajax_pages.bind(this, 1)}" class="float-right ui inline button active">Next</button>
        <button hide="{competitions.next}" disabled="disabled" class="float-right ui inline button disabled">Next</button>
    </div>
<script>
    var self = this
    self.competitions = {}
    self.competitions_cache = {}

    self.one("mount", function () {
        self.update_competitions_list(self.get_url_page_number_or_default())
    })

    self.handle_ajax_pages = function (num){
        self.update_competitions_list(self.get_url_page_number_or_default() + num)
    }

    self.update_competitions_list = function (num) {
        self.current_page = num
        if (self.competitions_cache[self.current_page]){
            self.competitions = self.competitions_cache[self.current_page]
            history.pushState("", document.title, "?page="+self.current_page)
            self.update()
        } else {
            return CODALAB.api.get_public_competitions({"page":self.current_page})
                .fail(function (response) {
                    toastr.error("Could not load competition list")
                })
                .done(function (response){
                    console.log(response)
                    self.competitions = response
                    self.competitions_cache[self.current_page.toString()] = response
                    history.pushState("", document.title, "?page="+self.current_page)
                    self.update()
                })
        }
    }

    self.get_array_length = function (arr) {
        if(arr === undefined){
            return 0
        }
        return arr.length
    }

    self.pretty_date = function (date_string) {
        if (!!date_string) {
            return luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL)
        } else {
            return ''
        }
    }

    self.pretty_description = function(description){
        return description.substring(0,120) + (description.length > 120 ? '...' : '') || ''
    }

    self.get_url_page_number_or_default = function (){
        let queryString = window.location.search
        let urlParams = new URLSearchParams(queryString)
        if(urlParams.has('page')){
            let pagenum = parseInt(urlParams.get('page'))
            if(pagenum < 1){
                history.pushState("test", document.title, "?page="+1)
                return 1
            } else {
                return pagenum
            }
        } else {
            history.pushState("test", document.title, "?page="+1)
            return 1
        }
    }

    $(window).on('popstate', function (event) {
        self.update_competitions_list(self.get_url_page_number_or_default())
    })


</script>

<style type="text/stylus">
    public-list
        width 100%
    :scope
        display block
        margin-bottom 5px

    .pagination-nav
        padding 10px 0
        width 100%
        text-align center
        margin-bottom 20px

    .float-left
        float left

    .float-right
        float right

    .center
        margin auto

    .link-no-deco
        text-decoration none

    .tile-wrapper
        border solid 1px gainsboro
        display inline-flex
        //grid-template-columns 0.1fr 3fr 1.3fr

        min-width 425px
        background-color #fff
        transition all 75ms ease-in-out
        color #909090
        width 100%
        margin-bottom 6px

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

    .comp-info
        width calc(100% - 140px - 80px)

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
        width 140px

    .organizer
        font-size 13px
        text-align left
        margin 0.35em
</style>

</public-list>
