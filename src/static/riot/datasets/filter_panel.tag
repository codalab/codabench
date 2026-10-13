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
      <h5 class="ui header" style="margin-bottom: 8px;">Order By</h5>
      <div class="filter-item">
        <label><input type="radio" name="dataset_order" value="most_downloaded" checked="{ filter_state.ordering === 'most_downloaded' }" onchange="{ set_ordering }"> Most downloaded first</label>
      </div>
      <div class="filter-item">
        <label><input type="radio" name="dataset_order" value="recently_added" checked="{ filter_state.ordering === 'recently_added' }" onchange="{ set_ordering }"> Recently added first</label>
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
      <button type="button" class="ui fluid basic compact button" onclick="{ reset_all_filters }">
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

        return {
            search: initial.search || '',
            ordering: initial.ordering || '',
            has_license: Boolean(initial.has_license),
            is_verified: Boolean(initial.is_verified)
        }
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

    self.set_ordering = function (e) {
        self.filter_state.ordering = e.target.value
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

    self.reset_all_filters = function () {
        self.filter_state = self.get_initial_filter_state(true)

        if (self.refs.search_input) self.refs.search_input.value = ''
        $(self.root).find('input[type="radio"]').prop('checked', false)
        $(self.root).find('input[type="checkbox"]').prop('checked', false)

        self.update()
        self.notify_filter_change()
    }

    self.on('unmount', function () {
        if (self.search_timer) clearTimeout(self.search_timer)
    })
  </script>

  <style type="text/stylus">
    dataset-filter-panel
      display block

    .filters-panel
      width 100%
      background #fff
      border-radius 4px
      margin-top 0 !important
      margin-bottom 15px

      .filter-item
        display block !important
        margin-bottom 6px !important
        font-size 13px

      input[type="radio"],
      input[type="checkbox"]
        margin-right 5px
  </style>
</dataset-filter-panel>
