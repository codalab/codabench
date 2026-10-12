<dashboard>
    <div class="ui container fluid dashboard-container" style="max-width: 1400px; padding: 0 20px;">
        <div class="ui stackable grid">
            <div class="sixteen wide column">
                <h2 class="ui header">
                    <i class="chart pie icon"></i>
                    <div class="content">
                        Competitions Dashboard
                        <div class="sub header">Analyze trends, organizers, and domains across Codabench</div>
                    </div>
                </h2>
            </div>
        </div>

        <div class="ui divider"></div>

        <div class="ui active inverted dimmer" if="{ loading }">
            <div class="ui large text loader">Fetching data...</div>
        </div>

        <div class="ui stackable grid" show="{ !loading }">
            <div class="four wide column">
                <competition-filter-panel show_visibility="{ isAdmin }" show_counts="{ true }" categories="{ categoryFilters }" onfilterchange="{ handleFilterChange }"></competition-filter-panel>
            </div>

            <div class="twelve wide column">
                <dashboard-charts p="{ this }"></dashboard-charts>


                <dashboard-table p="{ this }"></dashboard-table>
            </div>
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

        self.kpis = {
            distinctOrganizers: 0,
            participants: 0,
            submissions: 0
        };

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

            fetchPage(apiUrl);
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
                        var cat = tag.category || "Other";
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

            // Re-bind charts, using refs array for dynamically rendered canvas elements
            self.availableCategories.forEach((cat, idx) => {
                self.state.selectedTags[cat] = {};
                self.chartCards.push({
                    catName: cat,
                    id: "chart_cat_" + idx
                });
            });

            self.kpis.categoriesPresent = self.availableCategories.length;

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
                    var matchTitle = c.title.toLowerCase().indexOf(s) !== -1;
                    var matchOrg = c.organizer.toLowerCase().indexOf(s) !== -1;
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

                tagsArr.sort((a, b) => {
                    if (a.checked !== b.checked) return a.checked ? -1 : 1;
                    if (b.count !== a.count) return b.count - a.count;
                    return a.name.localeCompare(b.name);
                });
                var noTagsChecked = (self.state.selectedTags[cat] && self.state.selectedTags[cat]['_no_tags_']) ? true : false;

                self.categoryFilters.push({
                    name: cat,
                    tags: tagsArr,
                    noTagsCount: self.noTagsCounts[cat] || 0,
                    noTagsChecked: noTagsChecked
                });
            });

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

            var oPairs = countOrgs(rows, 10);
            self.renderHorizontalBar("chOrgs", oPairs, "#21ba45");

            var cPairs = rows.map((c) => {
                var shortTitle = c.title.length > 25 ? c.title.substring(0, 25) + '...' : c.title;
                return [shortTitle, c.participants_count || 0];
            });
            cPairs.sort((a, b) => {
                return b[1] - a[1];
            });
            cPairs = cPairs.slice(0, 10);
            self.renderHorizontalBar("chComps", cPairs, "#fbbd08");

            // Re-bind charts, using refs array for dynamically rendered canvas elements
            self.availableCategories.forEach((cat, idx) => {
                var counts = self.categoryTagsCounts[cat] || {};
                var pairs = Object.keys(counts).map((k) => {
                    return [k, counts[k]];
                });
                pairs.sort((a, b) => {
                    return b[1] - a[1];
                });
                pairs = pairs.slice(0, 15);

                var canvasId = "chart_cat_" + idx;

                var el = document.getElementById(canvasId);
                if (!el && self.refs.dynamicCharts) {
                    if (Array.isArray(self.refs.dynamicCharts)) {
                        el = self.refs.dynamicCharts[idx];
                    } else if (idx === 0) {
                        el = self.refs.dynamicCharts;
                    }
                }
                var color = PALETTE[idx % PALETTE.length];

                if (el) {
                    if (idx % 3 === 0) {
                        self.renderHorizontalBarId(canvasId, pairs, color, el);
                    } else if (idx % 3 === 1) {
                        self.renderDoughnutId(canvasId, pairs, el);
                    } else {
                        self.renderVerticalBarId(canvasId, pairs, color, el);
                    }
                }
            });
        };

        self.renderHorizontalBar = (refName, pairs, color) => {
            var el = self.refs[refName];
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
                                fontSize: 11
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

        // Export currently filtered competitions to CSV
        self.downloadCSV = () => {
            var rows = self.filteredCompetitions;
            var esc = (v) => {
                return '"' + String(v || '').replace(/"/g, '""') + '"';
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
    </script>

    <style type="text/stylus" scoped>
        .kpi-stats
            display flex !important
            justify-content space-around !important
            flex-wrap wrap !important
            margin-bottom 1.2rem !important

        .chart-card
            padding 12px 14px !important

        .table-card
            padding 14px !important
            margin-top 16px !important

        .table-top-bar
            display flex
            justify-content space-between
            align-items center
            margin-bottom 12px

        .table-scroll-wrap
            max-height 480px
            overflow-y auto

        .pagination-footer
            display flex
            justify-content center
            margin-top 12px
        .dashboard-container
            margin-top 15px
            margin-bottom 40px

        .canvas-wrap
            position relative
            height 250px
            width 100%
    </style>
</dashboard>