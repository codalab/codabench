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

        <div class="ui active inverted dimmer" if="{ loading }">
            <div class="ui large text loader">Fetching data...</div>
        </div>

        <div class="dashboard-layout" show="{ !loading }">
            <aside class="dashboard-sidebar">
                <competition-filter-panel show_visibility="{ isAdmin }" show_counts="{ true }" categories="{ categoryFilters }" onfilterchange="{ handleFilterChange }"></competition-filter-panel>
            </aside>

            <main class="dashboard-main">
                <!-- Show when there are no competitions matching filters -->
                <div class="no-results-message" if="{ filteredCompetitions.length === 0 }" style="margin-bottom: 20px;">
                    <div class="ui warning message">
                        <div class="header">No competitions found</div>
                        Try changing your filters or search term.
                    </div>
                </div>

                <dashboard-charts p="{ this }"></dashboard-charts>
                <dashboard-table p="{ this }"></dashboard-table>
            </main>
        </div>
    </div>

    <script>
        var self = this;
        self.isAdmin = typeof CODALAB !== "undefined" && CODALAB.state && CODALAB.state.user && (CODALAB.state.user.is_superuser || CODALAB.state.user.is_staff);
        self.isLoggedIn = typeof CODALAB !== "undefined" && CODALAB.state && CODALAB.state.user && CODALAB.state.user.logged_in;

        self.loading = true;
        self.dataSource = "api";
        self.allCompetitions = [];
        self.filteredCompetitions = [];
        self.pagedCompetitions = [];
        self.pageSize = 15;
        self.currentPage = 1;
        self.totalPages = 1;

        self.availableCategories = [];
        self.categoryFilters = [];
        self.chartCards = [];
        self.categoryTagsCounts = {};
        self.showOrgsChart = false;
        self.showCompsChart = false;
        self.showCumTagsChart = false;
        self.showHeatmapChart = false;
        self.categoriesWithTags = [];

        self.kpis = {
            distinctOrganizers: 0,
            participants: 0,
            submissions: 0
        };

        // 4 New Notebook Charts State
        self.launchesInterval = 'yearly';
        self.launchesStartDateStr = '';
        self.launchesEndDateStr = '';
        self.selectedCumCat = null;
        self.heatmapCat1 = null;
        self.heatmapCat2 = null;
        self.heatmapNormalize = false;

        // Filter and sort state
        self.state = {
            search: "",
            filter_mode: "or",
            mode: "or",
            visibility: "public",
            type: "all",
            participating_in: false,
            organizing: false,
            has_reward: false,
            selectedTags: {},
            sortKey: "id",
            sortDir: 1,
            startDate: null,
            endDate: null
        };

        self.charts = {};
        self.search_timer = null;

        var PALETTE = ["#2185d0", "#00b5ad", "#21ba45", "#fbbd08", "#f2711c", "#db2828", "#a333c8", "#e03997", "#767676"];

        self.myOrganizingIds = new Set();
        self.myParticipatingIds = new Set();

        self.on('mount', () => {
            self.fetchData();
            self.fetchUserCompetitionIds();
        });

        self.fetchUserCompetitionIds = () => {
            if (!self.isLoggedIn) return;

            const fetchAllIds = (initialUrl, onComplete) => {
                var collectedIds = new Set();
                const getPage = (url) => {
                    CODALAB.api.request('GET', url)
                        .done((resp) => {
                            var items = (resp && resp.results) ? resp.results : [];
                            items.forEach((c) => collectedIds.add(c.id));
                            if (resp && resp.next) {
                                var parser = document.createElement('a');
                                parser.href = resp.next;
                                var relativeUrl = parser.pathname + parser.search;
                                getPage(relativeUrl);
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

            var baseApi = (typeof URLS !== "undefined" && URLS.API) ? URLS.API : "/api/";
            fetchAllIds(baseApi + "competitions/?mine=true&page_size=1000", (ids) => {
                self.myOrganizingIds = ids;
                if (self.state.organizing) {
                    self.applyFilters();
                    self.update();
                    setTimeout(self.initOrUpdateCharts, 50);
                }
            });

            fetchAllIds(baseApi + "competitions/?participating_in=true&page_size=1000", (ids) => {
                self.myParticipatingIds = ids;
                if (self.state.participating_in) {
                    self.applyFilters();
                    self.update();
                    setTimeout(self.initOrUpdateCharts, 50);
                }
            });
        };

        // Fetch all competitions using recursive pagination to enable client-side filtering
        self.fetchData = () => {
            self.loading = true;
            self.update();

            var allResults = [];
            var apiUrl = (typeof URLS !== "undefined" && URLS.API) ? URLS.API + "competitions/?page_size=1000" : "/api/competitions/?page_size=1000";
            if (self.isAdmin) {
                apiUrl += "&visibility=all";
            } else {
                apiUrl += "&visibility=public";
            }

            var tagsUrl = (typeof URLS !== "undefined" && URLS.API) ? URLS.API + "tags/" : "/api/tags/";
            self.globalCategoryTags = self.globalCategoryTags || {};
            CODALAB.api.request('GET', tagsUrl)
                .done((tagsData) => {
                    if (Array.isArray(tagsData)) {
                        tagsData.forEach((tag) => {
                            var cat = tag.category_name || "Other";
                            if (!self.globalCategoryTags[cat]) self.globalCategoryTags[cat] = {};
                            self.globalCategoryTags[cat][tag.name] = true;
                        });
                    }
                    fetchPage(apiUrl);
                })
                .fail(() => {
                    // Fall back to extracting tags from competitions data
                    fetchPage(apiUrl);
                });

            const fetchPage = (url) => {
                CODALAB.api.request('GET', url)
                    .done((resp) => {
                        var results = (resp && resp.results) ? resp.results : [];
                        allResults = allResults.concat(results);

                        if (resp && resp.next) {
                            var parser = document.createElement('a');
                            parser.href = resp.next;
                            var relativeUrl = parser.pathname + parser.search;
                            fetchPage(relativeUrl);
                        } else {
                            self.allCompetitions = self.classifyCompetitions(allResults);
                            self.dataSource = "api";
                            self.onDataLoaded();
                        }
                    })
                    .fail(() => {
                        if (typeof toastr !== "undefined") toastr.error("Failed to load competitions data");
                        if (allResults.length > 0) {
                            self.allCompetitions = self.classifyCompetitions(allResults);
                        } else {
                            self.allCompetitions = [];
                        }
                        self.dataSource = "api";
                        self.onDataLoaded();
                    });
            }
        };

        self.onDataLoaded = () => {
            self.loading = false;
            self.applyFilters();
            self.update();
            setTimeout(() => {
                self.initOrUpdateCharts();
            }, 50);
        };

        // Extract categories and tags from raw API response to build filter menus
        self.classifyCompetitions = (list) => {
            if (!self.globalCategoryTags) self.globalCategoryTags = {};

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

            if (!self.selectedCumCat || !self.availableCategories.includes(self.selectedCumCat)) {
                self.selectedCumCat = self.availableCategories[0] || null;
            }
            if (!self.heatmapCat1 || !self.availableCategories.includes(self.heatmapCat1)) {
                self.heatmapCat1 = self.availableCategories[0] || null;
            }
            if (!self.heatmapCat2 || !self.availableCategories.includes(self.heatmapCat2)) {
                self.heatmapCat2 = self.availableCategories[1] || self.availableCategories[0] || null;
            }

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

            self.currentPage = 1;
            self.applyFilters();
            self.update();
            setTimeout(self.initOrUpdateCharts, 50);
        };

        self.sortTableId = () => {
            self.sortTable('id');
        };
        self.sortTableTitle = () => {
            self.sortTable('title');
        };
        self.sortTableOrg = () => {
            self.sortTable('organizer');
        };

        self.sortTable = (key) => {
            if (self.state.sortKey === key) {
                self.state.sortDir *= -1;
            } else {
                self.state.sortKey = key;
                self.state.sortDir = 1;
            }
            self.applyFilters();
            self.update();
        };

        self.changePagePrev = () => {
            var p = self.currentPage - 1;
            if (p >= 1 && p <= self.totalPages) {
                self.currentPage = p;
                self.updatePagination();
            }
        };

        self.changePageNext = () => {
            var p = self.currentPage + 1;
            if (p >= 1 && p <= self.totalPages) {
                self.currentPage = p;
                self.updatePagination();
            }
        };

        // Check if competition tags match selected filters (AND/OR mode)
        function tagMatch(compTagsByCat, selectedTagsByCat) {
            var hasAnySelection = false;
            var cats = Object.keys(selectedTagsByCat);
            for (var i = 0; i < cats.length; i++) {
                if (Object.keys(selectedTagsByCat[cats[i]]).length > 0) {
                    hasAnySelection = true;
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
            var isAndMode = self.state.mode === "and";
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
            var hasActiveFacet = userCompActive || rewardActive || tagsActive;
            var myUsername = (CODALAB.state.user && CODALAB.state.user.username) || "";

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

                    // We must include the entire end date up to midnight
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

                if (hasActiveFacet) {
                    var userCompMatch = false;
                    if (userCompActive) {
                        var isOrganizer = (self.myOrganizingIds && self.myOrganizingIds.has(c.id)) || Boolean(myUsername && c.organizer === myUsername);
                        var isParticipant = Boolean(self.myParticipatingIds && self.myParticipatingIds.has(c.id));
                        userCompMatch = (self.state.participating_in && self.state.organizing)
                            ? (isParticipant || isOrganizer)
                            : (self.state.participating_in ? isParticipant : isOrganizer);
                    }

                    var rewardMatch = rewardActive && Boolean(c.has_reward);
                    var tagsMatch = tagsActive && tagMatch(c.tagsByCategory, self.state.selectedTags);

                    if (isAndMode) {
                        if (userCompActive && !userCompMatch) return false;
                        if (rewardActive && !rewardMatch) return false;
                        if (tagsActive && !tagsMatch) return false;
                    } else {
                        if (!userCompMatch && !rewardMatch && !tagsMatch) return false;
                    }
                }

                return true;
            });

            self.filteredCompetitions.sort((a, b) => {
                var vA = a[self.state.sortKey];
                var vB = b[self.state.sortKey];
                if (typeof vA === "string") vA = vA.toLowerCase();
                if (typeof vB === "string") vB = vB.toLowerCase();
                if (vA < vB) return -1 * self.state.sortDir;
                if (vA > vB) return 1 * self.state.sortDir;
                return 0;
            });

            var orgs = {};
            self.categoryTagsCounts = {};
            var totalTags = 0;
            var totalParticipants = 0;
            var totalSubmissions = 0;
            self.noTagsCounts = {};
            self.filteredCompetitions.forEach((c) => {
                orgs[c.organizer] = true;
                totalParticipants += (c.participants_count || 0);
                totalSubmissions += (c.submissions_count || 0);

                Object.keys(c.tagsByCategory).forEach((cat) => {
                    if (!self.categoryTagsCounts[cat]) self.categoryTagsCounts[cat] = {};
                    c.tagsByCategory[cat].forEach((t) => {
                        totalTags++;
                        self.categoryTagsCounts[cat][t] = (self.categoryTagsCounts[cat][t] || 0) + 1;
                    });
                });

                self.availableCategories.forEach((cat) => {
                    if (!c.tagsByCategory[cat] || c.tagsByCategory[cat].length === 0) {
                        self.noTagsCounts[cat] = (self.noTagsCounts[cat] || 0) + 1;
                    }
                });
            });

            self.kpis.distinctOrganizers = Object.keys(orgs).length;
            self.kpis.tagsAssigned = totalTags;
            self.kpis.participants = totalParticipants;
            self.kpis.submissions = totalSubmissions;

            self.categoryFilters = [];
            self.availableCategories.forEach((cat) => {
                var counts = self.categoryTagsCounts[cat] || {};
                var allTagsForCat = Object.keys(self.globalCategoryTags[cat]);

                var tagsArr = allTagsForCat.map((k) => {
                    var isChecked = false;
                    if (self.state.selectedTags[cat] && self.state.selectedTags[cat][k]) {
                        isChecked = true;
                    }
                    return {
                        name: k,
                        count: (counts[k] || 0),
                        checked: isChecked
                    };
                });

                var noTagsChecked = (self.state.selectedTags[cat] && self.state.selectedTags[cat]['_no_tags_']) ? true : false;

                self.categoryFilters.push({
                    name: cat,
                    tags: tagsArr,
                    noTagsCount: self.noTagsCounts[cat] || 0,
                    noTagsChecked: noTagsChecked
                });
            });

            var oPairs = countOrgs(self.filteredCompetitions, 10);
            self.showOrgsChart = oPairs.length > 0;

            var cPairs = self.filteredCompetitions
                .filter((c) => (c.participants_count || 0) > 0)
                .map((c) => {
                    var shortTitle = c.title.length > 25 ? c.title.substring(0, 25) + '...' : c.title;
                    return [shortTitle, c.participants_count || 0];
                })
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);
            self.showCompsChart = cPairs.length > 0;

            self.chartCards = [];
            self.categoriesWithTags = [];
            self.availableCategories.forEach((cat, catIdx) => {
                var counts = self.categoryTagsCounts[cat] || {};
                var hasData = Object.keys(counts).some((k) => counts[k] > 0);
                if (hasData) {
                    self.categoriesWithTags.push(cat);
                    self.chartCards.push({
                        catName: cat,
                        id: "chart_cat_" + cat.replace(/[^a-zA-Z0-9]/g, "_"),
                        typeIdx: catIdx
                    });
                }
            });

            self.showCumTagsChart = self.filteredCompetitions.length > 0 && self.categoriesWithTags.length > 0;
            self.showHeatmapChart = self.filteredCompetitions.length > 0 && self.categoriesWithTags.length > 0;

            if (self.categoriesWithTags.length > 0) {
                if (!self.selectedCumCat || !self.categoriesWithTags.includes(self.selectedCumCat)) {
                    self.selectedCumCat = self.categoriesWithTags[0];
                }
                if (!self.heatmapCat1 || !self.categoriesWithTags.includes(self.heatmapCat1)) {
                    self.heatmapCat1 = self.categoriesWithTags[0];
                }
                if (!self.heatmapCat2 || !self.categoriesWithTags.includes(self.heatmapCat2)) {
                    self.heatmapCat2 = self.categoriesWithTags[1] || self.categoriesWithTags[0];
                }
            } else {
                self.selectedCumCat = null;
                self.heatmapCat1 = null;
                self.heatmapCat2 = null;
            }

            self.totalPages = Math.max(1, Math.ceil(self.filteredCompetitions.length / self.pageSize));
            self.currentPage = Math.min(self.currentPage, self.totalPages);
            self.updatePagination();
        };

        self.updatePagination = () => {
            var start = (self.currentPage - 1) * self.pageSize;
            self.pagedCompetitions = self.filteredCompetitions.slice(start, start + self.pageSize);
        };

        function countOrgs(list, limit) {
            var map = {};
            list.forEach((c) => {
                map[c.organizer] = (map[c.organizer] || 0) + 1;
            });
            var entries = Object.keys(map).map((k) => {
                return [k, map[k]];
            });
            entries.sort((a, b) => {
                return b[1] - a[1];
            });
            return entries.slice(0, limit);
        }

        // Cycle through Bar, Doughnut, and Vertical Bar charts for tag categories
        self.initOrUpdateCharts = () => {
            var rows = self.filteredCompetitions;
            var hasCompetitions = rows.length > 0;

            var visibleIds = new Set();
            if (hasCompetitions) {
                visibleIds.add("chCumulativeGrowth");
                visibleIds.add("chLaunches");
            }
            if (self.showCumTagsChart) visibleIds.add("chCumTags");
            if (self.showHeatmapChart) visibleIds.add("chHeatmap");
            if (self.showOrgsChart) visibleIds.add("chOrgs");
            if (self.showCompsChart) visibleIds.add("chComps");
            self.chartCards.forEach((c) => visibleIds.add(c.id));

            Object.keys(self.charts).forEach((id) => {
                if (!visibleIds.has(id)) {
                    if (self.charts[id]) {
                        self.charts[id].destroy();
                        delete self.charts[id];
                    }
                }
            });

            if (hasCompetitions) {
                self.renderCumulativeGrowthChart();
                self.renderLaunchesChart();
            }
            if (self.showCumTagsChart) {
                self.renderCumTagsChart();
            }
            if (self.showHeatmapChart) {
                self.renderHeatmapChart();
            }

            if (self.showOrgsChart) {
                var oPairs = countOrgs(rows, 10);
                self.renderHorizontalBar("chOrgs", oPairs, "#21ba45");
            }

            if (self.showCompsChart) {
                var cPairs = rows
                    .filter((c) => (c.participants_count || 0) > 0)
                    .map((c) => {
                        var shortTitle = c.title.length > 25 ? c.title.substring(0, 25) + '...' : c.title;
                        return [shortTitle, c.participants_count || 0];
                    })
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 10);
                self.renderHorizontalBar("chComps", cPairs, "#fbbd08");
            }

            self.chartCards.forEach((chart) => {
                var cat = chart.catName;
                var counts = self.categoryTagsCounts[cat] || {};
                var pairs = Object.keys(counts).map((k) => {
                    return [k, counts[k]];
                });
                pairs.sort((a, b) => {
                    return b[1] - a[1];
                });
                pairs = pairs.slice(0, 15);

                var canvasId = chart.id;
                var el = document.getElementById(canvasId);
                var color = PALETTE[chart.typeIdx % PALETTE.length];

                if (el) {
                    if (chart.typeIdx % 3 === 0) {
                        self.renderHorizontalBarId(canvasId, pairs, color, el);
                    } else if (chart.typeIdx % 3 === 1) {
                        self.renderDoughnutId(canvasId, pairs, el);
                    } else {
                        self.renderVerticalBarId(canvasId, pairs, color, el);
                    }
                }
            });
        };

        self.renderHorizontalBar = (refName, pairs, color) => {
            var el = (self.refs && self.refs[refName]) || document.getElementById(refName);
            if (!el) return;
            self.renderHorizontalBarId(refName, pairs, color, el);
        };

        self.renderHorizontalBarId = (id, pairs, color, elementObj) => {
            var el = elementObj || document.getElementById(id);
            if (!el) return;
            var labels = pairs.map((p) => p[0]);
            var dataVals = pairs.map((p) => p[1]);

            if (self.charts[id] && self.charts[id].ctx && self.charts[id].ctx.canvas === el) {
                self.charts[id].data.labels = labels;
                self.charts[id].data.datasets[0].data = dataVals;
                self.charts[id].update();
            } else {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                }
                self.charts[id] = new Chart(el, {
                    type: "horizontalBar",
                    data: {
                        labels: labels,
                        datasets: [{
                            data: dataVals,
                            backgroundColor: color || "#2185d0",
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false
                        },
                        scales: {
                            xAxes: [{
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0
                                }
                            }],
                            yAxes: [{
                                gridLines: {
                                    display: false
                                }
                            }]
                        }
                    }
                });
            }
        };

        self.renderDoughnutId = (id, pairs, elementObj) => {
            var el = elementObj || document.getElementById(id);
            if (!el) return;
            var labels = pairs.map((p) => p[0]);
            var dataVals = pairs.map((p) => p[1]);

            if (self.charts[id] && self.charts[id].ctx && self.charts[id].ctx.canvas === el) {
                self.charts[id].data.labels = labels;
                self.charts[id].data.datasets[0].data = dataVals;
                self.charts[id].data.datasets[0].backgroundColor = labels.map((_, i) => {
                    return PALETTE[(i + 5) % PALETTE.length];
                });
                self.charts[id].update();
            } else {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                }
                self.charts[id] = new Chart(el, {
                    type: "doughnut",
                    data: {
                        labels: labels,
                        datasets: [{
                            data: dataVals,
                            backgroundColor: labels.map((_, i) => {
                                return PALETTE[(i + 5) % PALETTE.length];
                            })
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutoutPercentage: 55,
                        legend: {
                            position: "right",
                            labels: {
                                boxWidth: 12,
                                fontSize: 12
                            }
                        }
                    }
                });
            }
        };

        self.renderVerticalBarId = (id, pairs, color, elementObj) => {
            var el = elementObj || document.getElementById(id);
            if (!el) return;
            var labels = pairs.map((p) => p[0]);
            var dataVals = pairs.map((p) => p[1]);

            if (self.charts[id] && self.charts[id].ctx && self.charts[id].ctx.canvas === el) {
                self.charts[id].data.labels = labels;
                self.charts[id].data.datasets[0].data = dataVals;
                self.charts[id].update();
            } else {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                }
                self.charts[id] = new Chart(el, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [{
                            data: dataVals,
                            backgroundColor: color || "#a333c8",
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false
                        },
                        scales: {
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0
                                }
                            }],
                            xAxes: [{
                                gridLines: {
                                    display: false
                                }
                            }]
                        }
                    }
                });
            }
        };

        function getBluesColor(pct) {
            if (pct <= 0) return "#f8fafc";
            var r = Math.round(240 - pct * (240 - 8));
            var g = Math.round(246 - pct * (246 - 65));
            var b = Math.round(252 - pct * (252 - 145));
            return "rgb(" + r + "," + g + "," + b + ")";
        }

        self.renderCumulativeGrowthChart = () => {
            var id = "chCumulativeGrowth";
            var el = (self.refs && self.refs[id]) || document.getElementById(id);
            if (!el) return;

            var validComps = self.filteredCompetitions.filter(function (c) {
                return c.created_when && !isNaN(new Date(c.created_when).getTime());
            });

            if (validComps.length === 0) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            validComps.sort(function (a, b) {
                return new Date(a.created_when) - new Date(b.created_when);
            });

            var startDate = new Date(validComps[0].created_when);
            var endDate = new Date(validComps[validComps.length - 1].created_when);

            var startY = startDate.getUTCFullYear();
            var startM = startDate.getUTCMonth();
            var endY = endDate.getUTCFullYear();
            var endM = endDate.getUTCMonth();

            var months = [];
            var curY = startY, curM = startM;
            while (curY < endY || (curY === endY && curM <= endM)) {
                var mStr = curY + "-" + (curM + 1 < 10 ? "0" : "") + (curM + 1);
                months.push(mStr);
                curM++;
                if (curM > 11) {
                    curM = 0;
                    curY++;
                }
            }

            var countsByMonth = {};
            validComps.forEach(function (c) {
                var d = new Date(c.created_when);
                var mStr = d.getUTCFullYear() + "-" + (d.getUTCMonth() + 1 < 10 ? "0" : "") + (d.getUTCMonth() + 1);
                countsByMonth[mStr] = (countsByMonth[mStr] || 0) + 1;
            });

            var runningTotal = 0;
            var cumData = months.map(function (m) {
                runningTotal += (countsByMonth[m] || 0);
                return runningTotal;
            });

            if (self.charts[id] && self.charts[id].ctx && self.charts[id].ctx.canvas === el) {
                self.charts[id].data.labels = months;
                self.charts[id].data.datasets[0].data = cumData;
                self.charts[id].update();
            } else {
                if (self.charts[id]) self.charts[id].destroy();
                self.charts[id] = new Chart(el, {
                    type: "line",
                    data: {
                        labels: months,
                        datasets: [{
                            label: "Cumulative Competitions",
                            data: cumData,
                            borderColor: "#2980b9",
                            backgroundColor: "rgba(41, 128, 185, 0.08)",
                            borderWidth: 2.5,
                            pointRadius: months.length > 36 ? 0 : 2,
                            pointHoverRadius: 5,
                            pointBackgroundColor: "#2980b9",
                            fill: true,
                            lineTension: 0.15
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: { display: false },
                        tooltips: {
                            mode: "index",
                            intersect: false
                        },
                        scales: {
                            xAxes: [{
                                gridLines: { display: false },
                                ticks: {
                                    autoSkip: true,
                                    maxTicksLimit: 12,
                                    maxRotation: 45,
                                    minRotation: 0
                                }
                            }],
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0
                                }
                            }]
                        }
                    }
                });
            }
        };

        self.renderLaunchesChart = () => {
            var id = "chLaunches";
            var el = (self.refs && self.refs[id]) || document.getElementById(id);
            if (!el) return;

            var startDate = self.launchesStartDateStr ? new Date(self.launchesStartDateStr + "T00:00:00Z") : null;
            var endDate = self.launchesEndDateStr ? new Date(self.launchesEndDateStr + "T23:59:59.999Z") : null;

            var validComps = self.filteredCompetitions.filter(function (c) {
                if (!c.created_when) return false;
                var d = new Date(c.created_when);
                if (isNaN(d.getTime())) return false;
                if (startDate && d < startDate) return false;
                if (endDate && d > endDate) return false;
                return true;
            });

            if (validComps.length === 0) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            var interval = self.launchesInterval || "yearly";

            function getBucketKey(d) {
                var y = d.getUTCFullYear();
                var m = d.getUTCMonth();
                if (interval === "yearly") {
                    return y.toString();
                } else if (interval === "semiannual") {
                    return y + (m < 6 ? "-S1" : "-S2");
                } else if (interval === "monthly") {
                    return y + "-" + (m + 1 < 10 ? "0" : "") + (m + 1);
                } else {
                    // Weekly (ISO 8601 week)
                    var target = new Date(Date.UTC(y, m, d.getUTCDate()));
                    var dayNr = target.getUTCDay() || 7;
                    target.setUTCDate(target.getUTCDate() + 4 - dayNr);
                    var yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
                    var weekNo = Math.ceil((((target - yearStart) / 86400000) + 1) / 7);
                    return target.getUTCFullYear() + "-W" + (weekNo < 10 ? "0" : "") + weekNo;
                }
            }

            var counts = {};
            validComps.forEach(function (c) {
                var k = getBucketKey(new Date(c.created_when));
                counts[k] = (counts[k] || 0) + 1;
            });

            var labels = Object.keys(counts).sort();

            // Continuous ranges for yearly, semiannual, monthly
            if (labels.length > 1 && interval === "yearly") {
                var minYear = parseInt(labels[0], 10);
                var maxYear = parseInt(labels[labels.length - 1], 10);
                var fullYears = [];
                for (var yr = minYear; yr <= maxYear; yr++) {
                    fullYears.push(yr.toString());
                }
                labels = fullYears;
            } else if (labels.length > 1 && interval === "semiannual") {
                var startY = parseInt(labels[0].split("-")[0], 10);
                var startS = labels[0].split("-")[1] === "S1" ? 1 : 2;
                var endY = parseInt(labels[labels.length - 1].split("-")[0], 10);
                var endS = labels[labels.length - 1].split("-")[1] === "S1" ? 1 : 2;
                var fullSem = [];
                var cY = startY, cS = startS;
                while (cY < endY || (cY === endY && cS <= endS)) {
                    fullSem.push(cY + "-S" + cS);
                    if (cS === 1) {
                        cS = 2;
                    } else {
                        cS = 1;
                        cY++;
                    }
                }
                labels = fullSem;
            } else if (labels.length > 1 && interval === "monthly") {
                var startP = labels[0].split("-");
                var endP = labels[labels.length - 1].split("-");
                var sY = parseInt(startP[0], 10), sM = parseInt(startP[1], 10) - 1;
                var eY = parseInt(endP[0], 10), eM = parseInt(endP[1], 10) - 1;
                var fullM = [];
                var curY = sY, curM = sM;
                while (curY < eY || (curY === eY && curM <= eM)) {
                    fullM.push(curY + "-" + (curM + 1 < 10 ? "0" : "") + (curM + 1));
                    curM++;
                    if (curM > 11) {
                        curM = 0;
                        curY++;
                    }
                }
                labels = fullM;
            }

            var dataVals = labels.map(function (k) {
                return counts[k] || 0;
            });

            if (self.charts[id] && self.charts[id].ctx && self.charts[id].ctx.canvas === el) {
                self.charts[id].data.labels = labels;
                self.charts[id].data.datasets[0].data = dataVals;
                self.charts[id].update();
            } else {
                if (self.charts[id]) self.charts[id].destroy();
                self.charts[id] = new Chart(el, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "Launches",
                            data: dataVals,
                            backgroundColor: "#2980b9",
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: { display: false },
                        scales: {
                            xAxes: [{
                                gridLines: { display: false },
                                ticks: {
                                    autoSkip: true,
                                    maxTicksLimit: 20,
                                    maxRotation: 45,
                                    minRotation: 0
                                }
                            }],
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0
                                }
                            }]
                        }
                    }
                });
            }
        };

        self.renderCumTagsChart = () => {
            var id = "chCumTags";
            var el = (self.refs && self.refs[id]) || document.getElementById(id);
            if (!self.showCumTagsChart) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            var available = (self.categoriesWithTags && self.categoriesWithTags.length > 0) ? self.categoriesWithTags : self.availableCategories;
            var cat = self.selectedCumCat;
            if (!cat || !available.includes(cat)) {
                cat = available[0] || null;
                self.selectedCumCat = cat;
            }

            if (!cat) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            var compsWithCat = [];
            var tagTotals = {};
            self.filteredCompetitions.forEach(function (c) {
                if (!c.created_when) return;
                var d = new Date(c.created_when);
                if (isNaN(d.getTime())) return;
                var tags = (c.tagsByCategory && c.tagsByCategory[cat]) || [];
                if (tags.length > 0) {
                    tags.forEach(function (t) {
                        tagTotals[t] = (tagTotals[t] || 0) + 1;
                    });
                    compsWithCat.push({ date: d, tags: tags });
                }
            });

            var topTags = Object.keys(tagTotals).sort(function (a, b) {
                return tagTotals[b] - tagTotals[a];
            }).slice(0, 10);

            if (topTags.length === 0 || compsWithCat.length === 0) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            compsWithCat.sort(function (a, b) {
                return a.date - b.date;
            });

            var startY = compsWithCat[0].date.getUTCFullYear();
            var startM = compsWithCat[0].date.getUTCMonth();
            var endY = compsWithCat[compsWithCat.length - 1].date.getUTCFullYear();
            var endM = compsWithCat[compsWithCat.length - 1].date.getUTCMonth();

            var months = [];
            var curY = startY, curM = startM;
            while (curY < endY || (curY === endY && curM <= endM)) {
                var mStr = curY + "-" + (curM + 1 < 10 ? "0" : "") + (curM + 1);
                months.push(mStr);
                curM++;
                if (curM > 11) {
                    curM = 0;
                    curY++;
                }
            }

            var monthlyCounts = {};
            compsWithCat.forEach(function (item) {
                var d = item.date;
                var mStr = d.getUTCFullYear() + "-" + (d.getUTCMonth() + 1 < 10 ? "0" : "") + (d.getUTCMonth() + 1);
                if (!monthlyCounts[mStr]) monthlyCounts[mStr] = {};
                item.tags.forEach(function (t) {
                    if (topTags.includes(t)) {
                        monthlyCounts[mStr][t] = (monthlyCounts[mStr][t] || 0) + 1;
                    }
                });
            });

            var CUM_PALETTE = ["#2185d0", "#21ba45", "#f2711c", "#a333c8", "#00b5ad", "#fbbd08", "#db2828", "#e03997", "#34495e", "#16a085"];
            var datasets = topTags.map(function (t, idx) {
                var col = CUM_PALETTE[idx % CUM_PALETTE.length];
                var running = 0;
                var series = months.map(function (m) {
                    running += (monthlyCounts[m] && monthlyCounts[m][t]) ? monthlyCounts[m][t] : 0;
                    return running;
                });
                return {
                    label: t + " (" + tagTotals[t] + ")",
                    data: series,
                    borderColor: col,
                    backgroundColor: "transparent",
                    borderWidth: 2,
                    pointRadius: months.length > 36 ? 0 : 2,
                    pointHoverRadius: 4,
                    pointBackgroundColor: col,
                    fill: false,
                    lineTension: 0.15
                };
            });

            if (self.charts[id] && self.charts[id].ctx && self.charts[id].ctx.canvas === el) {
                self.charts[id].data.labels = months;
                self.charts[id].data.datasets = datasets;
                self.charts[id].update();
            } else {
                if (self.charts[id]) self.charts[id].destroy();
                self.charts[id] = new Chart(el, {
                    type: "line",
                    data: {
                        labels: months,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: true,
                            position: "right",
                            labels: {
                                boxWidth: 12,
                                fontSize: 11
                            }
                        },
                        tooltips: {
                            mode: "index",
                            intersect: false
                        },
                        scales: {
                            xAxes: [{
                                gridLines: { display: false },
                                ticks: {
                                    autoSkip: true,
                                    maxTicksLimit: 12,
                                    maxRotation: 45,
                                    minRotation: 0
                                }
                            }],
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0
                                }
                            }]
                        }
                    }
                });
            }
        };

        self.renderHeatmapChart = () => {
            var id = "chHeatmap";
            var el = (self.refs && self.refs[id]) || document.getElementById(id);
            if (!self.showHeatmapChart) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            var available = (self.categoriesWithTags && self.categoriesWithTags.length > 0) ? self.categoriesWithTags : self.availableCategories;
            var cat1 = self.heatmapCat1;
            var cat2 = self.heatmapCat2;
            if (!cat1 || !available.includes(cat1)) {
                cat1 = available[0] || null;
                self.heatmapCat1 = cat1;
            }
            if (!cat2 || !available.includes(cat2)) {
                cat2 = available[1] || available[0] || null;
                self.heatmapCat2 = cat2;
            }

            if (!cat1 || !cat2) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            var matrix = {};
            var rowCounts = {};
            var colCounts = {};

            self.filteredCompetitions.forEach(function (c) {
                var tags1 = (c.tagsByCategory && c.tagsByCategory[cat1]) || [];
                var tags2 = (c.tagsByCategory && c.tagsByCategory[cat2]) || [];
                if (tags1.length === 0 || tags2.length === 0) return;

                tags1.forEach(function (t1) {
                    rowCounts[t1] = (rowCounts[t1] || 0) + 1;
                    if (!matrix[t1]) matrix[t1] = {};
                    tags2.forEach(function (t2) {
                        colCounts[t2] = (colCounts[t2] || 0) + 1;
                        matrix[t1][t2] = (matrix[t1][t2] || 0) + 1;
                    });
                });
            });

            var rowOrder = Object.keys(rowCounts).sort(function (a, b) {
                return rowCounts[b] - rowCounts[a];
            }).slice(0, 18);

            var colOrder = Object.keys(colCounts).sort(function (a, b) {
                return colCounts[b] - colCounts[a];
            }).slice(0, 18);

            if (rowOrder.length === 0 || colOrder.length === 0) {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                    delete self.charts[id];
                }
                return;
            }

            var maxVal = 1;
            rowOrder.forEach(function (r) {
                colOrder.forEach(function (c) {
                    var v = (matrix[r] && matrix[r][c]) || 0;
                    if (v > maxVal) maxVal = v;
                });
            });

            var rowSums = {};
            rowOrder.forEach(function (r) {
                var s = 0;
                colOrder.forEach(function (c) {
                    s += (matrix[r] && matrix[r][c]) || 0;
                });
                rowSums[r] = s;
            });

            var desiredHeight = Math.max(380, rowOrder.length * 28 + 90);
            if (el.parentElement) {
                el.parentElement.style.height = desiredHeight + "px";
            }

            // Mouse hover tooltip on canvas
            el.onmousemove = function (evt) {
                var chart = self.charts[id];
                if (!chart || !chart.chartArea) return;
                var chartArea = chart.chartArea;
                var rect = el.getBoundingClientRect();
                var mouseX = evt.clientX - rect.left;
                var mouseY = evt.clientY - rect.top;

                if (mouseX >= chartArea.left && mouseX <= chartArea.right &&
                    mouseY >= chartArea.top && mouseY <= chartArea.bottom) {
                    var colW = (chartArea.right - chartArea.left) / colOrder.length;
                    var rowH = (chartArea.bottom - chartArea.top) / rowOrder.length;
                    var cIdx = Math.floor((mouseX - chartArea.left) / colW);
                    var rIdx = Math.floor((mouseY - chartArea.top) / rowH);

                    if (rIdx >= 0 && rIdx < rowOrder.length && cIdx >= 0 && cIdx < colOrder.length) {
                        var rTag = rowOrder[rIdx];
                        var cTag = colOrder[cIdx];
                        var val = (matrix[rTag] && matrix[rTag][cTag]) || 0;
                        var rSum = rowSums[rTag] || 0;
                        var pctStr = rSum > 0 ? ((val / rSum) * 100).toFixed(1) + "%" : "0%";
                        el.title = rTag + " × " + cTag + ": " + val + " (" + pctStr + ")";
                        return;
                    }
                }
                el.title = "";
            };

            var heatmapPlugin = {
                id: "heatmapCellRenderer",
                afterDraw: function (chart) {
                    var ctx = chart.ctx;
                    var chartArea = chart.chartArea;
                    if (!chartArea) return;

                    var numCols = colOrder.length;
                    var numRows = rowOrder.length;
                    if (numCols === 0 || numRows === 0) return;

                    var colWidth = (chartArea.right - chartArea.left) / numCols;
                    var rowHeight = (chartArea.bottom - chartArea.top) / numRows;

                    ctx.save();
                    ctx.beginPath();
                    ctx.rect(chartArea.left, chartArea.top, chartArea.right - chartArea.left, chartArea.bottom - chartArea.top);
                    ctx.clip();

                    for (var rIdx = 0; rIdx < numRows; rIdx++) {
                        var rTag = rowOrder[rIdx];
                        var rSum = rowSums[rTag] || 0;
                        var y = chartArea.top + rIdx * rowHeight;

                        for (var cIdx = 0; cIdx < numCols; cIdx++) {
                            var cTag = colOrder[cIdx];
                            var val = (matrix[rTag] && matrix[rTag][cTag]) || 0;
                            var x = chartArea.left + cIdx * colWidth;

                            var ratio = 0;
                            var text = "";
                            if (self.heatmapNormalize) {
                                var pct = rSum > 0 ? (val / rSum) * 100 : 0;
                                ratio = Math.min(1, pct / 100);
                                text = pct > 0 ? (pct >= 10 ? pct.toFixed(0) + "%" : pct.toFixed(1) + "%") : "0%";
                            } else {
                                ratio = Math.min(1, val / maxVal);
                                text = val.toString();
                            }

                            ctx.fillStyle = getBluesColor(ratio);
                            ctx.fillRect(x + 0.5, y + 0.5, colWidth - 1, rowHeight - 1);

                            ctx.strokeStyle = "#ffffff";
                            ctx.lineWidth = 1;
                            ctx.strokeRect(x + 0.5, y + 0.5, colWidth - 1, rowHeight - 1);

                            var fontSize = Math.min(11, Math.max(9, Math.floor(rowHeight * 0.4)));
                            ctx.font = (ratio > 0.4 ? "600 " : "400 ") + fontSize + 'px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                            ctx.fillStyle = ratio > 0.45 ? "#ffffff" : (val > 0 ? "#1e293b" : "#94a3b8");
                            ctx.textAlign = "center";
                            ctx.textBaseline = "middle";
                            ctx.fillText(text, x + colWidth / 2, y + rowHeight / 2);
                        }
                    }
                    ctx.restore();
                }
            };

            if (self.charts[id]) {
                self.charts[id].destroy();
            }

            self.charts[id] = new Chart(el, {
                type: "bubble",
                data: {
                    xLabels: colOrder,
                    yLabels: rowOrder,
                    datasets: [{ data: [] }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 0 },
                    legend: { display: false },
                    tooltips: { enabled: false },
                    layout: {
                        padding: { top: 10, right: 15, bottom: 10, left: 10 }
                    },
                    scales: {
                        xAxes: [{
                            type: "category",
                            labels: colOrder,
                            position: "bottom",
                            offset: true,
                            gridLines: { display: false, drawBorder: false },
                            ticks: {
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 35,
                                fontSize: 11,
                                fontColor: "#334155"
                            }
                        }],
                        yAxes: [{
                            type: "category",
                            labels: rowOrder,
                            position: "left",
                            offset: true,
                            gridLines: { display: false, drawBorder: false },
                            ticks: {
                                autoSkip: false,
                                fontSize: 11,
                                fontColor: "#334155"
                            }
                        }]
                    }
                },
                plugins: [heatmapPlugin]
            });
        };

        // Export currently filtered competitions to CSV
        self.downloadCSV = () => {
            var rows = self.filteredCompetitions;
            var esc = (v) => {
                var s = String(v == null ? '' : v);
                // Escape leading characters that could be interpreted as formulas in Excel
                if (/^[=+\-@\t\r]/.test(s)) {
                    s = "'" + s;
                }
                return '"' + s.replace(/"/g, '""') + '"';
            };
            var headers = ["id", "title", "organizer", "reward", "url"].concat(self.availableCategories).map(esc);
            var lines = [headers.join(",")];
            rows.forEach((c) => {
                var rowData = [
                    c.id,
                    esc(c.title),
                    esc(c.organizer),
                    esc(c.reward),
                    esc(c.url)
                ];
                self.availableCategories.forEach((cat) => {
                    rowData.push(esc((c.tagsByCategory[cat] || []).join("; ")));
                });
                lines.push(rowData.join(","));
            });
            var blob = new Blob(["\uFEFF" + lines.join("\r\n")], {
                type: "text/csv;charset=utf-8;"
            });
            var link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = "codabench_competitions_filtered.csv";
            link.click();
            URL.revokeObjectURL(link.href);
        };

        self.on('unmount', () => {
            Object.keys(self.charts).forEach((id) => {
                if (self.charts[id]) {
                    self.charts[id].destroy();
                }
            });
            self.charts = {};
        });
    </script>

    <style type="text/stylus">
        dashboard
            display block
            width 100%

        .dashboard-page-container
            max-width 1440px
            margin 0 auto
            padding 15px 20px 40px 20px

        .dashboard-header
            display flex
            justify-content space-between
            align-items center
            flex-wrap wrap
            gap 12px
            margin-bottom 20px
            padding-bottom 16px
            border-bottom 1px solid #e3e7ec

        .dashboard-title-group
            flex 1
            min-width 240px

        .dashboard-title
            margin 0
            font-size 24px
            font-weight bold
            color #1b1b1b
            display flex
            align-items center
            gap 10px

            i.icon
                color #43637a
                margin 0

        .dashboard-subtitle
            margin 4px 0 0 0
            font-family Roboto, sans-serif
            font-size 14px
            font-weight normal
            color #64748b
            line-height 1.4

        .dashboard-layout
            display flex
            align-items flex-start
            gap 20px
            width 100%

        .dashboard-sidebar
            width 270px
            flex-shrink 0

        .dashboard-main
            flex 1
            min-width 0

        @media (max-width 991px)
            .dashboard-layout
                flex-direction column

            .dashboard-sidebar
                width 100%

        .canvas-wrap
            position relative
            height 250px
            width 100%
    </style>
</dashboard>