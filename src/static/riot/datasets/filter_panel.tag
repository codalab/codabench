<dataset-filter-panel>
  <div class="filters-panel ui segments">

    <!-- Search -->
    <div class="ui segment">
      <h4 class="ui header" style="margin-bottom: 8px;">Search</h4>
      <div class="ui fluid small left icon input">
        <i class="search icon"></i>
        <input type="text" placeholder="Search title/description..." ref="search_input" oninput="{ on_search_input }" value="{ filter_state.search }">
      </div>
    </div>

    <!-- Order By -->
    <div class="ui segment">
      <h5 class="ui header" style="margin-bottom: 8px;">Order by</h5>
      <div class="ui fluid selection dropdown" ref="order_by_dropdown">
        <input type="hidden" name="dataset_order" value="{ filter_state.ordering || 'recently_added' }">
        <i class="dropdown icon"></i>
        <div class="text">{ get_ordering_label(filter_state.ordering) }</div>
        <div class="menu">
          <div class="item" data-value="recently_added">Recently Added</div>
          <div class="item" data-value="most_downloaded">Most Downloaded</div>
        </div>
      </div>
    </div>

    <!-- Dataset Properties -->
    <div class="ui segment">
      <h5 class="ui header" style="margin-bottom: 8px;">Dataset Properties</h5>
      <div class="ui checkbox filter-item">
        <input type="checkbox" checked="{ filter_state.has_license }" onchange="{ toggle_has_license }">
        <label>Has License</label>
      </div>
      <div class="ui checkbox filter-item">
        <input type="checkbox" checked="{ filter_state.is_verified }" onchange="{ toggle_is_verified }">
        <label>Is Verified</label>
      </div>
    </div>

    <!-- Clear Filters -->
    <div class="ui secondary segment">
      <button type="button" class="ui fluid basic compact button clear-filters-btn" onclick="{ reset_all_filters }">
        <i class="undo icon"></i> Clear All Filters
      </button>
    </div>

  </div>

  <script>
    var self = this

    self.search_timer = null

    self.get_initial_filter_state = function (force_clean) {
        var initial = (!force_clean && opts.initial_filters && typeof opts.initial_filters === 'object')
            ? Object.assign({}, opts.initial_filters)
            : {}

        var state = {
            search: initial.search || '',
            ordering: initial.ordering || 'recently_added',
            has_license: Boolean(initial.has_license),
            is_verified: Boolean(initial.is_verified)
        }

        if (!force_clean && typeof window !== "undefined" && window.location) {
            var urlParams = new URLSearchParams(window.location.search)
            if (urlParams.has("ordering")) {
                var ord = urlParams.get("ordering")
                if (["most_downloaded", "recently_added"].includes(ord)) {
                    state.ordering = ord
                }
            }
        }

        return state
    }

    self.get_ordering_label = function (val) {
        if (val === 'most_downloaded') return 'Most Downloaded'
        return 'Recently Added'
    }

    self.filter_state = self.get_initial_filter_state(false)

    self.notify_filter_change = function () {
        if (typeof opts.onfilterchange === 'function') {
            opts.onfilterchange(Object.assign({}, self.filter_state))
        }
    }

    self.on_search_input = function (e) {
        self.filter_state.search = e.target.value
        if (self.search_timer) clearTimeout(self.search_timer)
        self.search_timer = setTimeout(function () {
            self.notify_filter_change()
        }, 400)
    }

    self.set_ordering = function (val) {
        if (!val) val = 'recently_added'
        if (self.filter_state.ordering === val) return
        self.filter_state.ordering = val
        self.update()
        self.notify_filter_change()
    }

    self.toggle_has_license = function (e) {
        self.filter_state.has_license = e.target.checked
        self.update()
        self.notify_filter_change()
    }

    self.toggle_is_verified = function (e) {
        self.filter_state.is_verified = e.target.checked
        self.update()
        self.notify_filter_change()
    }

    self.init_order_by_dropdown = function () {
        if (!self.refs.order_by_dropdown) return
        var $dropdown = $(self.refs.order_by_dropdown)
        $dropdown.dropdown({
            onChange: function (value, text, item) {
                self.set_ordering(value)
            }
        })
        var current_val = self.filter_state.ordering || 'recently_added'
        $dropdown.dropdown('set selected', current_val)
    }

    self.reset_all_filters = function (e) {
        if (e && e.currentTarget && e.currentTarget.blur) e.currentTarget.blur()
        self.filter_state = self.get_initial_filter_state(true)

        if (self.refs.search_input) self.refs.search_input.value = ''
        if (self.refs.order_by_dropdown) {
            $(self.refs.order_by_dropdown).dropdown('set selected', 'recently_added')
        }
        $(self.root).find('input[type="checkbox"]').prop('checked', false)

        self.update()
        self.notify_filter_change()
    }

    self.one('mount', function () {
        self.init_order_by_dropdown()
    })

    self.on('unmount', function () {
        if (self.search_timer) clearTimeout(self.search_timer)
    })
  </script>

  <style type="text/stylus">
    dataset-filter-panel
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

      // Search input
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
</dataset-filter-panel>
