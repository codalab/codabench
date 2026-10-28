<competition-filter-panel>
  <div class="filters-panel ui segments">
    <!-- Search & Match Mode -->
    <div class="ui segment">
      <h4 class="ui header" style="margin-bottom: 8px;">Search</h4>
      <div class="ui fluid small left icon input">
        <i class="search icon"></i>
        <input type="text" placeholder="Search..." ref="search_input" oninput="{ on_search_input }" value="{ filter_state.search }">
      </div>

      <h5 class="ui header" style="margin-top: 12px; margin-bottom: 6px;">Filter Match Mode</h5>
      <div class="mode-pills-container">
        <button type="button" class="tag-pill mode-pill { active: filter_state.filter_mode === 'or' }" onclick="{ set_mode_or }">Any (OR)</button>
        <button type="button" class="tag-pill mode-pill { active: filter_state.filter_mode === 'and' }" onclick="{ set_mode_and }">All (AND)</button>
      </div>
    </div>

    <!-- Visibility (only if opts.show_visibility is true) -->
    <div class="ui segment" if="{ opts.show_visibility }">
      <h5 class="ui header" style="margin-bottom: 6px;">Visibility</h5>
      <div class="mode-pills-container">
        <button type="button" class="tag-pill mode-pill { active: filter_state.visibility === 'public' }" onclick="{ set_visibility.bind(this, 'public') }">Public</button>
        <button type="button" class="tag-pill mode-pill { active: filter_state.visibility === 'private' }" onclick="{ set_visibility.bind(this, 'private') }">Private</button>
        <button type="button" class="tag-pill mode-pill { active: filter_state.visibility === 'all' }" onclick="{ set_visibility.bind(this, 'all') }">All</button>
      </div>
    </div>

    <!-- Creation Date Range -->
    <div class="ui segment">
      <h5 class="ui header" style="margin-bottom: 8px;">Creation Date Range</h5>
      <div class="ui calendar" ref="start_calendar" style="margin-bottom: 6px;">
        <div class="ui fluid input left icon">
          <i class="calendar icon"></i>
          <input type="text" placeholder="Start Date">
        </div>
      </div>
      <div class="ui calendar" ref="end_calendar">
        <div class="ui fluid input left icon">
          <i class="calendar icon"></i>
          <input type="text" placeholder="End Date">
        </div>
      </div>
    </div>

    <!-- Order By (only if opts.show_ordering is true) -->
    <div class="ui segment" if="{ opts.show_ordering }">
      <h5 class="ui header" style="margin-bottom: 8px;">Order by</h5>
      <div class="ui fluid selection dropdown" ref="order_by_dropdown">
        <input type="hidden" name="order" value="{ filter_state.ordering || 'recent' }">
        <i class="dropdown icon"></i>
        <div class="text">{ get_ordering_label(filter_state.ordering) }</div>
        <div class="menu">
          <div class="item" data-value="recent">Recently Added</div>
          <div class="item" data-value="popular">Most Popular</div>
          <div class="item" data-value="with_most_submissions">Most Submissions</div>
        </div>
      </div>
    </div>

    <!-- Your Competitions -->
    <div class="ui segment">
      <h5 class="ui header" style="margin-bottom: 8px;">Your Competitions</h5>
      <div class="ui checkbox filter-item { disabled: !get_is_logged_in() }" style="margin-bottom: 6px;">
        <input type="checkbox" checked="{ filter_state.participating_in }" disabled="{ !get_is_logged_in() }" onchange="{ toggle_participating }">
        <label>Participating In <span if="{ !get_is_logged_in() }" class="filter-count">(Login required)</span></label>
      </div>
      <div class="ui checkbox filter-item { disabled: !get_is_logged_in() }">
        <input type="checkbox" checked="{ filter_state.organizing }" disabled="{ !get_is_logged_in() }" onchange="{ toggle_organizing }">
        <label>Organizing <span if="{ !get_is_logged_in() }" class="filter-count">(Login required)</span></label>
      </div>
    </div>

    <!-- Other filters -->
    <div class="ui segment">
      <h5 class="ui header" style="margin-bottom: 8px;">Other filters</h5>
      <div class="ui checkbox filter-item">
        <input type="checkbox" checked="{ filter_state.has_reward }" onchange="{ toggle_has_reward }">
        <label>Has reward</label>
      </div>
    </div>

    <!-- Tag Categories Accordion -->
    <div class="ui segment accordion category-accordion" each="{ cat in get_categories() }">
      <h5 class="title { open_cats[cat.name] !== false ? 'active' : '' } ui header" style="margin-bottom: 0;">
        { cat.name }
        <i class="dropdown icon" style="float: right;"></i>
      </h5>
      <div class="content { open_cats[cat.name] !== false ? 'active' : '' }" data-catname="{ cat.name }" style="margin-top: 4px;">
        <div class="tag-pills-container">
          <button type="button"
                  class="tag-pill { active: is_cat_no_tags_checked(cat) }"
                  if="{ cat.noTagsCount !== undefined }"
                  onclick="{ toggle_category_no_tags.bind(this, cat) }">
            <span class="tag-pill-name"><i>None</i></span>
            <span if="{ opts.show_counts && (cat.noTagsCount !== undefined) }" class="tag-pill-count">{ cat.noTagsCount }</span>
          </button>
          <button type="button"
                  class="tag-pill { active: is_tag_checked(cat, tag) }"
                  each="{ tag in cat.tags }"
                  onclick="{ toggle_tag.bind(this, cat.name, tag) }">
            <span class="tag-pill-name">{ tag.name }</span>
            <span if="{ opts.show_counts && (tag.count !== undefined) }" class="tag-pill-count">{ tag.count }</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Reset / Clear Filters -->
    <div class="ui secondary segment">
      <button type="button" class="ui fluid basic compact button clear-filters-btn" onclick="{ reset_all_filters }">
        <i class="undo icon"></i> Clear All Filters
      </button>
    </div>
  </div>

  <script>
    var self = this
    self.search_timer = null
    self.loaded_categories = []
    self.open_cats = {}

    self.get_is_logged_in = function () {
        if (opts.is_logged_in !== undefined) return Boolean(opts.is_logged_in)
        return Boolean(typeof CODALAB !== "undefined" && CODALAB.state && CODALAB.state.user && CODALAB.state.user.logged_in)
    }

    self.get_initial_filter_state = function (force_clean) {
        var initial = (!force_clean && opts.initial_filters && typeof opts.initial_filters === 'object')
            ? Object.assign({}, opts.initial_filters)
            : {}

        var defaults = {
            search: initial.search || '',
            filter_mode: initial.filter_mode || initial.mode || 'or',
            mode: initial.filter_mode || initial.mode || 'or',
            visibility: initial.visibility || 'public',
            ordering: initial.ordering || (opts.show_ordering ? 'recent' : ''),
            start_date: initial.start_date || '',
            end_date: initial.end_date || '',
            startDate: initial.startDate || (initial.start_date ? new Date(initial.start_date) : null),
            endDate: initial.endDate || (initial.end_date ? new Date(initial.end_date) : null),
            participating_in: Boolean(initial.participating_in),
            organizing: Boolean(initial.organizing),
            has_reward: Boolean(initial.has_reward),
            no_tags_by_category: initial.no_tags_by_category ? Object.assign({}, initial.no_tags_by_category) : {},
            selected_tags: initial.selected_tags ? Object.assign({}, initial.selected_tags) : {},
            selected_tags_by_cat: initial.selected_tags_by_cat ? JSON.parse(JSON.stringify(initial.selected_tags_by_cat)) : {}
        }

        if (!force_clean && opts.show_ordering && typeof window !== "undefined" && window.location) {
            var urlParams = new URLSearchParams(window.location.search)
            if (urlParams.has("ordering")) {
                var ord = urlParams.get("ordering")
                if (["popular", "recent", "with_most_submissions"].includes(ord)) {
                    defaults.ordering = ord
                }
            }
        }

        return defaults
    }

    self.get_ordering_label = function (val) {
        if (val === 'popular') return 'Most Popular'
        if (val === 'with_most_submissions') return 'Most Submissions'
        return 'Recently Added'
    }

    self.filter_state = self.get_initial_filter_state(false)

    self.get_categories = function () {
        if (opts.categories !== undefined && Array.isArray(opts.categories)) {
            return opts.categories
        }
        return self.loaded_categories || []
    }

    self.notify_filter_change = function () {
        if (typeof opts.onfilterchange === 'function') {
            self.filter_state.mode = self.filter_state.filter_mode
            self.filter_state.selectedTags = self.filter_state.selected_tags_by_cat
            opts.onfilterchange(self.filter_state)
        }
    }

    // Search with debounce (400ms)
    self.on_search_input = function (e) {
        self.filter_state.search = e.target.value

        if (self.search_timer) {
            clearTimeout(self.search_timer)
        }
        self.search_timer = setTimeout(function () {
            self.notify_filter_change()
        }, 400)
    }

    // Filter match mode
    self.set_filter_mode = function (mode, e) {
        if (e && e.currentTarget && e.currentTarget.blur) e.currentTarget.blur()
        if (self.filter_state.filter_mode === mode) return
        self.filter_state.filter_mode = mode
        self.filter_state.mode = mode
        self.update()
        self.notify_filter_change()
    }
    self.set_mode_or = function (e) { self.set_filter_mode('or', e) }
    self.set_mode_and = function (e) { self.set_filter_mode('and', e) }

    // Visibility
    self.set_visibility = function (val, e) {
        if (e && e.currentTarget && e.currentTarget.blur) e.currentTarget.blur()
        if (self.filter_state.visibility === val) return
        self.filter_state.visibility = val
        self.update()
        self.notify_filter_change()
    }

    // Order By
    self.set_ordering = function (val) {
        if (!val) val = 'recent'
        if (self.filter_state.ordering === val) return
        self.filter_state.ordering = val
        self.update()
        self.notify_filter_change()
    }

    // User competitions auth filters
    self.toggle_auth_filter = function (key, e) {
        if (!self.get_is_logged_in() && e.target.checked) {
            e.target.checked = false
            if (typeof toastr !== "undefined") {
                toastr.warning("Authentication required for filtering by participating in or organizing.")
            }
            return
        }
        self.filter_state[key] = e.target.checked
        self.update()
        self.notify_filter_change()
    }
    self.toggle_participating = function (e) { self.toggle_auth_filter('participating_in', e) }
    self.toggle_organizing = function (e) { self.toggle_auth_filter('organizing', e) }

    // Reward filter
    self.toggle_has_reward = function (e) {
        self.filter_state.has_reward = e.target.checked
        self.update()
        self.notify_filter_change()
    }

    // Category None toggle
    self.toggle_category_no_tags = function (cat, e) {
        if (e && e.preventDefault) e.preventDefault()
        if (e && e.currentTarget && e.currentTarget.blur) e.currentTarget.blur()
        var is_checked
        if (e && e.target && typeof e.target.checked === 'boolean') {
            is_checked = e.target.checked
        } else {
            is_checked = !self.is_cat_no_tags_checked(cat)
        }
        var cat_name = (typeof cat === 'object') ? cat.name : cat
        if (typeof cat === 'object') {
            cat.noTagsChecked = is_checked
        }
        if (is_checked) {
            self.filter_state.no_tags_by_category[cat_name] = true
            if (!self.filter_state.selected_tags_by_cat[cat_name]) {
                self.filter_state.selected_tags_by_cat[cat_name] = {}
            }
            self.filter_state.selected_tags_by_cat[cat_name]['_no_tags_'] = true
        } else {
            delete self.filter_state.no_tags_by_category[cat_name]
            if (self.filter_state.selected_tags_by_cat[cat_name]) {
                delete self.filter_state.selected_tags_by_cat[cat_name]['_no_tags_']
                if (Object.keys(self.filter_state.selected_tags_by_cat[cat_name]).length === 0) {
                    delete self.filter_state.selected_tags_by_cat[cat_name]
                }
            }
        }
        self.update()
        self.notify_filter_change()
    }

    // Specific tag toggle
    self.toggle_tag = function (cat_name, tag, e) {
        if (e && e.preventDefault) e.preventDefault()
        if (e && e.currentTarget && e.currentTarget.blur) e.currentTarget.blur()
        var is_checked
        if (e && e.target && typeof e.target.checked === 'boolean') {
            is_checked = e.target.checked
        } else {
            is_checked = !self.is_tag_checked({ name: cat_name }, tag)
        }
        if (tag && typeof tag === 'object') {
            tag.checked = is_checked
        }
        var tag_id = tag.id
        var tag_name = tag.name
        var key = (tag_id !== undefined && tag_id !== null) ? tag_id : tag_name

        if (is_checked) {
            self.filter_state.selected_tags[key] = true
            if (!self.filter_state.selected_tags_by_cat[cat_name]) {
                self.filter_state.selected_tags_by_cat[cat_name] = {}
            }
            self.filter_state.selected_tags_by_cat[cat_name][tag_name] = true
            if (tag_id !== undefined && tag_id !== null) {
                self.filter_state.selected_tags_by_cat[cat_name][tag_id] = true
            }
        } else {
            delete self.filter_state.selected_tags[key]
            if (self.filter_state.selected_tags_by_cat[cat_name]) {
                delete self.filter_state.selected_tags_by_cat[cat_name][tag_name]
                if (tag_id !== undefined && tag_id !== null) {
                    delete self.filter_state.selected_tags_by_cat[cat_name][tag_id]
                }
                if (Object.keys(self.filter_state.selected_tags_by_cat[cat_name]).length === 0) {
                    delete self.filter_state.selected_tags_by_cat[cat_name]
                }
            }
        }
        self.update()
        self.notify_filter_change()
    }

    self.get_tag_key = function (tag) {
        return (tag && tag.id !== undefined && tag.id !== null) ? tag.id : (tag && tag.name)
    }

    self.is_tag_checked = function (cat, tag) {
        if (!tag) return false
        if (tag.checked) return true
        var key = self.get_tag_key(tag)
        if (self.filter_state.selected_tags && self.filter_state.selected_tags[key]) return true
        if (cat && cat.name && self.filter_state.selected_tags_by_cat && self.filter_state.selected_tags_by_cat[cat.name]) {
            if (self.filter_state.selected_tags_by_cat[cat.name][tag.name]) return true
            if (tag.id !== undefined && self.filter_state.selected_tags_by_cat[cat.name][tag.id]) return true
        }
        return false
    }

    self.is_cat_no_tags_checked = function (cat) {
        if (!cat) return false
        if (cat.noTagsChecked) return true
        if (self.filter_state.no_tags_by_category && self.filter_state.no_tags_by_category[cat.name]) return true
        if (self.filter_state.selected_tags_by_cat && self.filter_state.selected_tags_by_cat[cat.name] && self.filter_state.selected_tags_by_cat[cat.name]['_no_tags_']) return true
        return false
    }

    // Reset filters
    self.reset_all_filters = function (e) {
        if (e && e.currentTarget && e.currentTarget.blur) e.currentTarget.blur()
        self.filter_state = self.get_initial_filter_state(true)

        var cats = self.get_categories()
        if (Array.isArray(cats)) {
            cats.forEach(function (cat) {
                cat.noTagsChecked = false
                if (Array.isArray(cat.tags)) {
                    cat.tags.forEach(function (t) {
                        t.checked = false
                    })
                }
            })
        }

        if (self.refs.search_input) {
            self.refs.search_input.value = ''
        }
        if (self.refs.start_calendar) {
            $(self.refs.start_calendar).calendar('clear')
        }
        if (self.refs.end_calendar) {
            $(self.refs.end_calendar).calendar('clear')
        }
        if (self.refs.order_by_dropdown) {
            $(self.refs.order_by_dropdown).dropdown('set selected', 'recent')
        }

        $(self.root).find('input[type="radio"]').prop('checked', false)
        $(self.root).find('input[type="checkbox"]').prop('checked', false)

        self.update()
        self.notify_filter_change()
    }
    self.resetFilters = self.reset_all_filters
    self.clear_all_filters = self.reset_all_filters

    self.init_order_by_dropdown = function () {
        if (!opts.show_ordering || !self.refs.order_by_dropdown) return
        var $dropdown = $(self.refs.order_by_dropdown)
        $dropdown.dropdown({
            onChange: function (value, text, item) {
                self.set_ordering(value)
            }
        })
        var current_val = self.filter_state.ordering || 'recent'
        $dropdown.dropdown('set selected', current_val)
    }

    self.init_calendars = function () {
        var general_calendar_options = {
            type: 'date',
            formatter: {
                date: function(date, settings) {
                    if (!date) return ''
                    var d = date.getDate(),
                        m = date.getMonth() + 1,
                        y = date.getFullYear()
                    return y + '-' + (m <= 9 ? '0' + m : m) + '-' + (d <= 9 ? '0' + d : d)
                }
            }
        }

        var start_options = Object.assign({}, general_calendar_options, {
            endCalendar: $(self.refs.end_calendar),
            onChange: function(date, text) {
                self.filter_state.start_date = text || ''
                self.filter_state.startDate = date ? new Date(date) : null
                self.notify_filter_change()
            }
        })

        var end_options = Object.assign({}, general_calendar_options, {
            startCalendar: $(self.refs.start_calendar),
            onChange: function(date, text) {
                self.filter_state.end_date = text || ''
                self.filter_state.endDate = date ? new Date(date) : null
                self.notify_filter_change()
            }
        })

        if (self.refs.start_calendar) {
            $(self.refs.start_calendar).calendar(start_options)
        }
        if (self.refs.end_calendar) {
            $(self.refs.end_calendar).calendar(end_options)
        }
    }

    self.init_accordions = function () {
        $(self.root).find('.category-accordion').accordion({
            exclusive: false,
            onOpen: function() {
                var catName = $(this).data('catname')
                if (catName) self.open_cats[catName] = true
            },
            onClose: function() {
                var catName = $(this).data('catname')
                if (catName) self.open_cats[catName] = false
            }
        })
    }

    self.fetch_tags = function () {
        if (opts.categories !== undefined) {
            return
        }
        if (typeof CODALAB === "undefined" || !CODALAB.api || !CODALAB.api.get_tags) {
            return
        }

        CODALAB.api.get_tags()
            .done(function (tags) {
                if (!Array.isArray(tags)) return
                var groups = {}
                tags.forEach(function (tag) {
                    var cat = tag.category_name || "Other"
                    if (!groups[cat]) groups[cat] = []
                    groups[cat].push(tag)
                })

                var categories = Object.keys(groups).sort()
                self.loaded_categories = categories.map(function (cat) {
                    var catTags = groups[cat]
                    return {
                        name: cat,
                        tags: catTags
                    }
                })
                self.update()
                setTimeout(self.init_accordions, 50)
            })
            .fail(function () {
                if (typeof toastr !== "undefined") {
                    toastr.error("Failed to load tags")
                }
            })
    }

    self.one("mount", function () {
        self.init_calendars()
        self.init_order_by_dropdown()
        self.fetch_tags()
        setTimeout(self.init_accordions, 50)
    })

    self.on("updated", function () {
        setTimeout(self.init_accordions, 30)
    })

    self.on("unmount", function () {
        if (self.search_timer) {
            clearTimeout(self.search_timer)
        }
    })
  </script>

  <style type="text/stylus">
    competition-filter-panel
      display block

    .filters-panel.ui.segments
      width 100%
      background #fff
      border 1px solid #e3e7ec !important
      border-radius 10px !important
      box-shadow 0 1px 2px rgba(0, 0, 0, 0.04) !important
      margin-top 0 !important
      margin-bottom 15px
      overflow hidden

      > .ui.segment
        background #fff !important
        border-top 1px solid #f1f4f7 !important
        padding 12px 14px !important
        margin 0 !important

        &:first-child
          border-top none !important

      .ui.header
        color #1b1b1b !important
        font-family inherit !important
        font-weight 700 !important
        font-size 15px !important
        letter-spacing -0.01em
        margin 0 0 8px 0

      h4.ui.header
        font-size 15px !important

      h5.ui.header
        font-size 14.5px !important

      // Search & Date Inputs
      .ui.input input
        border 1px solid #e3e7ec !important
        border-radius 6px !important
        font-size 13px
        color #1b1b1b
        background #fff
        padding 8px 10px 8px 34px !important
        transition border-color 0.15s ease, box-shadow 0.15s ease

        &:focus
          border-color #43637a !important
          box-shadow 0 0 0 2px rgba(67, 99, 122, 0.15) !important
          outline none

      .ui.icon.input > i.icon
        color #2e2e2e !important
        opacity 0.5 !important
        transition opacity 0.3s ease !important

      .ui.icon.input input:focus ~ i.icon
        opacity 0.85 !important

      .filter-item
        display block !important
        margin-bottom 6px !important
        font-size 13px
        color #2e2e2e

        label
          cursor pointer
          color #2e2e2e
          font-size 13px

          &:hover
            color #1b1b1b

        &.disabled
          opacity 0.5
          pointer-events none

      .filter-count
        color #888
        font-size 11px
        margin-left 4px

      .filter-scroll-list
        max-height 170px
        overflow-y auto
        padding-right 4px

      .category-accordion
        margin 0 !important
        border-radius 0 !important
        border-top 1px solid #f1f4f7 !important
        background #fff !important

        .title
          font-family inherit !important
          font-size 14.5px !important
          font-weight 700 !important
          color #1b1b1b !important
          cursor pointer
          user-select none
          display flex
          align-items center
          justify-content space-between
          padding 2px 0
          transition color 0.15s ease

          &:hover
            color #1b1b1b !important

          i.dropdown.icon
            float none !important
            color #555 !important
            opacity 0.7
            margin 0
            font-size 11px
            transition transform 0.2s ease

          &.active i.dropdown.icon
            transform rotate(90deg)

        .content
          padding-top 2px !important
          padding-bottom 2px !important

      .mode-pills-container
        display flex
        gap 6px
        width 100%

      .mode-pill
        flex 1
        justify-content center
        text-align center

      .tag-pills-container
        display flex
        flex-wrap wrap
        gap 6px
        align-items center
        max-height 220px
        overflow-y auto
        padding 2px 2px 4px 2px

      .tag-pill
        display inline-flex
        align-items center
        gap 4px
        padding 4px 9px
        font-size 12px
        font-weight 500
        line-height 1.2
        color var(--cb-navy-700, #36536d)
        background-color #f1f4f7
        border 1px solid #e2e8f0
        border-radius 6px
        cursor pointer
        transition all 0.15s ease-in-out
        user-select none
        box-shadow none !important
        text-align left
        max-width 100%

        &:hover
          background-color #e5ebf1
          border-color #cbd5e1
          color var(--cb-navy-900, #1b2f40)
          box-shadow none !important

        &:focus,
        &:active
          background-color #f1f4f7 !important
          border-color #e2e8f0 !important
          color var(--cb-navy-700, #36536d) !important
          outline none !important
          box-shadow none !important

        &.active
          background-color #43637a !important
          border-color #43637a !important
          color #ffffff !important
          box-shadow none !important

          &:hover
            background-color #2d3f4d !important
            border-color #2d3f4d !important
            opacity 0.95
            color #ffffff !important
            box-shadow none !important

          &:focus,
          &:active
            background-color #43637a !important
            border-color #43637a !important
            color #ffffff !important
            opacity 1 !important
            box-shadow none !important
            outline none !important

          .tag-pill-name
            color #ffffff

          .tag-pill-count
            background-color rgba(255, 255, 255, 0.25)
            color #ffffff

        .tag-pill-name
          white-space normal
          word-break break-word

        .tag-pill-count
          font-size 10px
          line-height 1
          padding 2px 5px
          border-radius 4px
          background-color #e2e8f0
          color #475569
          font-weight 600
          margin-left 2px

      .clear-filters-btn
        border 1px solid #e3e7ec !important
        border-radius 4px !important
        background-color #f8fafc !important
        color #2e2e2e !important
        font-weight 500 !important
        font-size 13px !important
        padding 9px 12px !important
        box-shadow none !important
        outline none !important
        transition all 0.15s ease-in-out !important

        i.icon
          color #555 !important
          opacity 0.85

        &:hover
          background-color #f1f4f7 !important
          border-color #cbd5e1 !important
          color #1b1b1b !important
          box-shadow none !important
          outline none !important

        &:focus,
        &:active
          background-color #f8fafc !important
          border-color #e3e7ec !important
          color #2e2e2e !important
          box-shadow none !important
          outline none !important

      input[type="radio"],
      input[type="checkbox"]
        margin-right 6px
        accent-color #43637a
  </style>
</competition-filter-panel>
