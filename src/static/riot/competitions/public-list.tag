<public-list>
  <!-- Title -->
  <div class="page-header">
    <h1 class="page-title">Public Benchmarks and Competitions</h1>
    <div class="action-buttons">
      <a class="create-btn" href="{ URLS.COMPETITION_ADD }">
        <i class="bi bi-plus-square-fill me-1"></i> Create
      </a>
      <a class="create-btn" href="{ URLS.COMPETITION_UPLOAD }">
        <i class="bi bi-cloud-arrow-up-fill me-1"></i> Upload
      </a>
    </div>
  </div>

  <!-- External Competitions banner - hidden when the feature is disabled (URLS.EXTERNAL_COMPETITIONS_PUBLIC is empty) -->
  <div class="external-competitions-banner" show="{ URLS.EXTERNAL_COMPETITIONS_PUBLIC }">
    <span>Browse external competitions from other platforms like CodaLab and other Codabench instances</span>
    <a class="external-btn" href="{ URLS.EXTERNAL_COMPETITIONS_PUBLIC }">External Competitions</a>
  </div>

  <!-- Two-column layout -->
  <div class="content-container">

    <!-- Filters -->
    <competition-filter-panel show_ordering="{ true }" initial_filters="{ filter_state }" onfilterchange="{ handle_filter_change }"></competition-filter-panel>

    <!-- Competitions -->
    <div class="list-panel">

      <div id="loading" class="loading-indicator" show="{!competitions}">
        <div class="spinner"></div>
      </div>

      <div each="{competition in competitions.results}">
        <div class="tile-wrapper">
          <div class="ui square tiny bordered image img-wrapper">
            <img src="{competition.logo_icon ? competition.logo_icon : competition.logo}" loading="lazy">
          </div>
          <a class="link-no-deco" href="../{competition.id}">
            <div class="comp-info">
              <h4 class="heading">{competition.title}</h4>
              <p class="comp-description">{ pretty_description(competition.description) }</p>
              <p class="organizer"><em>Organized by: <strong>{competition.created_by}</strong></em></p>
            </div>
          </a>
          <div class="comp-stats">
            {pretty_date(competition.first_phase_start)}
            <div if="{!competition.reward && ! competition.report}" class="ui divider"></div>
            <div>
              <span if="{competition.reward}"><img width="30" height="30" src="/static/img/trophy.png"></span>
              <span if="{competition.report}"><a href="{competition.report}" target="_blank"><img width="30" height="30" src="/static/img/paper.png"></a></span>
            </div>
            <strong>{competition.participants_count}</strong> Participants
          </div>
        </div>
      </div>

      <!-- Show when there are no competitions in the list -->
      <div class="no-results-message" if="{competitions.results && competitions.results.length === 0}">
        <div class="ui warning message">
          <div class="header">No competitions found</div>
          Try changing your filters or search term.
        </div>
      </div>

      <!--  Pagination  -->
      <div class="pagination-nav" if="{competitions.next || competitions.previous}">
        <button show="{competitions.previous}" onclick="{handle_ajax_pages.bind(this, -1)}" class="float-left ui inline button active">Back</button>
        <button hide="{competitions.previous}" disabled="disabled" class="float-left ui inline button disabled">Back</button>
        { current_page } of {Math.ceil(competitions.count/competitions.page_size)}
        <button show="{competitions.next}" onclick="{handle_ajax_pages.bind(this, 1)}" class="float-right ui inline button active">Next</button>
        <button hide="{competitions.next}" disabled="disabled" class="float-right ui inline button disabled">Next</button>
      </div>

    </div>
  </div>

  <script>
    var self = this
    self.isLoggedIn = typeof CODALAB !== "undefined" && CODALAB.state && CODALAB.state.user && CODALAB.state.user.logged_in
    self.competitions = {}

    self.get_initial_filter_state = function () {
        return {
            search: '',
            filter_mode: 'or',
            tags: '',
            no_tags_by_category: {},
            selected_tags: {},
            start_date: '',
            end_date: '',
            ordering: '',
            participating_in: false,
            organizing: false,
            has_reward: false
        }
    }

    self.filter_state = self.get_initial_filter_state()

    self.handle_filter_change = function (filters) {
        self.filter_state = filters
        self.update_competitions_list(1)
    }

    self.one("mount", function () {
        const urlParams = new URLSearchParams(window.location.search)

        if (urlParams.has("ordering")) {
            const ordering = urlParams.get("ordering")
            if (["popular", "recent", "with_most_submissions"].includes(ordering)) {
                self.filter_state.ordering = ordering
            }
        }

        self.update_competitions_list(self.get_url_page_number_or_default())
    })

    self.handle_ajax_pages = function (num) {
        $('.pagination-nav > button').prop('disabled', true)
        self.update_competitions_list(self.get_url_page_number_or_default() + num)
    }

    self.update_competitions_list = function (num) {
        self.current_page = num
        $('#loading').show()
        $('.pagination-nav').hide()

        function handleSuccess(response) {
            self.competitions = response
            $('#loading').hide()
            $('.pagination-nav').show()
            history.pushState("", document.title, "?page=" + self.current_page)
            $('.pagination-nav > button').prop('disabled', false)
            self.update()
        }

        var tag_ids = Object.keys(self.filter_state.selected_tags)
            .filter(function (id) { return self.filter_state.selected_tags[id] && id !== '_no_tags_' })
            .join(',')

        var params = {
            "page": self.current_page
        }

        if (self.filter_state.search) {
            params.search = self.filter_state.search
        }
        if (tag_ids) {
            params.tags = tag_ids
        }
        if (self.filter_state.filter_mode) {
            params.filter_mode = self.filter_state.filter_mode
        }
        var scalar_filters = ['start_date', 'end_date', 'ordering', 'participating_in', 'organizing', 'has_reward']
        scalar_filters.forEach(function (k) {
            if (self.filter_state[k]) {
                params[k] = self.filter_state[k]
            }
        })

        return CODALAB.api.get_public_competitions(params)
        .fail(function (resp) {
            $('#loading').hide()
            $('.pagination-nav').show()

            let message = "Could not load competition list"
            if (resp.responseJSON && resp.responseJSON.detail) {
                message = resp.responseJSON.detail
            } else if (resp.responseText) {
                try {
                    const json = JSON.parse(resp.responseText)
                    if (json.detail) {
                        message = json.detail
                    }
                } catch (_) {
                    message = resp.responseText
                }
            }
            toastr.error(message)
        })
        .done(handleSuccess)
    }

    self.get_array_length = function (arr) {
        return arr === undefined ? 0 : arr.length
    }

    self.pretty_date = function (date_string) {
        return !!date_string ? luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL) : ''
    }

    self.pretty_description = function (description) {
        return description.substring(0, 120) + (description.length > 120 ? '...' : '') || ''
    }

    self.get_url_page_number_or_default = function () {
        let urlParams = new URLSearchParams(window.location.search)
        if (urlParams.has('page')) {
            let pagenum = parseInt(urlParams.get('page'))
            if (pagenum < 1) {
                history.pushState("test", document.title, "?page=1")
                return 1
            } else {
                return pagenum
            }
        } else {
            history.pushState("test", document.title, "?page=1")
            return 1
        }
    }

    $(window).on('popstate', function () {
        self.update_competitions_list(self.get_url_page_number_or_default())
    })
  </script>

  <style type="text/stylus">
    public-list
      width 100%

    :scope
      display block
      margin-bottom 5px

    .page-header
      display flex
      align-items center
      justify-content space-between
      margin-bottom 20px

      .action-buttons
        display flex
        gap 10px

    .page-title
      margin 0
      font-size 24px
      font-weight bold
      color #1b1b1b
    
    .create-btn
      font-size 14px
      padding 0.5em 1em
      background-color #43637a
      color #fff
      text-decoration none
      border-radius 4px
      display inline-block
      cursor pointer
      transition background-color 0.2s ease

      &:hover
        background-color #2d3f4d
        color #fff
        text-decoration none

    // .external-competitions-banner / .external-btn live in
    // src/static/stylus/external_competitions.styl - shared with external_competitions/external_competition_list.tag

    .content-container
      display flex
      width 100%

    competition-filter-panel
      width 270px
      flex-shrink 0
      margin-right 15px

    .list-panel
      flex-grow 1

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
      all unset
      text-decoration none
      cursor pointer
      width 100%

    .tile-wrapper
      border solid 1px gainsboro
      display inline-flex
      min-width 425px
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
      padding 20px
      width 100%
      margin 0 auto

    .spinner
      border 4px solid rgba(0,0,0,.1)
      width 36px
      height 36px
      border-radius 50%
      border-top-color #3498db
      animation spin 1s ease-in-out infinite

    @keyframes spin
      0%
        transform rotate(0deg)
      100%
        transform rotate(360deg)
  </style>
</public-list>
