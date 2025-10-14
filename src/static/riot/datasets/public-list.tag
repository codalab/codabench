<public-datasets>
  <!-- Title -->
  <div class="page-header">
    <h1 class="page-title">Public Datasets</h1>
    <a class="create-btn" href="{ URLS.DATASET_CREATE }?from=public">
      <i class="bi bi-plus-square-fill me-1"></i> Create
    </a>
  </div>

  <!-- Two-column layout -->
  <div class="content-container">

    <!-- Filters -->
    <div class="filters-panel">
        <h3>Filters</h3>

        <div class="filter-group">
            <label class="filter-label" for="search-title-description"><strong>Search by Title/Description</strong></label>
            <div class="ui input">
              <input type="text" id="search-title-description" oninput="{on_title_description_input}" placeholder="Enter title/description...">
            </div>
        </div>

        <div class="filter-group">
            <strong class="filter-label">Order By</strong>
            <label><input type="radio" name="order" value="most_downloaded" onchange="{set_ordering}"> Most downloaded first</label>
            <label><input type="radio" name="order" value="recently_added" onchange="{set_ordering}"> Recently added first</label>
        </div>

        <div class="filter-group">
            <strong class="filter-label">Dataset properties</strong>
            <label><input type="checkbox" onchange="{toggle_has_license}"> Has License</label>
            <label><input type="checkbox" onchange="{toggle_is_verified}"> Is Verified</label>
        </div>

        <div class="filter-group" show="{should_show_clear_filters()}">
            <button class="clear-filters-btn ui button" onclick="{clear_all_filters}">Clear All Filters</button>
        </div>
    </div>

    <!-- Datasets -->
    <div class="list-panel">
        <div id="loading" class="loading-indicator" show="{!datasets}">
            <div class="spinner"></div>
        </div>

        <!-- Dataset tiles -->
        <div each="{dataset in datasets.results}" class="tile-wrapper">
          <div class="full-width">
            <a class="link-no-deco" href="../{dataset.id}">
              <div class="dataset-info">
                  <h4 class="heading">{dataset.name}</h4>
                  <p class="dataset-description">{ pretty_description(dataset.description) }</p>
                  <div class="dataset-stats">
                    <div title="Created Date"><i class="bi bi-calendar-event-fill"></i> {pretty_date(dataset.created_when)}</div>
                    <div title="File Size"><i class="bi bi-file-earmark-fill"></i> {pretty_bytes(dataset.file_size)}</div>
                    <div title="License"><i class="bi bi-shield-shaded"></i> {dataset.license || 'N/A'}</div>
                    <div title="Downloads"><i class="bi bi-file-earmark-arrow-down-fill"></i> {dataset.downloads}</div>
                    <div if="{dataset.is_verified}" title="Verified"><i class="bi bi-check-circle-fill green"></i>Verified</div>
                  </div>
                  <div class="dataset-stats">
                    <div class="uploader">
                      <em>Uploaded by: <strong>{dataset.created_by}</strong></em>
                    </div>
                  </div>
              </div>
            </a>
          </div>
        </div>

        <div class="no-results-message" if="{datasets.results && datasets.results.length === 0}">
            <div class="ui warning message">
              <div class="header">No datasets found</div>
              Try changing your filters or search term.
            </div>
        </div>

        <div class="pagination-nav" if="{datasets.next || datasets.previous}">
            <button show="{datasets.previous}" onclick="{handle_ajax_pages.bind(this, -1)}" class="float-left ui inline button active">Back</button>
            <button hide="{datasets.previous}" disabled class="float-left ui inline button disabled">Back</button>
            { current_page } of {Math.ceil(datasets.count / datasets.page_size)}
            <button show="{datasets.next}" onclick="{handle_ajax_pages.bind(this, 1)}" class="float-right ui inline button active">Next</button>
            <button hide="{datasets.next}" disabled class="float-right ui inline button disabled">Next</button>
        </div>
    </div>
  </div>

  <script>
    var self = this
    self.search_timer = null
    self.datasets = {}

    self.filter_state = {
        search: '',
        ordering: '',
        has_license: false,
        is_verified: false,
    }

    self.on_title_description_input = function(e) {
        const value = e.target.value
        self.filter_state.search = value
        self.update()
        if (self.search_timer) clearTimeout(self.search_timer)
        self.search_timer = setTimeout(() => {
            self.update_datasets_list(1)
        }, 1000)
    }

    self.set_ordering = function (e) {
        self.filter_state.ordering = e.target.value
        self.update()
        self.update_datasets_list(1)
    }

    self.toggle_has_license = function(e) {
        self.filter_state.has_license = e.target.checked
        self.update()
        self.update_datasets_list(1)
    }

    self.toggle_is_verified = function(e) {
        self.filter_state.is_verified = e.target.checked
        self.update()
        self.update_datasets_list(1)
    }

    self.should_show_clear_filters = function () {
        const f = self.filter_state
        return f.search || f.ordering || f.has_license || f.is_verified
    }

    self.clear_all_filters = function() {
        self.filter_state = {
            search: '',
            ordering: '',
            has_license: false,
            is_verified: false,
        }
        document.getElementById('search-title-description').value = ''
        document.querySelectorAll('input[name="order"]').forEach(r => r.checked = false)
        document.querySelectorAll('input[type="checkbox"]').forEach(c => c.checked = false)
        self.update_datasets_list(1)
    }

    self.one("mount", function () {
        self.update_datasets_list(self.get_url_page_number_or_default())
    })

    self.handle_ajax_pages = function (num) {
        $('.pagination-nav > button').prop('disabled', true)
        self.update_datasets_list(self.get_url_page_number_or_default() + num)
    }

    self.update_datasets_list = function (num) {
        self.current_page = num;
        $('#loading').show();
        $('.pagination-nav').hide();

        function handleSuccess(response) {
            self.datasets = response;
            $('#loading').hide();
            $('.pagination-nav').show();
            history.pushState("", document.title, "?page=" + self.current_page);
            $('.pagination-nav > button').prop('disabled', false);
            self.update();
        }

        return CODALAB.api.get_public_datasets({
              "page": self.current_page,
              "search": self.filter_state.search,
              "ordering": self.filter_state.ordering,
              "has_license": self.filter_state.has_license,
              "is_verified": self.filter_state.is_verified
            })
            .fail(function (resp) {
                $('#loading').hide()
                $('.pagination-nav').show()
                let message = "Could not load datasets list"
                try {
                    const json = JSON.parse(resp.responseText)
                    if (json.detail) message = json.detail
                } catch (_) {
                    if (resp.responseText) message = resp.responseText
                }
                toastr.error(message)
            })
            .done(handleSuccess);
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
            let p = parseInt(urlParams.get('page'))
            return p < 1 ? 1 : p
        }
        return 1
    }

    $(window).on('popstate', function () {
        self.update_datasets_list(self.get_url_page_number_or_default())
    })
  </script>

  <style type="text/stylus">
    public-datasets
      width 100%

    :scope
      display block
      margin-bottom 5px

    .page-header
      display flex
      align-items center
      justify-content space-between
      margin-bottom 20px

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

    .link-no-deco
      all unset
      text-decoration none
      cursor pointer
      width 100%
    
    .full-width
      width 100%

    .tile-wrapper
      display flex
      border 1px solid #ddd
      padding 1em
      margin-bottom 1em
      border-radius 5px
      background-color #f9f9f9
      transition all 75ms ease-in-out

    .tile-wrapper:hover
      box-shadow 0 3px 4px -1px #cac9c9ff
      background-color #e6edf2
      border solid 1px #a5b7c5

    .dataset-info
      width 100%

    .dataset-info .heading
      font-size 1.2em
      margin-bottom 0.3em

    .dataset-description
      margin-bottom 0.5em
      font-size 13px
      line-height 1.15em
      color #555

    .uploader
      font-size 0.9em
      color #777

    .green
      color #009022ff

    .dataset-stats
      display flex
      flex-wrap wrap
      gap 1em
      font-size 0.9em
      align-items center
      margin-top 0.5em
      color #555

    .dataset-stats > div
      display flex
      align-items center
      gap 0.4em

    .ui.mini.primary.button
      padding 0.4em 0.8em
      font-size 0.85em

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
</public-datasets>
