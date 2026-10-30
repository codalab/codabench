<consulting-list>
  <!-- Title -->
  <div class="page-header">
    <h1 class="page-title">Consulting</h1>
  </div>

  <p class="consulting-blurb">
    This page lists independent consultants who offer help with organizing benchmarks and competitions.
    Codabench provides it as a courtesy to users who are looking for help. Please note that the consultants
    listed here are not affiliated with or endorsed by Codabench, and any arrangement is made directly
    between you and the consultant.
  </p>

  <!-- Logged-in user's own listing -->
  <div class="consulting-banner" if="{!my_listing_loading}">
    <span if="{!my_listing}">Do you offer consulting services to benchmark and competition organizers? Add your listing here.</span>
    <!-- Same message for every status; the status itself is shown on the My Listing page -->
    <span if="{my_listing}">You have a consulting listing. You can check its status, edit or remove it here.</span>

    <a class="consulting-btn" href="{URLS.CONSULTING_MY_LISTING}">{my_listing ? 'Manage your listing' : 'Add your listing'}</a>
  </div>

  <div class="list-panel">

    <!-- Hidden when there is nothing to sort -->
    <div class="sort-group" show="{listings.results && listings.results.length > 0}">
      <label for="consulting-ordering">Sort by</label>
      <select id="consulting-ordering" onchange="{on_ordering_change}">
        <option value="oldest">Oldest first</option>
        <option value="newest">Newest first</option>
        <option value="alphabetical">Alphabetical (A-Z)</option>
      </select>
    </div>

    <div class="loading-indicator" show="{loading}">
      <div class="spinner"></div>
    </div>

    <!-- Two cards per row -->
    <div class="listing-grid">
      <div each="{listing in listings.results}" class="listing-card">
        <div class="card-main">
          <div class="card-info">
            <div class="card-picture">
              <img src="{listing.picture}" loading="lazy">
            </div>
            <h4 class="heading">{listing.title}</h4>
            <div class="card-links">
              <a if="{listing.website_url}" href="{listing.website_url}" target="_blank" rel="noopener" title="Website"><i class="bi bi-globe"></i></a>
              <a if="{listing.linkedin_url}" href="{listing.linkedin_url}" target="_blank" rel="noopener" title="LinkedIn"><i class="bi bi-linkedin"></i></a>
              <a if="{listing.github_url}" href="{listing.github_url}" target="_blank" rel="noopener" title="GitHub"><i class="bi bi-github"></i></a>
            </div>
          </div>
          <button class="expand-btn" onclick="{toggle_description}" title="{listing.expanded ? 'Hide description' : 'Show description'}">
            <i class="bi {listing.expanded ? 'bi-chevron-up' : 'bi-chevron-down'}"></i>
          </button>
        </div>
        <!-- Filled with the rendered markdown on update -->
        <div class="card-description" show="{listing.expanded}" data-listing-id="{listing.id}"></div>
      </div>
    </div>

    <!-- Show when there are no listings -->
    <div class="no-results-message" if="{!loading && listings.results && listings.results.length === 0}">
      <div class="ui warning message">
        <div class="header">No consulting listings yet</div>
      </div>
    </div>

    <!--  Pagination  -->
    <div class="pagination-nav" if="{!loading && (listings.next || listings.previous)}">
      <button show="{listings.previous}" onclick="{handle_ajax_pages.bind(this, -1)}" class="float-left ui inline button">Back</button>
      <button hide="{listings.previous}" disabled="disabled" class="float-left ui inline button disabled">Back</button>
      { current_page } of {Math.ceil(listings.count/listings.page_size)}
      <button show="{listings.next}" onclick="{handle_ajax_pages.bind(this, 1)}" class="float-right ui inline button">Next</button>
      <button hide="{listings.next}" disabled="disabled" class="float-right ui inline button disabled">Next</button>
    </div>

  </div>

  <script>
    var self = this
    self.listings = {}
    self.loading = true
    self.current_page = 1
    self.ordering = 'oldest'
    self.my_listing = null
    // Anonymous users have no listing to load, so their banner can show right away
    self.my_listing_loading = CODALAB.state.user.logged_in

    self.one("mount", function () {
        self.update_listings(1)
        if (CODALAB.state.user.logged_in) {
            self.update_my_listing()
        }
    })

    // Descriptions are markdown, so they are rendered into the cards here instead of through a riot expression
    self.on("updated", function () {
        _.forEach(self.listings.results, function (listing) {
            if (listing.expanded) {
                $(self.root).find(`.card-description[data-listing-id="${listing.id}"]`).html(render_markdown(listing.description))
            }
        })
    })

    self.on_ordering_change = function (e) {
        self.ordering = e.target.value
        self.update_listings(1)
    }

    self.toggle_description = function (e) {
        e.item.listing.expanded = !e.item.listing.expanded
    }

    self.handle_ajax_pages = function (num) {
        self.update_listings(self.current_page + num)
            .done(function () {
                // Short pause so the user sees the new results appear before scrolling up
                setTimeout(function () {
                    window.scrollTo({top: 0, behavior: 'smooth'})
                }, 200)
            })
    }

    self.update_listings = function (num) {
        self.current_page = num
        self.loading = true
        self.update()

        return CODALAB.api.get_consulting_listings({
            "page": self.current_page,
            "ordering": self.ordering
        })
        .fail(function (response) {
            self.loading = false
            self.update()
            toastr.error(`Could not load consulting listings (status ${response.status})`)
        })
        .done(function (response) {
            self.listings = response
            self.loading = false
            self.update()
        })
    }

    self.update_my_listing = function () {
        CODALAB.api.get_my_consulting_listing()
            .done(function (response) {
                // Empty response (204) when the user has no listing
                self.my_listing = response || null
            })
            .always(function () {
                self.my_listing_loading = false
                self.update()
            })
    }
  </script>
</consulting-list>
