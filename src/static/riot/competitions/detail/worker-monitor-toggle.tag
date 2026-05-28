<worker-monitor-toggle>
    <button
        if="{ canViewWorkersPanel }"
        class="ui small button"
        onclick="{ toggleWorkersPanel }">
        { showWorkersPanel ? 'Hide workers' : 'Show workers' }
    </button>

    <aside
        if="{ canViewWorkersPanel && showWorkersPanel }"
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
                            Last update: { lastSyncLabel() }
                        </div>
                    </div>
                </div>
                <div class="workers-drag-hint">Drag to move</div>
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

            <div class="workers-section">
                <div class="workers-section-title">Default compute workers</div>

                <div class="workers-table-wrap">
                    <table class="ui very compact selectable striped table workers-table">
                        <thead>
                            <tr>
                                <th>Worker</th>
                                <th>Status</th>
                                <th>Jobs</th>
                                <th>Last seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ worker in sortedWorkers() }">
                                <td>
                                    <strong>{ worker.hostname }</strong>
                                </td>
                                <td>
                                    <span class="ui tiny label worker-status { getStatusClass(worker) }">
                                        <i class="{ getStatusIcon(worker) } icon"></i>
                                        { getStatusText(worker) }
                                    </span>
                                </td>
                                <td>{ worker.running_jobs || 0 }</td>
                                <td>{ formatLastSeen(worker.timestamp) }</td>
                            </tr>
                            <tr if="{ sortedWorkers().length === 0 }">
                                <td colspan="4" class="center aligned">
                                    <div class="workers-empty">
                                        <div class="header">No compute workers detected</div>
                                        <div class="description">Waiting for the first websocket snapshot.</div>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="workers-section" if="{ sortedPrivateWorkers().length }">
                <div class="workers-section-title">Private queues</div>

                <div class="workers-table-wrap">
                    <table class="ui very compact selectable striped table workers-table">
                        <thead>
                            <tr>
                                <th>Competition</th>
                                <th>Queue</th>
                                <th>Status</th>
                                <th>Jobs</th>
                                <th>Last seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ worker in sortedPrivateWorkers() }">
                                <td>
                                    <strong>{ worker.hostname || worker.competition_title || 'Private competition' }</strong>
                                </td>
                                <td>{ worker.queue_name || '—' }</td>
                                <td>
                                    <span class="ui tiny label worker-status { getStatusClass(worker) }">
                                        <i class="{ getStatusIcon(worker) } icon"></i>
                                        { getStatusText(worker) }
                                    </span>
                                </td>
                                <td>{ worker.running_jobs || 0 }</td>
                                <td>{ formatLastSeen(worker.timestamp) }</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="workers-footer">
                Green = available, yellow = busy, red = unavailable
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

        self.showWorkersPanel = false
        self.panelLeft = 24
        self.panelTop = 24
        self.panelWidth = 460

        self.draggingPanel = false
        self.dragOffsetX = 0
        self.dragOffsetY = 0

        self.toggleWorkersPanel = function () {
            self.showWorkersPanel = !self.showWorkersPanel
            if (self.showWorkersPanel) {
                self.loadPanelPosition()
                self.connect_workers_socket()
            } else {
                self.close_workers_socket()
            }

            self.update()
        }

        self.close_workers_socket = function () {
            if (self.wsReconnectTimer) {
                clearTimeout(self.wsReconnectTimer)
                self.wsReconnectTimer = null
            }

            if (self.ws) {
                try {
                    self.ws.close()
                } catch (e) {}
                self.ws = null
            }

            self.wsState = 'disconnected'
        }

        self.connect_workers_socket = function () {
            if (self.ws) {
                try {
                    self.ws.close()
                } catch (e) {}
                self.ws = null
            }
            var scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
            var url = scheme + '://' + window.location.host + '/ws/workers/'

            self.wsState = 'connecting'
            self.update()

            self.ws = new WebSocket(url)

            self.ws.onopen = function () {
                self.wsState = 'connected'
                var competitionId = parseInt(self.opts.competition_id) || null
                if (competitionId) {
                    self.ws.send(JSON.stringify({
                        type: 'subscribe',
                        competition_id: competitionId
                    }))
                }
                self.update()
            }

            self.ws.onmessage = function (event) {
                var message = null

                try {
                    message = JSON.parse(event.data)
                } catch (e) {
                    console.error('Invalid websocket payload:', event.data)
                    return
                }

                if (message.type === 'workers.snapshot') {
                    self.workers = message.workers || []
                    self.privateWorkers = message.private_workers || []
                    self.lastSyncAt = Date.now()
                    self.update()
                }
            }

            self.ws.onclose = function () {
                self.wsState = 'disconnected'
                self.update()
            }
        }

        self.startPanelDrag = function (e) {
            if (e.button !== 0) return

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

            var minLeft = 8
            var minTop = 8
            var maxLeft = Math.max(minLeft, window.innerWidth - self.panelWidth - 8)
            var maxTop = Math.max(minTop, window.innerHeight - 80)

            var newLeft = e.clientX - self.dragOffsetX
            var newTop = e.clientY - self.dragOffsetY

            self.panelLeft = Math.min(Math.max(minLeft, newLeft), maxLeft)
            self.panelTop = Math.min(Math.max(minTop, newTop), maxTop)

            self.update()
        }

        self.stopPanelDrag = function () {
            if (!self.draggingPanel) return

            self.draggingPanel = false
            document.body.classList.remove('workers-panel-dragging')

            window.removeEventListener('mousemove', self.onPanelDragMove)
            window.removeEventListener('mouseup', self.stopPanelDrag)
        }

        self.one('mount', function () {
            self.loadPanelPosition()
        })

        self.one('unmount', function () {
            window.removeEventListener('mousemove', self.onPanelDragMove)
            window.removeEventListener('mouseup', self.stopPanelDrag)
            self.close_workers_socket()
            document.body.classList.remove('workers-panel-dragging')
        })

        self.loadPanelPosition = function () {
            try {
                var raw = localStorage.getItem(self.panelStorageKey)
                if (!raw) return

                var pos = JSON.parse(raw)
                if (typeof pos.left === 'number') self.panelLeft = pos.left
                if (typeof pos.top === 'number') self.panelTop = pos.top

                self.clampPanelPosition()
            } catch (e) {
                console.warn('Could not load panel position', e)
            }
        }

        self.savePanelPosition = function () {
            try {
                localStorage.setItem(self.panelStorageKey, JSON.stringify({
                    left: self.panelLeft,
                    top: self.panelTop
                }))
            } catch (e) {
                console.warn('Could not save panel position', e)
            }
        }

        self.clampPanelPosition = function () {
            var minLeft = 8
            var minTop = 8
            var maxLeft = Math.max(minLeft, window.innerWidth - self.panelWidth - 8)
            var maxTop = Math.max(minTop, window.innerHeight - 80)

            self.panelLeft = Math.min(Math.max(minLeft, self.panelLeft), maxLeft)
            self.panelTop = Math.min(Math.max(minTop, self.panelTop), maxTop)
        }

        self.sortedWorkers = function () {
            var order = { available: 0, busy: 1, unavailable: 2 }

            return (self.workers || []).slice().sort(function (a, b) {
                var sa = self.displayStatus(a)
                var sb = self.displayStatus(b)

                var oa = order[sa] != null ? order[sa] : 99
                var ob = order[sb] != null ? order[sb] : 99

                if (oa !== ob) return oa - ob

                if ((b.running_jobs || 0) !== (a.running_jobs || 0)) {
                    return (b.running_jobs || 0) - (a.running_jobs || 0)
                }

                return (a.hostname || '').localeCompare(b.hostname || '')
            })
        }

        self.sortedPrivateWorkers = function () {
            var order = { available: 0, busy: 1, unavailable: 2 }

            return (self.privateWorkers || []).slice().sort(function (a, b) {
                var sa = self.displayStatus(a)
                var sb = self.displayStatus(b)

                var oa = order[sa] != null ? order[sa] : 99
                var ob = order[sb] != null ? order[sb] : 99

                if (oa !== ob) return oa - ob

                if ((b.running_jobs || 0) !== (a.running_jobs || 0)) {
                    return (b.running_jobs || 0) - (a.running_jobs || 0)
                }

                var an = a.competition_title || a.queue_name || a.hostname || ''
                var bn = b.competition_title || b.queue_name || b.hostname || ''
                return an.localeCompare(bn)
            })
        }

        self.displayStatus = function (worker) {
            return worker && worker.status ? worker.status : 'unavailable'
        }

        self.getStatusClass = function (worker) {
            if (self.displayStatus(worker) === 'available') return 'green'
            if (self.displayStatus(worker) === 'busy') return 'yellow'
            return 'red'
        }

        self.getStatusIcon = function (worker) {
            if (self.displayStatus(worker) === 'available') return 'check circle'
            if (self.displayStatus(worker) === 'busy') return 'clock'
            return 'times circle'
        }

        self.getStatusText = function (worker) {
            if (self.displayStatus(worker) === 'available') return 'Available'
            if (self.displayStatus(worker) === 'busy') return 'Busy'
            return 'Unavailable'
        }

        self.formatLastSeen = function (timestamp) {
            if (!timestamp) return '—'

            var age = Math.round((Date.now() / 1000) - timestamp)
            if (age < 5) return 'just now'
            if (age < 60) return age + 's ago'

            var minutes = Math.floor(age / 60)
            if (minutes < 60) return minutes + 'm ago'

            return Math.floor(minutes / 60) + 'h ago'
        }

        self.lastSyncLabel = function () {
            if (!self.lastSyncAt) return 'never'

            var age = Math.round((Date.now() - self.lastSyncAt) / 1000)
            if (age < 5) return 'just now'
            if (age < 60) return age + 's ago'

            var minutes = Math.floor(age / 60)
            return minutes + 'm ago'
        }

        self.totalCount = function () {
            return (self.workers || []).length
        }

        self.availableCount = function () {
            return (self.workers || []).filter(function (w) {
                return self.displayStatus(w) === 'available'
            }).length
        }

        self.busyCount = function () {
            return (self.workers || []).filter(function (w) {
                return self.displayStatus(w) === 'busy'
            }).length
        }

        self.unavailableCount = function () {
            return (self.workers || []).filter(function (w) {
                return self.displayStatus(w) === 'unavailable'
            }).length
        }

        self.connectionLabel = function () {
            if (self.wsState === 'connected') return 'Connected'
            if (self.wsState === 'connecting') return 'Connecting'
            if (self.wsState === 'error') return 'Error'
            return 'Disconnected'
        }

        self.panelStorageKey = 'codabench_workers_panel_position'

        window.addEventListener('resize', function () {
            if (!self.showWorkersPanel) return
            self.clampPanelPosition()
            self.update()
        })
    </script>

    <style type="text/stylus">
        .workers-panel
            position fixed
            z-index 25
            max-height calc(100vh - 48px)
            overflow auto

        .workers-card
            width 100%
            background #fff
            border 1px solid rgba(0,0,0,.1)
            border-radius 16px
            box-shadow 0 8px 24px rgba(0,0,0,.08)
            padding 14px

        .workers-header
            margin-bottom 12px

        .workers-drag-handle
            cursor move
            user-select none
            touch-action none

        .workers-title
            display flex
            align-items flex-start
            gap 10px

        .workers-title .icon
            margin-top 2px

        .workers-title-text
            font-size 18px
            font-weight 700
            color #1f2937
            line-height 1.2

        .workers-subtitle
            margin-top 4px
            font-size 12px
            color #6b7280
            display flex
            align-items center
            flex-wrap wrap
            gap 6px

        .workers-connection
            display inline-flex
            align-items center
            padding 3px 8px
            border-radius 999px
            font-weight 700
            font-size 11px
            text-transform uppercase
            letter-spacing .04em
            background #f3f4f6
            color #6b7280

        .workers-connection.connected
            background rgba(33, 186, 69, .12)
            color #21ba45

        .workers-connection.connecting
            background rgba(251, 189, 8, .14)
            color #b58105

        .workers-connection.error
            background rgba(219, 40, 40, .12)
            color #db2828

        .workers-connection.disconnected
            background rgba(219, 40, 40, .12)
            color #db2828

        .workers-separator
            opacity .6

        .workers-drag-hint
            margin-top 4px
            font-size 11px
            color #9ca3af
            white-space nowrap

        .workers-stats
            display grid
            grid-template-columns repeat(4, minmax(0, 1fr))
            gap 8px
            margin 10px 0 15px 0 !important

        .stat-card
            background #f9fafb
            border 1px solid rgba(0,0,0,.06)
            border-radius 12px
            padding 10px 8px
            text-align center
            display flex
            flex-direction column
            align-items center
            justify-content center

        .stat-value
            font-size 18px
            font-weight 800
            color #111827
            margin-bottom 4px
            min-width 1ch

        .stat-green
            color #21ba45

        .stat-yellow
            color #b58105

        .stat-red
            color #db2828

        .stat-label
            font-size 11px
            font-weight 700
            text-transform uppercase
            color #6b7280
            letter-spacing .04em

        .workers-section
            margin-top 16px

        .workers-section-title
            margin 12px 0 8px 0
            font-size 12px
            font-weight 700
            text-transform uppercase
            letter-spacing .04em
            color #6b7280

        .workers-table-wrap
            max-height calc(100vh - 240px)
            overflow auto
            border-radius 12px

        .workers-table
            margin 0 !important
            width 100%
            table-layout auto
            font-size 13px

        .workers-table thead th
            position sticky
            top 0
            background #f8fafc !important
            color #374151 !important
            font-weight 700 !important
            font-size 12px
            text-transform uppercase

        .workers-table td
        .workers-table th
            vertical-align middle !important

        .worker-status
            border-radius 999px !important
            font-weight 700 !important
            display inline-flex !important
            align-items center
            gap 6px
            white-space nowrap

        .workers-empty
            padding 24px 12px
            text-align center
            color #6b7280

        .workers-empty .header
            font-weight 700
            color #374151
            margin-bottom 4px

        .workers-footer
            margin-top 12px
            font-size 12px
            color #6b7280

        body.workers-panel-dragging
            user-select none

        @media (max-width: 1400px)
            .workers-panel
                width calc(100vw - 32px)
                max-width 520px

        @media (max-width: 768px)
            .workers-stats
                grid-template-columns repeat(2, minmax(0, 1fr))
    </style>
</worker-monitor-toggle>