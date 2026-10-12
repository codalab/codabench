<dashboard-filters>
    <div class="ui segments filter-panel">
        <!-- Search & Match Mode -->
        <div class="ui segment">
            <h4 class="ui header" style="margin-bottom: 8px;">Search</h4>
            <div class="ui fluid small action input">
                <input type="text" placeholder="Search..." ref="searchInput" oninput="{ updateSearch }" value="{ opts.p.state.search }">
                <select class="ui compact dropdown" onchange="{ updateSearchField }" style="border-top-left-radius: 0; border-bottom-left-radius: 0;">
                    <option value="both" selected="{ opts.p.state.searchField === 'both' }">All</option>
                    <option value="title" selected="{ opts.p.state.searchField === 'title' }">Title</option>
                    <option value="organizer" selected="{ opts.p.state.searchField === 'organizer' }">Organizer</option>
                </select>
            </div>

            <h5 class="ui header" style="margin-top: 12px; margin-bottom: 6px;">Filter Match Mode</h5>
            <div class="ui mini fluid two buttons">
                <button class="ui button { active: opts.p.state.mode === 'or', blue: opts.p.state.mode === 'or' }" onclick="{ setModeOr }">Any (OR)</button>
                <button class="ui button { active: opts.p.state.mode === 'and', blue: opts.p.state.mode === 'and' }" onclick="{ setModeAnd }">All (AND)</button>
            </div>
        </div>

        <!-- Admin Visibility Option -->
        <div class="ui segment" if="{ opts.p.isAdmin }">
            <h5 class="ui header" style="margin-bottom: 6px;">Visibility</h5>
            <div class="ui mini fluid buttons">
                <button class="ui button { active: opts.p.state.visibility === 'public', blue: opts.p.state.visibility === 'public' }" onclick="{ setVisibility.bind(this, 'public') }">Public</button>
                <button class="ui button { active: opts.p.state.visibility === 'private', blue: opts.p.state.visibility === 'private' }" onclick="{ setVisibility.bind(this, 'private') }">Private</button>
                <button class="ui button { active: opts.p.state.visibility === 'all', blue: opts.p.state.visibility === 'all' }" onclick="{ setVisibility.bind(this, 'all') }">All</button>
            </div>
        </div>

        <!-- Date Filter -->
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

        <!-- Your Competitions -->
        <div class="ui segment">
            <h5 class="ui header" style="margin-bottom: 8px;">Your Competitions</h5>
            <div class="ui checkbox filter-item { disabled: !opts.p.isLoggedIn }" style="margin-bottom: 6px;">
                <input type="checkbox" checked="{ opts.p.state.participating_in }" disabled="{ !opts.p.isLoggedIn }" onchange="{ toggleParticipating }">
                <label>Participating In <span if="{ !opts.p.isLoggedIn }" class="filter-count">(Login required)</span></label>
            </div>
            <div class="ui checkbox filter-item { disabled: !opts.p.isLoggedIn }">
                <input type="checkbox" checked="{ opts.p.state.organizing }" disabled="{ !opts.p.isLoggedIn }" onchange="{ toggleOrganizing }">
                <label>Organizing <span if="{ !opts.p.isLoggedIn }" class="filter-count">(Login required)</span></label>
            </div>
        </div>

        <!-- Other filters -->
        <div class="ui segment">
            <h5 class="ui header" style="margin-bottom: 8px;">Other filters</h5>
            <div class="ui checkbox filter-item">
                <input type="checkbox" checked="{ opts.p.state.has_reward }" onchange="{ toggleHasReward }">
                <label>Has reward</label>
            </div>
        </div>

        <!-- Dynamic Categories -->
        <div class="ui segment accordion category-accordion" each="{ cat in opts.p.categoryFilters }">
            <h5 class="title { opts.p.state.openCats[cat.name] !== false ? 'active' : '' } ui header" style="margin-bottom: 0;">
                { cat.name }
                <i class="dropdown icon" style="float: right;"></i>
            </h5>
            <div class="content { opts.p.state.openCats[cat.name] !== false ? 'active' : '' }" data-catname="{ cat.name }" style="margin-top: 10px;">
                <div class="filter-scroll-list">
                    <div class="ui checkbox filter-item">
                        <input type="checkbox" checked="{ cat.noTagsChecked }" data-cat="{ cat.name }" data-tag="_no_tags_" onchange="{ toggleTagHandler }">
                        <label><i>None</i> <span class="filter-count">({ cat.noTagsCount })</span></label>
                    </div>
                    <div class="ui checkbox filter-item" each="{ tag in cat.tags }">
                        <input type="checkbox" checked="{ tag.checked }" data-cat="{ cat.name }" data-tag="{ tag.name }" onchange="{ toggleTagHandler }">
                        <label>{ tag.name } <span class="filter-count">({ tag.count })</span></label>
                    </div>
                </div>
            </div>
        </div>

        <!-- Reset Filters Button -->
        <div class="ui secondary segment">
            <button class="ui fluid basic compact button" onclick="{ resetFilters }">
                <i class="undo icon"></i> Reset all filters
            </button>
        </div>
    </div>

    <script>
        var self = this;
        // Bind event handlers to parent methods
        self.updateSearch = (e) => {
            opts.p.updateSearch(e);
        };
        self.updateSearchField = (e) => {
            opts.p.updateSearchField(e);
        };
        self.setModeOr = (e) => {
            opts.p.setModeOr(e);
        };
        self.setModeAnd = (e) => {
            opts.p.setModeAnd(e);
        };
        self.setVisibility = (val, e) => {
            opts.p.setVisibility(val, e);
        };
        self.toggleTagHandler = (e) => {
            opts.p.toggleTagHandler(e);
        };
        self.toggleParticipating = (e) => {
            opts.p.toggleParticipating(e);
        };
        self.toggleOrganizing = (e) => {
            opts.p.toggleOrganizing(e);
        };
        self.toggleHasReward = (e) => {
            opts.p.toggleHasReward(e);
        };
        self.resetFilters = (e) => {
            opts.p.resetFilters(e);
        };

        self.on('mount', () => {
            // Transfer refs to parent so calendars can be initialized
            opts.p.refs.start_calendar = self.refs.start_calendar;
            opts.p.refs.end_calendar = self.refs.end_calendar;
            opts.p.refs.searchInput = self.refs.searchInput;
        });
    </script>
</dashboard-filters>