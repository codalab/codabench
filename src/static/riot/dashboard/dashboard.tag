<dashboard>
    <div class="dashboard-page-container">
        <!-- Dashboard Header -->
        <div class="dashboard-header">
            <div class="dashboard-title-group">
                <h1 class="dashboard-title">
                    <i class="chart pie icon"></i>
                    Competitions Dashboard
                </h1>
                <p class="dashboard-subtitle">Analyze trends, organizers, and domains across Codabench</p>
            </div>
        </div>

        <div class="ui active inverted dimmer" if="{ loading }">
            <div class="ui large text loader">Fetching data...</div>
        </div>

        <div class="dashboard-layout" show="{ !loading }">
            <aside class="dashboard-sidebar">
                <competition-filter-panel show_visibility="{ isAdmin }" show_counts="{ true }" categories="{ categoryFilters }" onfilterchange="{ handleFilterChange }"></competition-filter-panel>
            </aside>

            <main class="dashboard-main">
                <!-- Navigation Tabs (Full width of the main content, excluding filter sidebar) -->
                <div class="ui tiny fluid three secondary pointing tabular menu details-menu dashboard-tabs-menu">
                    <a class="item { active: activeTab === 'overview' }" onclick="{ setActiveTab.bind(this, 'overview') }">Overview</a>
                    <a class="item { active: activeTab === 'tags' }" onclick="{ setActiveTab.bind(this, 'tags') }">Tags Statistics</a>
                    <a class="item { active: activeTab === 'explorer' }" onclick="{ setActiveTab.bind(this, 'explorer') }">Data Exploration</a>
                </div>

                <!-- Show when there are no competitions matching filters -->
                <div class="no-results-message" if="{ filteredCompetitions.length === 0 }" style="margin-bottom: 20px;">
                    <div class="ui warning message">
                        <div class="header">No competitions found</div>
                        Try changing your filters or search term.
                    </div>
                </div>

                <!-- Tab 1: Overview -->
                <dashboard-overview p="{ this }"></dashboard-overview>

                <!-- Tab 2: Tags Statistics -->
                <dashboard-tags-stats p="{ this }"></dashboard-tags-stats>

                <!-- Tab 3: Data Exploration -->
                <dashboard-table p="{ this }"></dashboard-table>
            </main>
        </div>
    </div>

    <script>
        var self = this;
        self.isAdmin = typeof CODALAB !== "undefined" && CODALAB.state && CODALAB.state.user && (CODALAB.state.user.is_superuser || CODALAB.state.user.is_staff);
        self.isLoggedIn = typeof CODALAB !== "undefined" && CODALAB.state && CODALAB.state.user && CODALAB.state.user.logged_in;

        self.loading = true;
        self.allCompetitions = [];
        self.filteredCompetitions = [];

        self.availableCategories = [];
        self.categoryFilters = [];
        self.chartCards = [];
        self.categoryTagsCounts = {};
        self.showOrgsChart = false;
        self.showCompsChart = false;
        self.popularCompetitions = [];
        self.showCumTagsChart = false;
        self.showHeatmapChart = false;
        self.categoriesWithTags = [];

        self.kpis = {
            distinctOrganizers: 0,
            participants: 0,
            submissions: 0
        };

        // Tabs & Navigation State
        self.activeTab = 'overview';
        self.setActiveTab = (tab) => {
            if (self.activeTab === tab) return;
            self.activeTab = tab;
            if (window.location.hash !== '#/' + tab) {
                window.location.hash = '#/' + tab;
            }
            self.update();
        };

        self.syncTabFromHash = () => {
            var rawHash = (window.location.hash || '').replace(/^#\/?/, '');
            if (['overview', 'tags', 'explorer'].includes(rawHash)) {
                if (self.activeTab !== rawHash) {
                    self.activeTab = rawHash;
                    self.update();
                }
            }
        };

        self.state = {
            search: "",
            mode: "or",
            filter_mode: "or",
            visibility: "public",
            participating_in: false,
            organizing: false,
            has_reward: false,
            startDate: null,
            endDate: null,
            selectedTags: {},
            type: "all"
        };

        self.myOrganizingIds = new Set();
        self.myParticipatingIds = new Set();

        self.on('mount', () => {
            self.syncTabFromHash();
            window.addEventListener('hashchange', self.syncTabFromHash);
            self.fetchData();
            self.fetchUserCompetitionIds();
        });

        self.on('unmount', () => {
            window.removeEventListener('hashchange', self.syncTabFromHash);
        });

        self.fetchUserCompetitionIds = () => {
            if (!self.isLoggedIn) return;

            const fetchAllIds = (initialUrl, onComplete) => {
                var collectedIds = new Set();
                const getPage = (url) => {
                    CODALAB.api.request('GET', url)
                        .done((response) => {
                            var results = response.results || (Array.isArray(response) ? response : []);
                            results.forEach((item) => {
                                if (item && item.id) collectedIds.add(item.id);
                            });
                            if (response.next) {
                                getPage(response.next);
                            } else {
                                onComplete(collectedIds);
                            }
                        })
                        .fail(() => {
                            onComplete(collectedIds);
                        });
                };
                getPage(initialUrl);
            };

            fetchAllIds(URLS.API + 'competitions/?mine=true&page_size=100', (ids) => {
                self.myOrganizingIds = ids;
                if (self.state.organizing) {
                    self.applyFilters();
                    self.update();
                }
            });

            fetchAllIds(URLS.API + 'competitions/?participating_in=true&page_size=100', (ids) => {
                self.myParticipatingIds = ids;
                if (self.state.participating_in) {
                    self.applyFilters();
                    self.update();
                }
            });
        };

        self.fetchData = () => {
            self.loading = true;
            self.update();

            var endpoint = (typeof URLS !== "undefined" && URLS.API) ? (URLS.API + "competitions/public/?page_size=5000") : "/api/competitions/public/?page_size=5000";
            var allRawCompetitions = [];

            const fetchPage = (url) => {
                var req = (typeof CODALAB !== "undefined" && CODALAB.api && CODALAB.api.request)
                    ? CODALAB.api.request("GET", url)
                    : fetch(url).then((r) => r.json());

                const handleSuccess = (response) => {
                    var rawList = Array.isArray(response) ? response : (response.results || []);
                    allRawCompetitions = allRawCompetitions.concat(rawList);
                    if (response && response.next) {
                        fetchPage(response.next);
                    } else {
                        self.allCompetitions = self.classifyCompetitions(allRawCompetitions);
                        self.onDataLoaded();
                    }
                };

                const handleError = () => {
                    self.allCompetitions = self.classifyCompetitions(allRawCompetitions);
                    self.onDataLoaded();
                };

                if (req && typeof req.done === "function") {
                    req.done(handleSuccess).fail(handleError);
                } else if (req && typeof req.then === "function") {
                    req.then(handleSuccess).catch(handleError);
                }
            };

            fetchPage(endpoint);
        };

        self.onDataLoaded = () => {
            self.loading = false;
            self.applyFilters();
            self.update();
        };

        // Extract categories and tags from raw API response to build filter menus
        self.classifyCompetitions = (list) => {
            self.globalCategoryTags = {};

            var mapped = list.map((item) => {
                var compUrl = (typeof URLS !== "undefined" && URLS.COMPETITION_DETAIL) ? URLS.COMPETITION_DETAIL(item.id) : ("/competitions/" + item.id + "/");
                var comp = {
                    id: item.id,
                    title: item.title,
                    organizer: item.created_by || item.owner_display_name || "Unknown",
                    url: compUrl,
                    published: item.published,
                    competition_type: item.competition_type || "competition",
                    participants_count: item.participants_count || 0,
                    submissions_count: item.submissions_count || 0,
                    created_when: item.created_when,
                    reward: item.reward || "",
                    has_reward: Boolean(item.reward && String(item.reward).trim().length > 0),
                    tagsByCategory: {}
                };

                if (item.tags && Array.isArray(item.tags)) {
                    item.tags.forEach((tag) => {
                        var cat = tag.category_name || tag.category || "Other";
                        if (!comp.tagsByCategory[cat]) comp.tagsByCategory[cat] = [];
                        comp.tagsByCategory[cat].push(tag.name);

                        if (!self.globalCategoryTags[cat]) self.globalCategoryTags[cat] = {};
                        self.globalCategoryTags[cat][tag.name] = true;
                    });
                }
                return comp;
            });

            self.availableCategories = Object.keys(self.globalCategoryTags).sort();
            self.state.selectedTags = {};
            self.chartCards = [];

            self.availableCategories.forEach((cat) => {
                self.state.selectedTags[cat] = {};
            });

            mapped.forEach((comp) => {
                comp.categoryColumns = self.availableCategories.map((cat) => {
                    return (comp.tagsByCategory[cat] || []).join(", ");
                });
            });

            return mapped;
        };

        self.handleFilterChange = function (filters) {
            self.state.search = (filters.search || "").toLowerCase();
            self.state.mode = filters.filter_mode || filters.mode || "or";
            self.state.filter_mode = self.state.mode;
            self.state.visibility = filters.visibility || "public";
            self.state.participating_in = Boolean(filters.participating_in);
            self.state.organizing = Boolean(filters.organizing);
            self.state.has_reward = Boolean(filters.has_reward);
            self.state.startDate = filters.startDate || (filters.start_date ? new Date(filters.start_date) : null);
            self.state.endDate = filters.endDate || (filters.end_date ? new Date(filters.end_date) : null);
            self.state.selectedTags = filters.selected_tags_by_cat || {};

            self.applyFilters();
            self.update();
        };

        // Check if competition tags match selected filters (AND/OR mode)
        function tagMatch(compTagsByCat, selectedTagsByCat) {
            var hasAnySelection = false;
            var cats = Object.keys(selectedTagsByCat);
            for (var i = 0; i < cats.length; i++) {
                if (Object.keys(selectedTagsByCat[cats[i]]).length > 0) {
                    hasAnySelection = true;
                    break;
                }
            }
            if (!hasAnySelection) return true;

            if (self.state.mode === "and") {
                for (var i = 0; i < cats.length; i++) {
                    var cat = cats[i];
                    var selected = Object.keys(selectedTagsByCat[cat]);
                    var compTags = compTagsByCat[cat] || [];
                    var allMatch = true;
                    selected.forEach((it) => {
                        if (it === '_no_tags_') {
                            if (compTags.length > 0) allMatch = false;
                        } else {
                            if (compTags.indexOf(it) === -1) allMatch = false;
                        }
                    });
                    if (!allMatch) return false;
                }
                return true;
            } else {
                for (var i = 0; i < cats.length; i++) {
                    var cat = cats[i];
                    var selected = Object.keys(selectedTagsByCat[cat]);
                    var compTags = compTagsByCat[cat] || [];
                    var anyMatch = false;
                    selected.forEach((it) => {
                        if (it === '_no_tags_') {
                            if (compTags.length === 0) anyMatch = true;
                        } else {
                            if (compTags.indexOf(it) !== -1) anyMatch = true;
                        }
                    });
                    if (anyMatch) return true;
                }
                return false;
            }
        }

        // Main filter pipeline: Text search -> Dates -> Visibility -> Type -> Facets (User Comps / Reward / Tags)
        self.applyFilters = () => {
            var s = self.state.search;
            var userCompActive = Boolean(self.state.participating_in || self.state.organizing);
            var rewardActive = Boolean(self.state.has_reward);

            var tagsActive = false;
            var tagCats = Object.keys(self.state.selectedTags);
            for (var i = 0; i < tagCats.length; i++) {
                if (Object.keys(self.state.selectedTags[tagCats[i]]).length > 0) {
                    tagsActive = true;
                    break;
                }
            }

            self.filteredCompetitions = self.allCompetitions.filter((c) => {
                if (self.isAdmin) {
                    if (self.state.visibility === 'public' && !c.published) return false;
                    if (self.state.visibility === 'private' && c.published) return false;
                }
                if (self.state.type !== 'all' && c.competition_type !== self.state.type) {
                    return false;
                }

                if (self.state.startDate || self.state.endDate) {
                    var compDate = c.created_when ? new Date(c.created_when) : null;
                    if (!compDate) return false;

                    if (self.state.startDate && compDate < self.state.startDate) return false;

                    if (self.state.endDate) {
                        var endLimit = new Date(self.state.endDate);
                        endLimit.setHours(23, 59, 59, 999);
                        if (compDate > endLimit) return false;
                    }
                }
                if (s) {
                    var matchTitle = (c.title || "").toLowerCase().indexOf(s) !== -1;
                    var matchOrg = (c.organizer || "").toLowerCase().indexOf(s) !== -1;
                    if (!matchTitle && !matchOrg) return false;
                }

                if (self.state.mode === "and") {
                    if (self.state.participating_in && !self.myParticipatingIds.has(c.id)) return false;
                    if (self.state.organizing && !self.myOrganizingIds.has(c.id)) return false;
                    if (self.state.has_reward && !c.has_reward) return false;
                    if (tagsActive && !tagMatch(c.tagsByCategory, self.state.selectedTags)) return false;
                } else {
                    if (userCompActive || rewardActive || tagsActive) {
                        var matchesAny = false;
                        if (self.state.participating_in && self.myParticipatingIds.has(c.id)) matchesAny = true;
                        if (self.state.organizing && self.myOrganizingIds.has(c.id)) matchesAny = true;
                        if (self.state.has_reward && c.has_reward) matchesAny = true;
                        if (tagsActive && tagMatch(c.tagsByCategory, self.state.selectedTags)) matchesAny = true;
                        if (!matchesAny) return false;
                    }
                }
                return true;
            });

            // Calculate KPIs
            var totalPart = 0, totalSub = 0;
            var orgSet = new Set();
            self.filteredCompetitions.forEach((c) => {
                totalPart += (c.participants_count || 0);
                totalSub += (c.submissions_count || 0);
                if (c.organizer) orgSet.add(c.organizer);
            });
            self.kpis.distinctOrganizers = orgSet.size;
            self.kpis.participants = totalPart;
            self.kpis.submissions = totalSub;

            // Compute dynamic tag counts
            self.categoryTagsCounts = {};
            self.availableCategories.forEach((cat) => {
                self.categoryTagsCounts[cat] = {};
            });

            self.filteredCompetitions.forEach((c) => {
                Object.keys(c.tagsByCategory).forEach((cat) => {
                    if (!self.categoryTagsCounts[cat]) self.categoryTagsCounts[cat] = {};
                    c.tagsByCategory[cat].forEach((t) => {
                        self.categoryTagsCounts[cat][t] = (self.categoryTagsCounts[cat][t] || 0) + 1;
                    });
                });
            });

            // Dynamic filter panel categories
            self.categoryFilters = self.availableCategories.map((cat) => {
                var globalTagsObj = self.globalCategoryTags[cat] || {};
                var allTagNames = Object.keys(globalTagsObj);
                var activeCounts = self.categoryTagsCounts[cat] || {};

                var tagsList = allTagNames.map((name) => {
                    return {
                        id: name,
                        name: name,
                        count: activeCounts[name] || 0
                    };
                });

                var noTagsCount = 0;
                self.filteredCompetitions.forEach((c) => {
                    var compTags = (c.tagsByCategory && c.tagsByCategory[cat]) || [];
                    if (compTags.length === 0) {
                        noTagsCount++;
                    }
                });

                var isNoTagsChecked = Boolean(
                    self.state.selectedTags &&
                    self.state.selectedTags[cat] &&
                    self.state.selectedTags[cat]['_no_tags_']
                );

                return {
                    id: cat,
                    name: cat,
                    noTagsCount: noTagsCount,
                    noTagsChecked: isNoTagsChecked,
                    tags: tagsList
                };
            });

            // Prepare categories with active tags
            self.chartCards = [];
            self.categoriesWithTags = [];
            self.availableCategories.forEach((cat, idx) => {
                var counts = self.categoryTagsCounts[cat] || {};
                var activeTagKeys = Object.keys(counts).filter((k) => counts[k] > 0);
                if (activeTagKeys.length > 0) {
                    self.categoriesWithTags.push(cat);
                    var cardId = "chCat_" + cat.replace(/[^a-zA-Z0-9]/g, "_");
                    self.chartCards.push({
                        id: cardId,
                        catName: cat,
                        typeIdx: idx
                    });
                }
            });

            // Overview flags
            self.showOrgsChart = self.filteredCompetitions.length > 0 && self.kpis.distinctOrganizers > 1;

            var benchmarkComps = self.filteredCompetitions.filter((c) => c.competition_type === "benchmark");
            var pool = benchmarkComps.length > 0 ? benchmarkComps : self.filteredCompetitions;
            var sortedPool = pool.slice().sort((a, b) => {
                var pDiff = (b.participants_count || 0) - (a.participants_count || 0);
                if (pDiff !== 0) return pDiff;
                return (b.submissions_count || 0) - (a.submissions_count || 0);
            });
            self.popularCompetitions = sortedPool.slice(0, 10);
            self.showCompsChart = self.popularCompetitions.length > 0;

            self.showCumTagsChart = self.filteredCompetitions.length > 0 && self.categoriesWithTags.length > 0;
            self.showHeatmapChart = self.filteredCompetitions.length > 0 && self.categoriesWithTags.length >= 2;
        };
    </script>
</dashboard>