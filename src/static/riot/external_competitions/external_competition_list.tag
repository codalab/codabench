<external-competition-list>
  <!-- Title -->
  <div class="page-header">
    <h1 class="page-title">External Competitions</h1>
  </div>

  <p class="external-blurb">
    These competitions are hosted on other platforms (other Codabench and CodaLab instances)
    and are fetched here periodically. Codabench does not manage registration, submissions, or data for them -
    click through to a competition to view or join it on its original platform.
  </p>

  <div class="external-competitions-banner">
    <span>Do you want to list competitions from your platform here? Here's how to get started.</span>
    <a class="external-btn" href="https://docs.codabench.org/latest/Developers_and_Administrators/External-Competitions/" target="_blank" rel="noopener">View Docs</a>
  </div>

  <!-- Two-column layout -->
  <div class="content-container">

    <!-- Filters -->
    <div class="filters-panel">
        <!-- Filters main heading   -->
        <h3>Filters</h3>

        <!--  Search filter  -->
        <div class="filter-group">
            <label class="filter-label" for="search-title"><strong>Search</strong></label>
            <div class="ui input">
              <input type="text" id="search-title" oninput="{on_search_input}" placeholder="Search by name...">
            </div>
        </div>

        <!-- Platform filter   -->
        <div class="filter-group" id="platform-filter-group">
            <strong class="filter-label">Platform</strong>
            <label each="{platform in platforms}">
                <input type="checkbox" value="{platform.id}" onclick="{on_platform_toggle}"> {platform.name}
            </label>
        </div>

        <!--  Clear filters  -->
        <div class="filter-group" show="{should_show_clear_filters()}">
            <button class="clear-filters-btn ui button" onclick="{clear_all_filters}">Clear All Filters</button>
        </div>
    </div>

    <!-- Competitions -->
    <div class="list-panel">

      <div id="loading" class="loading-indicator" show="{!competitions}">
        <div class="spinner"></div>
      </div>

      <div each="{competition in competitions.results}" class="tile-wrapper">
        <div class="platform-badge" show="{ competition.platform_name }">{competition.platform_name}</div>
        <div class="ui square tiny bordered image img-wrapper">
          <img src="{competition.image_url}" loading="lazy">
        </div>
        <a class="link-no-deco full-width" href="{competition.competition_url}" target="_blank" rel="noopener">
          <div class="comp-info">
            <h4 class="heading">{competition.name}</h4>
            <p class="comp-description">{ pretty_description(competition.description) }</p>
            <div class="comp-stats">
              <div show="{ competition.platform_name }"><i class="bi bi-hdd-network-fill"></i> <span class="stat-label">Platform:</span> <span class="stat-value">{competition.platform_name}</span></div>
              <div show="{ competition.competition_created_when }"><i class="bi bi-calendar-event-fill"></i> <span class="stat-label">Created:</span> <span class="stat-value">{pretty_date(competition.competition_created_when)}</span></div>
              <div show="{ competition.competition_started_when }"><i class="bi bi-calendar2-week-fill"></i> <span class="stat-label">Start:</span> <span class="stat-value">{pretty_date(competition.competition_started_when)}</span></div>
              <div show="{ competition.organizer_name }"><i class="bi bi-person-fill"></i> <span class="stat-label">Organizer:</span> <span class="stat-value">{competition.organizer_name}</span></div>
            </div>
          </div>
        </a>
      </div>

      <!-- Show when there are no competitions in the list -->
      <div class="no-results-message" if="{competitions.results && competitions.results.length === 0}">
        <div class="ui warning message">
          <div class="header">No external competitions found</div>
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
    self.search_timer = null
    self.competitions = {}
    self.platforms = []

    // Filters state dictionary to keep track of which filters to apply
    self.filter_state = {
        search: '',
        platforms: []
    }

    // Function to set search (triggered when text is typed in the search box)
    self.on_search_input = function(e) {
        const value = e.target.value
        self.filter_state.search = value
        self.update()

        if (self.search_timer) {
            clearTimeout(self.search_timer)
        }

        self.search_timer = setTimeout(() => {
            self.update_competitions_list(1)
        }, 1000)  // wait 1 second after user stops typing
    }

    // Function to toggle a platform in/out of the filter (triggered when a checkbox is checked/unchecked)
    self.on_platform_toggle = function (e) {
        const id = e.target.value
        if (e.target.checked) {
            self.filter_state.platforms.push(id)
        } else {
            self.filter_state.platforms = self.filter_state.platforms.filter(p => p !== id)
        }
        self.update()
        self.update_competitions_list(1)
    }

    // Function that decides to show clear filter button or not
    self.should_show_clear_filters = function () {
        const { search, platforms } = self.filter_state
        return search || platforms.length > 0
    }

    // Function to clear all filters
    self.clear_all_filters = function() {
        self.filter_state = {
            search: '',
            platforms: []
        }

        // Clear inputs
        document.getElementById('search-title').value = ''
        document.querySelectorAll('#platform-filter-group input[type="checkbox"]').forEach(c => c.checked = false)

        // Call list update
        self.update_competitions_list(1)
    }

    self.one("mount", function () {
        // Load platforms once, to populate the filter dropdown
        CODALAB.api.get_external_competition_platforms()
            .done(function (response) {
                self.platforms = response
                self.update()
            })

        self.update_competitions_list(self.get_url_page_number_or_default())
    })

    self.handle_ajax_pages = function (num) {
        $('.pagination-nav > button').prop('disabled', true)
        self.update_competitions_list(self.get_url_page_number_or_default() + num)
    }

    self.update_competitions_list = function (num) {

        self.current_page = num;
        $('#loading').show();
        $('.pagination-nav').hide();

        function handleSuccess(response) {
            self.competitions = response;
            $('#loading').hide();
            $('.pagination-nav').show();
            history.pushState("", document.title, "?page=" + self.current_page);
            $('.pagination-nav > button').prop('disabled', false);
            self.update();
        }

        return CODALAB.api.get_external_competitions({
            "page": self.current_page,
            "search": self.filter_state.search,
            "platform": self.filter_state.platforms.join(',')
        })
        .fail(function (resp) {
            $('#loading').hide()
            $('.pagination-nav').show()

            let message = "Could not load external competitions list"
            if (resp.responseJSON && resp.responseJSON.detail) {
                message = resp.responseJSON.detail
            } else if (resp.responseText) {
                try {
                    const json = JSON.parse(resp.responseText)
                    if (json.detail) {
                        message = json.detail
                    }
                } catch (_) {
                    // fallback to raw text if not JSON
                    message = resp.responseText;
                }
            }
            toastr.error(message)
        })
        .done(handleSuccess);
    };

    self.pretty_date = function (date_string) {
        return !!date_string ? luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATE_FULL) : ''
    }

    self.pretty_description = function (description) {
        return description ? (description.substring(0, 120) + (description.length > 120 ? '...' : '')) : ''
    }

    self.get_url_page_number_or_default = function () {
        let urlParams = new URLSearchParams(window.location.search)
        if (urlParams.has('page')) {
            let pagenum = parseInt(urlParams.get('page'))
        if (pagenum < 1) {
            history.pushState("", document.title, "?page=1")
            return 1
        } else {
            return pagenum
        }
        } else {
            history.pushState("", document.title, "?page=1")
            return 1
        }
    }

    $(window).on('popstate', function () {
        self.update_competitions_list(self.get_url_page_number_or_default())
    })
  </script>

  <style type="text/stylus">
    external-competition-list
      width 100%

    :scope
      display block
      margin-bottom 5px
      background #f4f5f7
      padding 20px
      border-radius 6px

    .page-header
      display flex
      align-items center
      justify-content space-between
      margin-bottom 10px

    .page-title
      margin 0
      font-size 24px
      font-weight bold
      color #2c5a82

    .external-blurb
      font-size 13px
      color #5c5c5c
      margin-bottom 20px
      max-width 900px

    .external-competitions-banner
      display flex
      align-items center
      justify-content space-between
      padding 10px 15px
      margin-bottom 20px
      background #e9f0f8
      border 1px solid #c8daee
      border-radius 4px
      font-size 16px
      color #2c5a82

    .external-btn
      font-size 14px
      padding 0.5em 1em
      background-color #4684c7
      color #fff
      text-decoration none
      border-radius 4px
      display inline-block
      cursor pointer
      transition background-color 0.2s ease

      &:hover
        background-color #396ca3
        color #fff
        text-decoration none

    .content-container
      display flex
      width 100%

    .filters-panel
      width 250px
      flex-shrink 0
      border 1px solid #ddd
      padding 10px
      margin-right 10px
      margin-left 0 !important
      background #fff

      input[type="text"]
          width 100%
          padding 5px
          margin 5px 0 5px 0
          border 1px solid #ddd
          border-radius 4px

      input[type="checkbox"]
          margin-right 5px

    .filter-group
        margin-bottom 20px

    .filter-group label
        display block
        font-size 13px
        margin-bottom 6px

    .filter-label
        font-size 14px
        font-weight bold
        display block
        margin-bottom 8px

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

    .link-no-deco
      all unset
      text-decoration none
      cursor pointer
      width 100%

    .full-width
      width 100%

    .tile-wrapper
      position relative
      border solid 1px gainsboro
      display flex
      background-color #fff
      transition all 75ms ease-in-out
      width 100%
      margin-bottom 6px
      padding 1em
      border-radius 5px

    .tile-wrapper:hover
      box-shadow 0 3px 4px -1px #cac9c9ff
      transition all 75ms ease-in-out
      background-color #e9f0f8
      border solid 1px #c8daee

    .platform-badge
      position absolute
      top 8px
      right 8px
      background #4684c7
      color #fff
      font-size 11px
      font-weight 600
      padding 3px 8px
      border-radius 10px
      text-transform uppercase
      letter-spacing 0.03em

    .img-wrapper
      padding 5px
      align-self center

      img
        max-height 60px !important
        max-width 60px !important
        margin 0 auto

    .comp-info
      width 100%

    .comp-info .heading
      text-align left
      padding 5px
      color #1b1b1b
      margin-bottom 0.3em

    .comp-info .comp-description
      text-align left
      font-size 13px
      line-height 1.15em
      margin 0.35em
      color #555

    .comp-stats
      display flex
      flex-wrap wrap
      gap 1em
      font-size 0.9em
      align-items center
      margin-top 0.5em
      padding 0 0.35em
      color #555

    .comp-stats > div
      display flex
      align-items center
      gap 0.4em
      background #f0f2f4
      border-radius 12px
      padding 0.3em 0.7em

    .stat-label
      color #888

    .stat-value
      color #333
      font-weight normal

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
</external-competition-list>
