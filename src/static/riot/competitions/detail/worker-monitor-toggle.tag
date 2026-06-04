<worker-monitor-toggle>
    <button
        if="{ canViewWorkersPanel && !inlineMode && !allWorkers }"
        class="ui small button workers-toggle-btn"
        onclick="{ toggleWorkersPanel }">
        <i class="server icon"></i>
        { showWorkersPanel ? 'Hide workers' : 'Show workers' }
    </button>

    <!-- ── Inline mode (Monitor queue panel) ──────────────────────────────────── -->
    <div if="{ canViewWorkersPanel && inlineMode }" class="workers-inline">
        <div class="workers-card">
            <div class="workers-header">
                <div class="workers-title">
                    <i class="server icon"></i>
                    <div class="workers-title-text">
                        Compute Workers
                        <div class="workers-subtitle">
                            <span class="workers-connection { wsState }">{ connectionLabel() }</span>
                            <span class="workers-separator">•</span>
                            <span>Last update: { lastSyncLabel() }</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="workers-stats">
                <div class="stat-card">
                    <div class="stat-value">{ totalCount() }</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-green">{ availableCount() }</div>
                    <div class="stat-label">Available</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-yellow">{ busyCount() }</div>
                    <div class="stat-label">Busy</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-red">{ unavailableCount() }</div>
                    <div class="stat-label">Down</div>
                </div>
            </div>

            <!-- Public workers -->
            <div class="workers-section">
                <div class="workers-section-header">
                    <div class="workers-section-title">
                        Public compute workers
                        <span class="workers-count">{ sortedWorkers().length }</span>
                    </div>
                    <button type="button" class="workers-collapse-btn" onclick="{ togglePublicWorkers }">
                        <i class="{ publicWorkersCollapsed ? 'chevron down' : 'chevron up' } icon"></i>
                        { publicWorkersCollapsed ? 'Expand' : 'Collapse' }
                    </button>
                </div>
                <div if="{ !publicWorkersCollapsed }" class="workers-table-wrap">
                    <table class="workers-table">
                        <colgroup>
                            <col class="col-worker">
                            <col class="col-status">
                            <col class="col-jobs">
                            <col class="col-lastseen">
                        </colgroup>
                        <thead>
                            <tr>
                                <th>Worker</th>
                                <th>Status</th>
                                <th class="cell-center">Jobs</th>
                                <th>Last seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ worker in sortedWorkers() }">
                                <td class="cell-worker"><span class="worker-hostname">{ worker.hostname || '—' }</span></td>
                                <td>
                                    <span class="worker-status-badge { getStatusClass(worker) }">
                                        <i class="{ getStatusIcon(worker) } icon"></i>
                                        { getStatusText(worker) }
                                    </span>
                                </td>
                                <td class="cell-center cell-jobs">{ worker.running_jobs || 0 }</td>
                                <td class="cell-muted cell-nowrap">{ formatLastSeen(worker.last_seen) }</td>
                            </tr>
                            <tr if="{ sortedWorkers().length === 0 }">
                                <td colspan="4"><div class="workers-empty">No public compute workers detected</div></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div if="{ publicWorkersCollapsed }" class="workers-collapsed">
                    { sortedWorkers().length } worker(s) hidden
                </div>
            </div>

            <!-- Private workers -->
            <div class="workers-section">
                <div class="workers-section-header">
                    <div class="workers-section-title">
                        Private compute workers
                        <span class="workers-count">{ sortedPrivateWorkers().length }</span>
                    </div>
                </div>
                <div class="workers-table-wrap">
                    <table class="workers-table">
                        <colgroup>
                            <col class="col-worker">
                            <col class="col-queue">
                            <col class="col-status">
                            <col class="col-jobs">
                            <col class="col-lastseen">
                        </colgroup>
                        <thead>
                            <tr>
                                <th>Worker</th>
                                <th>Queue</th>
                                <th>Status</th>
                                <th class="cell-center">Jobs</th>
                                <th>Last seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ worker in sortedPrivateWorkers() }">
                                <td class="cell-worker"><span class="worker-hostname">{ worker.hostname || '—' }</span></td>
                                <td class="cell-queue cell-muted">{ worker.queue_source || '—' }</td>
                                <td>
                                    <span class="worker-status-badge { getStatusClass(worker) }">
                                        <i class="{ getStatusIcon(worker) } icon"></i>
                                        { getStatusText(worker) }
                                    </span>
                                </td>
                                <td class="cell-center cell-jobs">{ worker.running_jobs || 0 }</td>
                                <td class="cell-muted cell-nowrap">{ formatLastSeen(worker.last_seen) }</td>
                            </tr>
                            <tr if="{ sortedPrivateWorkers().length === 0 }">
                                <td colspan="5"><div class="workers-empty">No private compute workers detected</div></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- ── Floating panel mode (competition header) ───────────────────── -->
    <aside
        if="{ canViewWorkersPanel && !inlineMode && showWorkersPanel }"
        class="workers-panel"
        style="left: { panelLeft }px; top: { panelTop }px; width: { panelWidth }px;">
        <div class="workers-card">
            <div class="workers-header workers-drag-handle" onmousedown="{ startPanelDrag }">
                <div class="workers-title">
                    <i class="server icon"></i>
                    <div class="workers-title-text">
                        Compute Workers
                        <div class="workers-subtitle">
                            <span class="workers-connection { wsState }">{ connectionLabel() }</span>
                            <span class="workers-separator">•</span>
                            <span>Last update: { lastSyncLabel() }</span>
                        </div>
                    </div>
                </div>
                <div class="workers-drag-hint">
                    <i class="arrows alternate icon"></i> Drag
                </div>
            </div>

            <div class="workers-stats">
                <div class="stat-card">
                    <div class="stat-value">{ totalCount() }</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-green">{ availableCount() }</div>
                    <div class="stat-label">Available</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-yellow">{ busyCount() }</div>
                    <div class="stat-label">Busy</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value stat-red">{ unavailableCount() }</div>
                    <div class="stat-label">Down</div>
                </div>
            </div>

            <!-- Public workers -->
            <div class="workers-section">
                <div class="workers-section-header">
                    <div class="workers-section-title">
                        Public
                        <span class="workers-count">{ sortedWorkers().length }</span>
                    </div>
                    <button type="button" class="workers-collapse-btn" onclick="{ togglePublicWorkers }">
                        <i class="{ publicWorkersCollapsed ? 'chevron down' : 'chevron up' } icon"></i>
                        { publicWorkersCollapsed ? 'Expand' : 'Collapse' }
                    </button>
                </div>
                <div if="{ !publicWorkersCollapsed }" class="workers-table-wrap">
                    <table class="workers-table">
                        <colgroup>
                            <col class="col-worker">
                            <col class="col-status">
                            <col class="col-jobs">
                            <col class="col-lastseen">
                        </colgroup>
                        <thead>
                            <tr>
                                <th>Worker</th>
                                <th>Status</th>
                                <th class="cell-center">Jobs</th>
                                <th>Last seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ worker in sortedWorkers() }">
                                <td class="cell-worker"><span class="worker-hostname">{ worker.hostname || '—' }</span></td>
                                <td>
                                    <span class="worker-status-badge { getStatusClass(worker) }">
                                        <i class="{ getStatusIcon(worker) } icon"></i>
                                        { getStatusText(worker) }
                                    </span>
                                </td>
                                <td class="cell-center cell-jobs">{ worker.running_jobs || 0 }</td>
                                <td class="cell-muted cell-nowrap">{ formatLastSeen(worker.last_seen) }</td>
                            </tr>
                            <tr if="{ sortedWorkers().length === 0 }">
                                <td colspan="4"><div class="workers-empty">No public compute workers detected</div></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div if="{ publicWorkersCollapsed }" class="workers-collapsed">
                    { sortedWorkers().length } worker(s) hidden
                </div>
            </div>

            <!-- Private workers -->
            <div class="workers-section" if="{ sortedPrivateWorkers().length || allWorkers }">
                <div class="workers-section-header">
                    <div class="workers-section-title">
                        Private
                        <span class="workers-count">{ sortedPrivateWorkers().length }</span>
                    </div>
                </div>
                <div class="workers-table-wrap">
                    <table class="workers-table">
                        <colgroup>
                            <col class="col-worker">
                            <col class="col-queue">
                            <col class="col-status">
                            <col class="col-jobs">
                            <col class="col-lastseen">
                        </colgroup>
                        <thead>
                            <tr>
                                <th>Worker</th>
                                <th>Queue</th>
                                <th>Status</th>
                                <th class="cell-center">Jobs</th>
                                <th>Last seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ worker in sortedPrivateWorkers() }">
                                <td class="cell-worker"><span class="worker-hostname">{ worker.hostname || '—' }</span></td>
                                <td class="cell-queue cell-muted">{ worker.queue_source || '—' }</td>
                                <td>
                                    <span class="worker-status-badge { getStatusClass(worker) }">
                                        <i class="{ getStatusIcon(worker) } icon"></i>
                                        { getStatusText(worker) }
                                    </span>
                                </td>
                                <td class="cell-center cell-jobs">{ worker.running_jobs || 0 }</td>
                                <td class="cell-muted cell-nowrap">{ formatLastSeen(worker.last_seen) }</td>
                            </tr>
                            <tr if="{ sortedPrivateWorkers().length === 0 }">
                                <td colspan="5"><div class="workers-empty">No private compute workers detected</div></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </aside>

    <script>
        var self = this
        self.workers = []
        self.privateWorkers = []
        self.ws = null
        self.wsReconnectTimer = null
        self.wsState = 'disconnected'
        self.lastSyncAt = null
        self.canViewWorkersPanel =
            String(self.opts.can_view_workers_panel || 'false') === 'true'
        self.allWorkers = String(self.opts.all_workers || 'false') === 'true'
        self.inlineMode = String(self.opts.inline_mode || 'false') === 'true'
        self.showWorkersPanel = self.inlineMode || self.allWorkers
        self.panelLeft = 24
        self.panelTop = 24
        self.panelWidth = 480
        self.panelStorageKey = 'codabench_workers_panel_position'
        self.draggingPanel = false
        self.dragOffsetX = 0
        self.dragOffsetY = 0
        self.publicWorkersCollapsed = false
        self.shouldKeepSocketOpen = function () {
            return self.inlineMode || self.showWorkersPanel || self.allWorkers
        }
        self.togglePublicWorkers = function (e) {
            if (e) { e.preventDefault(); e.stopPropagation() }
            self.publicWorkersCollapsed = !self.publicWorkersCollapsed
            self.update()
        }
        self.toggleWorkersPanel = function () {
            if (self.inlineMode) return
            self.showWorkersPanel = !self.showWorkersPanel
            if (self.showWorkersPanel) {
                self.loadPanelPosition()
                self.connect_workers_socket()
            } else {
                self.close_workers_socket(false)
            }
            self.update()
        }
        self.close_workers_socket = function (allowReconnect) {
            if (self.wsReconnectTimer) { clearTimeout(self.wsReconnectTimer); self.wsReconnectTimer = null }
            if (self.ws) {
                try { self.ws.onopen = null; self.ws.onmessage = null; self.ws.onerror = null; self.ws.onclose = null; self.ws.close() } catch (e) {}
                self.ws = null
            }
            self.wsState = 'disconnected'
            if (allowReconnect && self.shouldKeepSocketOpen()) self.scheduleReconnect()
        }
        self.scheduleReconnect = function () {
            if (self.wsReconnectTimer) return
            self.wsReconnectTimer = setTimeout(function () {
                self.wsReconnectTimer = null
                if (!self.shouldKeepSocketOpen()) return
                self.connect_workers_socket()
            }, 3000)
        }
        self.connect_workers_socket = function () {
            if (!self.canViewWorkersPanel) return
            if (self.ws) { try { self.ws.close() } catch (e) {}; self.ws = null }
            var scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
            var url = scheme + '://' + window.location.host + '/ws/workers/'
            self.wsState = 'connecting'
            self.update()
            try { self.ws = new WebSocket(url) } catch (e) { self.wsState = 'error'; self.update(); self.scheduleReconnect(); return }
            self.ws.onopen = function () {
                self.wsState = 'connected'
                var payload = { type: 'subscribe' }
                if (self.allWorkers || self.inlineMode) {
                    payload.all_workers = true
                } else {
                    var competitionId = parseInt(self.opts.competition_id) || null
                    if (competitionId) payload.competition_id = competitionId
                    else payload.all_workers = true
                }
                try { self.ws.send(JSON.stringify(payload)) } catch (e) { console.error('Unable to send subscribe', e) }
                self.update()
            }
            self.ws.onmessage = function (event) {
                var message = null
                try { message = JSON.parse(event.data) } catch (e) { console.error('Invalid WS payload:', event.data); return }
                if (message.type === 'workers.snapshot') {
                    self.workers = message.workers || []
                    self.privateWorkers = message.private_workers || []
                    self.lastSyncAt = Date.now()
                    self.update()
                }
            }
            self.ws.onerror = function () { self.wsState = 'error'; self.update() }
            self.ws.onclose = function () { self.wsState = 'disconnected'; self.update(); self.scheduleReconnect() }
        }
        self.startPanelDrag = function (e) {
            if (self.inlineMode || e.button !== 0) return
            var panel = self.root.querySelector('.workers-panel')
            if (!panel) return
            var rect = panel.getBoundingClientRect()
            self.draggingPanel = true
            self.dragOffsetX = e.clientX - rect.left
            self.dragOffsetY = e.clientY - rect.top
            document.body.classList.add('workers-panel-dragging')
            window.addEventListener('mousemove', self.onPanelDragMove)
            window.addEventListener('mouseup', self.stopPanelDrag)
            e.preventDefault()
        }
        self.onPanelDragMove = function (e) {
            if (!self.draggingPanel) return
            var minLeft = 8, minTop = 8
            var maxLeft = Math.max(minLeft, window.innerWidth - self.panelWidth - 8)
            var maxTop = Math.max(minTop, window.innerHeight - 80)
            self.panelLeft = Math.min(Math.max(minLeft, e.clientX - self.dragOffsetX), maxLeft)
            self.panelTop  = Math.min(Math.max(minTop,  e.clientY - self.dragOffsetY), maxTop)
            self.update()
        }
        self.stopPanelDrag = function () {
            if (!self.draggingPanel) return
            self.draggingPanel = false
            document.body.classList.remove('workers-panel-dragging')
            window.removeEventListener('mousemove', self.onPanelDragMove)
            window.removeEventListener('mouseup', self.stopPanelDrag)
            self.savePanelPosition()
        }
        self.loadPanelPosition = function () {
            if (self.inlineMode) return
            try {
                var raw = localStorage.getItem(self.panelStorageKey)
                if (!raw) return
                var pos = JSON.parse(raw)
                if (typeof pos.left === 'number') self.panelLeft = pos.left
                if (typeof pos.top  === 'number') self.panelTop  = pos.top
                self.clampPanelPosition()
            } catch (e) {}
        }
        self.savePanelPosition = function () {
            if (self.inlineMode) return
            try { localStorage.setItem(self.panelStorageKey, JSON.stringify({ left: self.panelLeft, top: self.panelTop })) } catch (e) {}
        }
        self.clampPanelPosition = function () {
            if (self.inlineMode) return
            var minLeft = 8, minTop = 8
            var maxLeft = Math.max(minLeft, window.innerWidth - self.panelWidth - 8)
            var maxTop  = Math.max(minTop,  window.innerHeight - 80)
            self.panelLeft = Math.min(Math.max(minLeft, self.panelLeft), maxLeft)
            self.panelTop  = Math.min(Math.max(minTop,  self.panelTop),  maxTop)
        }
        self.displayStatus = function (w) { return w && w.status ? w.status : 'unavailable' }
        self.getStatusClass = function (w) {
            var s = self.displayStatus(w)
            if (s === 'available') return 'green'
            if (s === 'busy') return 'yellow'
            return 'red'
        }
        self.getStatusIcon = function (w) {
            var s = self.displayStatus(w)
            if (s === 'available') return 'check circle'
            if (s === 'busy') return 'clock'
            return 'times circle'
        }
        self.getStatusText = function (w) {
            var s = self.displayStatus(w)
            if (s === 'available') return 'Available'
            if (s === 'busy') return 'Busy'
            return 'Unavailable'
        }
        self.formatLastSeen = function (timestamp) {
            if (!timestamp) return '—'
            var age = Math.round((Date.now() / 1000) - timestamp)
            if (age < 5)  return 'just now'
            if (age < 60) return age + 's ago'
            var m = Math.floor(age / 60)
            if (m < 60)   return m + 'm ago'
            return Math.floor(m / 60) + 'h ago'
        }
        self.lastSyncLabel = function () {
            if (!self.lastSyncAt) return 'never'
            var age = Math.round((Date.now() - self.lastSyncAt) / 1000)
            if (age < 5)  return 'just now'
            if (age < 60) return age + 's ago'
            return Math.floor(age / 60) + 'm ago'
        }
        self.allDisplayedWorkers = function () { return (self.workers || []).concat(self.privateWorkers || []) }
        var _sortWorkers = function (list) {
            var order = { available: 0, busy: 1, unavailable: 2 }
            return list.slice().sort(function (a, b) {
                var oa = order[self.displayStatus(a)] != null ? order[self.displayStatus(a)] : 99
                var ob = order[self.displayStatus(b)] != null ? order[self.displayStatus(b)] : 99
                if (oa !== ob) return oa - ob
                if ((b.running_jobs || 0) !== (a.running_jobs || 0)) return (b.running_jobs || 0) - (a.running_jobs || 0)
                return (a.hostname || '').localeCompare(b.hostname || '')
            })
        }
        self.sortedWorkers        = function () { return _sortWorkers(self.workers || []) }
        self.sortedPrivateWorkers = function () { return _sortWorkers(self.privateWorkers || []) }
        self.totalCount     = function () { return self.allDisplayedWorkers().length }
        self.availableCount = function () { return self.allDisplayedWorkers().filter(function (w) { return self.displayStatus(w) === 'available'   }).length }
        self.busyCount      = function () { return self.allDisplayedWorkers().filter(function (w) { return self.displayStatus(w) === 'busy'        }).length }
        self.unavailableCount = function () { return self.allDisplayedWorkers().filter(function (w) { return self.displayStatus(w) === 'unavailable' }).length }
        self.connectionLabel = function () {
            if (self.wsState === 'connected')   return 'Connected'
            if (self.wsState === 'connecting')  return 'Connecting…'
            if (self.wsState === 'error')       return 'Error'
            return 'Disconnected'
        }
        self.onWindowResize = function () {
            if (self.inlineMode || !self.showWorkersPanel) return
            self.clampPanelPosition(); self.update()
        }
        self.one('mount', function () {
            if (!self.inlineMode) self.loadPanelPosition()
            if (self.shouldKeepSocketOpen()) self.connect_workers_socket()
            window.addEventListener('resize', self.onWindowResize)
        })
        self.one('unmount', function () {
            window.removeEventListener('mousemove', self.onPanelDragMove)
            window.removeEventListener('mouseup', self.stopPanelDrag)
            window.removeEventListener('resize', self.onWindowResize)
            self.close_workers_socket(false)
            document.body.classList.remove('workers-panel-dragging')
        })
    </script>

    <style type="text/stylus">

        $green = #21ba45
        $yellow = #b58105
        $red = #db2828
        $border = rgba(0,0,0,.08)
        $text = #1f2937
        $muted = #6b7280
        $subtle = #9ca3af
        $bg = #fff
        $bg-alt = #f8fafc
        $bg-stat = #f9fafb

        .workers-panel
            position fixed
            z-index 25
            max-height calc(100vh - 48px)
            overflow-y auto
            overflow-x hidden

        .workers-inline
            position relative
            width 100%

        .workers-card
            background $bg
            border 1px solid $border
            border-radius 14px
            box-shadow 0 4px 20px rgba(0,0,0,.07)
            padding 16px

        .workers-inline .workers-card
            box-shadow none
            border-radius 12px

        .workers-header
            display flex
            align-items center
            justify-content space-between
            margin-bottom 14px

        .workers-drag-handle
            cursor grab
            user-select none
            touch-action none
            &:active
                cursor grabbing

        .workers-title
            display flex
            align-items center
            gap 10px
            flex 1
            min-width 0

        .workers-title > .icon
            font-size 16px
            color $muted
            flex-shrink 0

        .workers-title-text
            font-size 15px
            font-weight 700
            color $text
            line-height 1.2
            min-width 0

        .workers-subtitle
            margin-top 3px
            font-size 11px
            color $muted
            display flex
            align-items center
            flex-wrap wrap
            gap 5px

        .workers-drag-hint
            flex-shrink 0
            display flex
            align-items center
            gap 4px
            font-size 11px
            color $subtle
            padding 4px 8px
            border-radius 6px
            background $bg-alt
            border 1px solid $border

        .workers-connection
            display inline-flex
            align-items center
            padding 2px 7px
            border-radius 999px
            font-weight 700
            font-size 10px
            text-transform uppercase
            letter-spacing .05em
            background #f3f4f6
            color $muted

        .workers-connection.connected
            background rgba(33,186,69,.12)
            color $green

        .workers-connection.connecting
            background rgba(251,189,8,.14)
            color $yellow

        .workers-connection.error,
        .workers-connection.disconnected
            background rgba(219,40,40,.10)
            color $red

        .workers-separator
            opacity .5

        .workers-stats
            display grid
            grid-template-columns repeat(4, 1fr)
            gap 8px
            margin 0 0 14px 0

        .stat-card
            background $bg-stat
            border 1px solid $border
            border-radius 10px
            padding 10px 8px
            text-align center

        .stat-value
            font-size 20px
            font-weight 800
            color $text
            line-height 1
            margin-bottom 4px

        .stat-green  { color $green }
        .stat-yellow { color $yellow }
        .stat-red    { color $red }

        .stat-label
            font-size 10px
            font-weight 700
            text-transform uppercase
            color $muted
            letter-spacing .05em

        .workers-section
            margin-top 14px

        .workers-section + .workers-section
            border-top 1px solid $border
            padding-top 14px

        .workers-section-header
            display flex
            align-items center
            justify-content space-between
            gap 10px
            margin-bottom 8px

        .workers-section-title
            font-size 11px
            font-weight 700
            text-transform uppercase
            letter-spacing .06em
            color $muted
            display flex
            align-items center
            gap 6px

        .workers-count
            display inline-flex
            align-items center
            justify-content center
            min-width 20px
            height 18px
            padding 0 5px
            border-radius 999px
            background rgba(0,0,0,.06)
            color $muted
            font-size 10px
            font-weight 700

        .workers-collapse-btn
            flex-shrink 0
            display inline-flex
            align-items center
            gap 4px
            padding 3px 10px
            border-radius 6px
            border 1px solid $border
            background $bg-alt
            color $muted
            font-size 11px
            font-weight 600
            cursor pointer
            line-height 1.6
            transition background .15s
            &:hover
                background #f0f2f5
                color $text

        .workers-collapse-btn .icon
            margin 0 !important
            font-size 10px !important

        .workers-collapsed
            padding 10px 12px
            text-align center
            color $subtle
            font-size 12px
            border 1px dashed rgba(0,0,0,.1)
            border-radius 8px
            background $bg-alt

        .workers-table-wrap
            border 1px solid $border
            border-radius 10px
            overflow hidden

        .workers-table
            width 100%
            table-layout fixed
            border-collapse collapse
            font-size 12.5px

        .workers-table .col-worker
            width auto

        .workers-table .col-queue
            width 130px

        .workers-table .col-status
            width 108px

        .workers-table .col-jobs
            width 56px

        .workers-table .col-lastseen
            width 88px

        .workers-table thead tr
            background $bg-alt
            border-bottom 1px solid $border

        .workers-table thead th
            padding 7px 10px
            font-size 10.5px
            font-weight 700
            text-transform uppercase
            letter-spacing .05em
            color $muted
            white-space nowrap
            overflow hidden
            text-overflow ellipsis
            text-align left

        .workers-table tbody tr
            border-bottom 1px solid rgba(0,0,0,.04)
            transition background .1s

        .workers-table tbody tr:last-child
            border-bottom none

        .workers-table tbody tr:hover
            background rgba(0,0,0,.02)

        .workers-table td
            padding 8px 10px
            vertical-align middle
            overflow hidden
            text-overflow ellipsis
            white-space nowrap

        .cell-worker
            font-weight 600
            color $text

        .worker-hostname
            font-family 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace
            font-size 11.5px
            display block
            overflow hidden
            text-overflow ellipsis
            white-space nowrap

        .cell-queue
            font-size 12px

        .cell-muted
            color $muted

        .cell-nowrap
            white-space nowrap

        .cell-center
            text-align center

        .cell-jobs
            font-weight 700
            font-size 13px
            color $text

        .worker-status-badge
            display inline-flex
            align-items center
            justify-content center
            gap 4px
            width 96px
            padding 7px 0
            border-radius 999px
            font-size 11px
            font-weight 700
            white-space nowrap
            line-height 1

        .worker-status-badge .icon
            margin 0 !important
            font-size 11px !important  
            line-height 1 !important
            vertical-align middle !important

        .worker-status-badge.green
            background rgba(33,186,69,.10)
            color darken($green, 10%)

        .worker-status-badge.yellow
            background rgba(251,189,8,.14)
            color darken($yellow, 5%)

        .worker-status-badge.red
            background rgba(219,40,40,.10)
            color darken($red, 5%)

        .workers-empty
            padding 18px
            text-align center
            color $subtle
            font-size 12px

        .workers-footer
            margin-top 12px
            padding-top 10px
            border-top 1px solid $border
            display flex
            align-items center
            gap 10px
            font-size 11px
            color $muted

        .footer-dot
            display inline-block
            width 8px
            height 8px
            border-radius 50%
            flex-shrink 0

        .footer-dot.green  { background $green }
        .footer-dot.yellow { background $yellow }
        .footer-dot.red    { background $red }

        body.workers-panel-dragging
            user-select none
            cursor grabbing !important

        @media (max-width: 1400px)
            .workers-panel
                width calc(100vw - 32px)
                max-width 520px

        @media (max-width: 768px)
            .workers-stats
                grid-template-columns repeat(2, 1fr)

            .workers-section-header
                flex-direction column
                align-items flex-start

            .workers-collapse-btn
                width 100%
                justify-content center

            .workers-table .col-queue
            .workers-table .col-lastseen
                width 80px

    </style>
</worker-monitor-toggle>