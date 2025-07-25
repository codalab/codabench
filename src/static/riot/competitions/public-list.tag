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

  <!-- Two-column layout -->
  <div class="content-container">

    <!-- Filters -->
    <div class="filters-panel">
        <!-- Filters main heading   -->
        <h3>Filters</h3>

        <!--  Search by title filter  -->
        <div class="filter-group">
            <label class="filter-label" for="search-title"><strong>Search by Title</strong></label>
            <div class="ui input">
              <input type="text" id="search-title" oninput="{on_title_input}" placeholder="Enter title...">
            </div>
        </div>

        <!-- Order by filter   -->
        <div class="filter-group">
            <strong class="filter-label">Order By</strong>
            <label><input type="radio" name="order" value="popular" onchange="{set_ordering}"> Most popular first</label>
            <label><input type="radio" name="order" value="recent" onchange="{set_ordering}"> Recently added first</label>
            <label><input type="radio" name="order" value="with_most_submissions" onchange="{set_ordering}"> With most submissions first</label>
        </div>

        <!-- Your competitions filters   -->
        <div class="filter-group">
            <strong class="filter-label">Your Competitions</strong>
            <label><input type="checkbox" onchange="{toggle_participating}"> Participating In</label>
            <label><input type="checkbox" onchange="{toggle_organizing}"> Organizing</label>
        </div>

        <!-- Your Other filter   -->
        <div class="filter-group">
            <strong class="filter-label">Other filters</strong>
            <label><input type="checkbox" onchange="{toggle_has_reward}"> Has reward</label>
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
    self.search_timer = null
    self.competitions = {}

    // Filters state dictionary to keep track of which filters to apply
    self.filter_state = {
        search: '',
        ordering: '',
        participating_in: false,
        organizing: false,
        has_reward: false
    }
    // Function to set search title (triggered when title is typed in the text box)
    self.on_title_input = function(e) {
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
    // Function to set ordering (triggered when a radio button is clicked)
    self.set_ordering = function (e) {
        self.filter_state.ordering = e.target.value
        self.update()
        self.update_competitions_list(1)
    }
    // Function to toggle participating (triggered when the checkbox is checked/uncheked)
    self.toggle_participating = function(e) {
        self.filter_state.participating_in = e.target.checked
        self.update()
        self.update_competitions_list(1)
    }
    // Function to toggle organizing (triggered when the checkbox is checked/uncheked)
    self.toggle_organizing = function(e) {
        self.filter_state.organizing = e.target.checked
        self.update()
        self.update_competitions_list(1)
    }
    // Function to toggle has reward (triggered when the checkbox is checked/uncheked)
    self.toggle_has_reward = function(e) {
        self.filter_state.has_reward = e.target.checked
        self.update()
        self.update_competitions_list(1)
    }

    // Function that decides to show clear filter button or not
    self.should_show_clear_filters = function () {
        const { search, ordering, participating_in, organizing, has_reward } = self.filter_state
        return search || ordering || participating_in || organizing || has_reward
    }
    // Function to clear all filters
    self.clear_all_filters = function() {
        self.filter_state = {
            search: '',
            ordering: '',
            participating_in: false,
            organizing: false,
            has_reward: false
        }

        // Clear inputs
        document.getElementById('search-title').value = ''
        document.querySelectorAll('input[name="order"]').forEach(r => r.checked = false)
        document.querySelectorAll('input[type="checkbox"]').forEach(c => c.checked = false)

        // Call list update
        self.update_competitions_list(1)
    }


    self.one("mount", function () {
        const urlParams = new URLSearchParams(window.location.search)

        // Check if ordering is set in the URL (e.g., ?ordering=popular)
        if (urlParams.has("ordering")) {
            const ordering = urlParams.get("ordering")
            if (["popular", "recent"].includes(ordering)) {
            self.filter_state.ordering = ordering

            // Set the corresponding radio button as checked
            const radio = document.querySelector(`input[name="order"][value="${ordering}"]`)
            if (radio) radio.checked = true
            }
        }
        
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

        return CODALAB.api.get_public_competitions({ 
            "page": self.current_page,
            "search": self.filter_state.search,
            "ordering": self.filter_state.ordering,
            "participating_in": self.filter_state.participating_in,
            "organizing": self.filter_state.organizing,
            "has_reward": self.filter_state.has_reward
        })
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
                    // fallback to raw text if not JSON
                    message = resp.responseText;
                }
            }
            toastr.error(message)
        })
        .done(handleSuccess);
    };

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
      background #f9f9f9

      input[type="text"]
          width 100%
          padding 5px
          margin 5px 0 5px 0
          border 1px solid #ddd
          border-radius 4px

      input[type="radio"],
      input[type="checkbox"]
          margin-right 5px

    .filter-group
        margin-bottom 20px

    .filter-label
        font-size 14px
        font-weight bold
        display block
        margin-bottom 8px

    .filter-group label
        display block
        font-size 13px
        margin-bottom 6px

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
