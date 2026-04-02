<competition-detail>
    <div class="layout">
        <div class="comp-content">
            <comp-detail-header class="comp-detail-paragraph-text" competition="{ competition }"></comp-detail-header>
            <comp-detail-timeline class="comp-detail-phases" competition="{ competition }"></comp-detail-timeline>
            <comp-tabs class="comp-detail-paragraph-text" competition="{ competition }"></comp-tabs>
        </div>

        <button
            if="{ canViewWorkersPanel }"
            class="ui button primary workers-toggle-btn"
            onclick="{ toggleWorkersPanel }">
            <i class="server icon"></i>
            { showWorkersPanel ? 'Hide workers' : 'Show workers' }
        </button>

        <aside if="{ canViewWorkersPanel && showWorkersPanel }"
               class="workers-panel"
               style="left: { panelLeft }px; top: { panelTop }px;">
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

                <div class="workers-table-wrap">
                    <table class="ui very compact selectable striped table workers-table">
                        <thead>
                            <tr>
                                <th class="col-worker">Worker</th>
                                <th class="col-status">Status</th>
                                <th class="col-jobs">Jobs</th>
                                <th class="col-lastseen">Last seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr each="{ worker in sortedWorkers() }">
                                <td><strong>{ worker.hostname }</strong></td>
                                <td>
                                    <span class="ui tiny label worker-status { getStatusClass(worker) }">
                                        <i class="{ getStatusIcon(worker) } icon"></i>
                                        { getStatusText(worker) }
                            return        </span>
                                </td>
                                <td><span class="ui circular label">{ worker.running_jobs || 0 }</span></td>
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

                <div class="workers-footer">
                    Green = available, yellow = busy, red = unavailable
                </div>
            </div>
        </aside>
    </div>

    <script>
        var self = this;

        self.competition = {};
        self.workers = [];
        self.ws = null;
        self.wsReconnectTimer = null;
        self.wsState = 'disconnected';
        self.lastSyncAt = null;

        self.canViewWorkersPanel = (self.opts.can_view_workers_panel === 'true');
        self.showWorkersPanel = false

        self.canViewWorkersPanel = String(self.opts.can_view_workers_panel || 'false') === 'true'
        self.panelLeft = 24;
        self.panelTop = 24;
        self.panelWidth = 375;
        self.draggingPanel = false;
        self.dragOffsetX = 0;
        self.dragOffsetY = 0;
        self.panelStorageKey = 'codabench_workers_panel_position';
        self.resizeListenerAttached = false;

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

        self.one('mount', function () {
            $('.menu .item', self.root).tab();
            self.update_competition_data();
            if (self.canViewWorkersPanel) {
                self.loadPanelPosition();
                self.attachResizeListener();
            }
        });

        self.close_workers_socket = function () {
            if (self.wsReconnectTimer) {
                clearTimeout(self.wsReconnectTimer)
                self.wsReconnectTimer = null
            }

            if (self.ws) {
                self.ws.onclose = null

                try { self.ws.close() } catch (e) {}
                self.ws = null
            }

            self.wsState = 'disconnected'
        }

        self.one('unmount', function () {
            self.detachResizeListener();
            if (self.wsReconnectTimer) {
                clearTimeout(self.wsReconnectTimer);
                self.wsReconnectTimer = null;
            }
            if (self.ws) {
                try { self.ws.close(); } catch(e) {}
                self.ws = null;
            }
            document.body.classList.remove('workers-panel-dragging');
        });

        self.update_competition_data = function () {
            CODALAB.api.get_competition(self.opts.competition_pk, self.opts.secret_key)
                .done(function (data) {
                    self.competition = data;
                    CODALAB.events.trigger('competition_loaded', self.competition);

                    let currentPhase = _.find(self.competition.phases, { status: 'Current' });
                    let selectedPhaseId = currentPhase ? currentPhase.id : null;
                    if (selectedPhaseId === null) {
                        let finalPhase = _.find(self.competition.phases, { is_final_phase: true });
                        selectedPhaseId = finalPhase ? finalPhase.id : null;
                    }
                    CODALAB.events.trigger(
                        'phase.selected',
                        (_.find(self.competition.phases, { id: selectedPhaseId }))
                    );

                    self.update();
                })
                .fail(function () {
                    toastr.error("Could not find competition");
                });
        };

        self.attachResizeListener = function () {
            if (self.resizeListenerAttached) return;
            window.addEventListener('resize', self.onWindowResize);
            self.resizeListenerAttached = true;
        };

        self.detachResizeListener = function () {
            if (!self.resizeListenerAttached) return;
            window.removeEventListener('resize', self.onWindowResize);
            self.resizeListenerAttached = false;
        };

        self.loadPanelPosition = function () {
            try {
                var raw = localStorage.getItem(self.panelStorageKey);
                if (!raw) return;
                var pos = JSON.parse(raw);
                if (typeof pos.left === 'number') self.panelLeft = pos.left;
                if (typeof pos.top === 'number') self.panelTop = pos.top;
                self.clampPanelPosition();
            } catch (e) {
                console.warn('Could not load panel position', e);
            }
        };

        self.savePanelPosition = function () {
            try {
                localStorage.setItem(self.panelStorageKey, JSON.stringify({
                    left: self.panelLeft,
                    top: self.panelTop
                }));
            } catch (e) {
                console.warn('Could not save panel position', e);
            }
        };

        self.clampPanelPosition = function () {
            var minLeft = 8, minTop = 8;
            var maxLeft = Math.max(minLeft, window.innerWidth - self.panelWidth - 8);
            var maxTop = Math.max(minTop, window.innerHeight - 80);
            self.panelLeft = Math.min(Math.max(minLeft, self.panelLeft), maxLeft);
            self.panelTop = Math.min(Math.max(minTop, self.panelTop), maxTop);
        };

        self.onWindowResize = function () {
            self.clampPanelPosition();
            self.update();
        };

        self.startPanelDrag = function (e) {
            if (e.button !== 0) return;
            var panel = self.root.querySelector('.workers-panel');
            if (!panel) return;
            var rect = panel.getBoundingClientRect();
            self.draggingPanel = true;
            self.dragOffsetX = e.clientX - rect.left;
            self.dragOffsetY = e.clientY - rect.top;
            document.body.classList.add('workers-panel-dragging');
            window.addEventListener('mousemove', self.onPanelDragMove);
            window.addEventListener('mouseup', self.stopPanelDrag);
            e.preventDefault(); e.stopPropagation();
        };

        self.onPanelDragMove = function (e) {
            if (!self.draggingPanel) return;
            var minLeft = 8, minTop = 8;
            var maxLeft = Math.max(minLeft, window.innerWidth - self.panelWidth - 8);
            var maxTop = Math.max(minTop, window.innerHeight - 80);
            var newLeft = e.clientX - self.dragOffsetX;
            var newTop = e.clientY - self.dragOffsetY;
            self.panelLeft = Math.min(Math.max(minLeft, newLeft), maxLeft);
            self.panelTop = Math.min(Math.max(minTop, newTop), maxTop);
            self.update();
        };

        self.stopPanelDrag = function () {
            if (!self.draggingPanel) return;
            self.draggingPanel = false;
            document.body.classList.remove('workers-panel-dragging');
            window.removeEventListener('mousemove', self.onPanelDragMove);
            window.removeEventListener('mouseup', self.stopPanelDrag);
            self.savePanelPosition();
            self.update();
        };

        self.connect_workers_socket = function () {
            if (self.ws) {
                try { self.ws.close(); } catch (e) {}
                self.ws = null;
            }
            var scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
            var url = scheme + '://' + window.location.host + '/ws/workers/';
            self.wsState = 'connecting';
            self.update();
            self.ws = new WebSocket(url);

            self.ws.onopen = function () {
                self.wsState = 'connected';
                self.update();
            };
            self.ws.onmessage = function (event) {
                try {
                    var message = JSON.parse(event.data);
                    if (message.type === 'workers.snapshot') {
                        self.workers = message.workers || [];
                        self.lastSyncAt = Date.now();
                        self.update();
                    }
                    if (message.type === 'worker.health' && message.worker) {
                        self.upsertWorker(message.worker);
                        self.lastSyncAt = Date.now();
                        self.update();
                    }
                } catch (e) {
                    console.error('Invalid websocket payload:', e);
                }
            };

            self.ws.onerror = function () {
                self.wsState = 'error'
                self.update()
            }

            self.ws.onclose = function () {
                self.wsState = 'disconnected'
                self.update()

                if (!self.showWorkersPanel) return

                if (self.wsReconnectTimer) {
                    clearTimeout(self.wsReconnectTimer)
                }

                self.wsReconnectTimer = setTimeout(function () {
                    self.connect_workers_socket()
                }, 2000)
            }
        };

        self.normalizeWorker = function (worker) {
            worker = worker || {};
            return {
                hostname: worker.hostname || 'unknown',
                status: worker.status || 'unavailable',
                running_jobs: typeof worker.running_jobs === 'number' ? worker.running_jobs : 0,
                timestamp: worker.timestamp || null
            };
        };

        self.normalizeWorkers = function (workers) {
            return (workers || [])
                .filter(function (w) { return w && w.hostname; })
                .map(self.normalizeWorker);
        };

        self.upsertWorker = function (worker) {
            worker = self.normalizeWorker(worker);
            if (!worker.hostname || worker.hostname === 'unknown') return;
            var idx = _.findIndex(self.workers, { hostname: worker.hostname });
            if (idx === -1) {
                self.workers.push(worker);
            } else {
                self.workers[idx] = worker;
            }
            self.workers = self.workers.slice();
        };

        self.sortedWorkers = function () {
            var order = { available: 0, busy: 1, unavailable: 2 };
            return (self.workers || []).slice().sort(function (a, b) {
                var sa = self.displayStatus(a), sb = self.displayStatus(b);
                var oa = order[sa] || 99, ob = order[sb] || 99;
                if (oa !== ob) return oa - ob;
                if ((b.running_jobs || 0) !== (a.running_jobs || 0)) {
                    return (b.running_jobs || 0) - (a.running_jobs || 0);
                }
                return (a.hostname || '').localeCompare(b.hostname || '');
            });
        };

        self.displayStatus = function (worker) {
            return worker && worker.status ? worker.status : 'unavailable';
        };
        self.getStatusClass = function (worker) {
            var status = self.displayStatus(worker);
            if (status === 'available') return 'green';
            if (status === 'busy') return 'yellow';
            return 'red';
        };
        self.getStatusIcon = function (worker) {
            var status = self.displayStatus(worker);
            if (status === 'available') return 'check circle';
            if (status === 'busy') return 'clock';
            return 'times circle';
        };
        self.getStatusText = function (worker) {
            var status = self.displayStatus(worker);
            if (status === 'available') return 'Available';
            if (status === 'busy') return 'Busy';
            return 'Unavailable';
        };

        self.formatLastSeen = function (timestamp) {
            if (!timestamp) return '—';
            var age = Math.round((Date.now()/1000) - timestamp);
            if (age < 5) return 'just now';
            if (age < 60) return age + 's ago';
            var minutes = Math.floor(age/60);
            if (minutes < 60) return minutes + 'm ago';
            return Math.floor(minutes/60) + 'h ago';
        };

        self.lastSyncLabel = function () {
            if (!self.lastSyncAt) return 'never';
            var age = Math.round((Date.now() - self.lastSyncAt)/1000);
            if (age < 5) return 'just now';
            if (age < 60) return age + 's ago';
            var minutes = Math.floor(age/60);
            return minutes + 'm ago';
        };

        self.totalCount = function () { return (self.workers || []).length; };
        self.availableCount = function () {
            return (self.workers || []).filter(w => self.displayStatus(w) === 'available').length;
        };
        self.busyCount = function () {
            return (self.workers || []).filter(w => self.displayStatus(w) === 'busy').length;
        };
        self.unavailableCount = function () {
            return (self.workers || []).filter(w => self.displayStatus(w) === 'unavailable').length;
        };
        self.connectionLabel = function () {
            if (self.wsState === 'connected') return 'Connected';
            if (self.wsState === 'connecting') return 'Connecting';
            if (self.wsState === 'error') return 'Error';
            return 'Disconnected';
        };

        CODALAB.events.on('new_submission_created', function () {
            self.update_competition_data();
        });
    </script>

    <style type="text/stylus">
        .comp-detail-paragraph-text {
            font-size: 16px !important;
            line-height: 20px !important;
        }
        :scope { display: block; width: 100%; height: 100%; }
        .layout { position: relative; display: block; }
        .comp-content { min-width: 0; padding-right: 0; }

        .workers-panel {
            position: fixed;
            top: 24px;
            right: 24px;
            width: 375px;
            z-index: 25;
            background: #fff;
            overflow: auto;
            max-height: calc(100vh - 48px);
        }

        .workers-card {
            background: #fff;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
            padding: 12px;
        }
        .workers-header { margin-bottom: 12px; }
        .workers-title { display: flex; align-items: flex-start; gap: 10px; }
        .workers-title .icon { margin-top: 2px; }
        .workers-title-text { font-size: 18px; font-weight: 700; color: #1f2937; line-height: 1.2; }
        .workers-subtitle {
            margin-top: 4px;
            font-size: 12px;
            color: #6b7280;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .workers-toggle-btn
            z-index 0
            position fixed
            top 74px
            right 24px
            background #576671 !important
            color white !important
            
        .workers-connection {
            display: inline-flex;
            align-items: center;
            padding: 3px 8px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            background: #f3f4f6;
            color: #6b7280;
        }
        .workers-connection.connected {
            background: rgba(33,186,69,.12);
            color: #21ba45;
        }
        .workers-connection.connecting {
            background: rgba(251,189,8,.14);
            color: #b58105;
        }
        .workers-connection.error {
            background: rgba(219,40,40,.12);
            color: #db2828;
        }
        .workers-connection.disconnected {
            background: rgba(219,40,40,.12);
            color: #db2828;
        }
        .workers-separator { opacity: .6; }
        .workers-drag-hint { margin-top: 4px; font-size: 11px; color: #9ca3af; white-space: nowrap; }

        .workers-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin: 10px 0 15px 0 !important;
        }
        .stat-card {
            background: #f9fafb;
            border: 1px solid rgba(0,0,0,0.06);
            border-radius: 12px;
            padding: 10px 8px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .stat-value {
            font-size: 18px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 4px;
            min-width: 1ch;
        }
        .stat-green { color: #21ba45; }
        .stat-yellow { color: #b58105; }
        .stat-red { color: #db2828; }
        .stat-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: #6b7280;
            letter-spacing: .04em;
        }

        .workers-table-wrap {
            max-height: calc(100vh - 240px);
            overflow: auto;
            border-radius: 12px;
        }
        .workers-table {
            margin: 0 !important;
            width: 100%;
            table-layout: auto;
            font-size: 13px;
        }
        .workers-table thead th {
            position: sticky;
            top: 0;
            background: #f8fafc !important;
            color: #374151 !important;
            font-weight: 700 !important;
            font-size: 12px;
            text-transform: uppercase;
        }
        .workers-table td, .workers-table th {
            vertical-align: middle !important;
        }
        .worker-hostname {
            font-size: 13px;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .worker-jobs {
            text-align: center;
        }
        .worker-lastseen {
            color: #6b7280;
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .worker-status {
            border-radius: 999px !important;
            font-weight: 700 !important;
            display: inline-flex !important;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
        }
        .workers-empty {
            padding: 24px 12px;
            text-align: center;
            color: #6b7280;
        }
        .workers-empty .header {
            font-weight: 700;
            color: #374151;
            margin-bottom: 4px;
        }
        .workers-footer {
            margin-top: 12px;
            font-size: 12px;
            color: #6b7280;
        }
        .ui.label.green {
            background-color: #21ba45 !important;
            color: white !important;
        }
        .ui.label.yellow {
            background-color: #f2c037 !important;
            color: black !important;
        }
        .ui.label.red {
            background-color: #db2828 !important;
            color: white !important;
        }
        body.workers-panel-dragging {
            user-select: none;
        }

        @media (max-width: 1400px) {
            .workers-panel {
                position: static;
                width: 100%;
                max-height: none;
                margin-top: 16px;
            }
            .workers-table-wrap {
                max-height: none;
            }
        }
        @media (max-width: 768px) {
            .workers-stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</competition-detail>
