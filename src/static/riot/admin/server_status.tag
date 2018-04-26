<server_status>
    <h1>Server Status</h1>
    <div class="ui horizontal divider"></div>
    <div class="ui relaxed three column stackable grid">
        <div class="four wide column">
            <div id="alert_box" class="ui segment">
                <i class="bell outline icon"></i><span class="ui tiny header">Jobs Currently Active</span>
                <h1 class="massive header">4</h1>
            </div>
        </div>
        <div id="server_status" class="four wide column">
            <div class="ui segment">
                <i class="server icon"></i><span class="ui tiny header">Server Idle Status</span>
                <div>
                    <canvas id="gauge_canvas"></canvas>
                </div>
            </div>
        </div>
        <div class="eight wide column">
            <div class="ui segment">
                <div class="ui small header">Last 10 Jobs Completed</div>
                <ol>
                    <li>Traffic Light Algorithm</li>
                    <li>Self-Checkout Button Placement</li>
                    <li>Dark Souls Speed Runner</li>
                    <li>Self-Driving Go-Kart</li>
                    <li>Video Encoder</li>
                    <li>Steins;Gate [ver. 2.74]</li>
                    <li>Advertisement Placement Algorithm</li>
                    <li>Military Drone Recon</li>
                    <li>Ad Click-Through Algorithm</li>
                    <li>Radio DJ Algorithm</li>
                </ol>
            </div>
        </div>
    </div>
    <div class="ui grid">
        <div class="column">
            <table class="ui celled table">
                <thead>
                <tr>
                    <th>CPU Usage</th>
                    <th>Disk Space</th>
                    <th>Memory Usage</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>32%</td>
                    <td>127 MB / 1250 MB</td>
                    <td>1.4 GB / 32.0 GB</td>
                </tr>
                </tbody>
            </table>
        </div>
    </div>
    <div id="external_monitors" class="ui two column centered grid">
        <div class="ui cards">
            <div class="ui card">
                <a class="image" href="#">
                    <img class="ui large image" src="/static/img/RabbitMQ.png">
                </a>
                <div class="content">
                    <a class="header" href="#">RabbitMQ</a>
                    <div class="meta">
                        <a href="#">
                            This page allows admins to view connections, queued messages, message rates, channels,
                            exchanges, and other administrative features relating to RabbitMQ e.g. Creating users,
                            adding v-hosts, and creating policies.
                        </a>
                    </div>
                </div>
            </div>
            <div class="ui card">
                <a class="image" href="#">
                    <img class="ui large image" src="/static/img/Flower.png">
                </a>
                <div class="content">
                    <a class="header" href="#">Flower</a>
                    <div class="meta">
                        <a href="#">
                            Flower is a powerful web-based Celery monitoring tool designed to keep track of our tasks.
                            Admins may view the state of which tasks were run, with what arguments, and many more
                            features. Here you may also view which queues your celery workers are consuming, and the
                            state of any tasks in them. At last, there is also a great monitoring page for viewing the
                            systemic impact of your workers.
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>


    <script>
        $(document).ready(function () {
            var opts = {
                angle: 0, // The span of the gauge arc
                lineWidth: 0.25, // The line thickness
                radiusScale: 1, // Relative radius
                pointer: {
                    length: 0.45, // Relative to gauge radius
                    strokeWidth: 0.035, // The thickness
                    color: '#000000'
                },
                limitMax: false,     // If false, max value increases automatically if value > maxValue
                limitMin: false,     // If true, the min value of the gauge will be fixed
                colorStart: '#1ecf2c',
                colorStop: '#da1111',
                strokeColor: '#E0E0E0',
                generateGradient: true,
                highDpiSupport: true,     // High resolution support
                staticZones: [
                    {strokeStyle: "#30B32D", min: 0, max: 5}, // Green
                    {strokeStyle: "#FFDD00", min: 5, max: 8}, // Yellow
                    {strokeStyle: "#F03E3E", min: 8, max: 10}  // Red
                ]
            };
            var target = document.getElementById('gauge_canvas'); // your canvas element
            var gauge = new Gauge(target).setOptions(opts); // create sexy gauge!
            gauge.maxValue = 10; // set max gauge value
            gauge.setMinValue(0);  // Prefer setter over gauge.minValue = 0
            gauge.animationSpeed = 32; // set animation speed (32 is default value)
            gauge.set(4); // set actual value
        })
    </script>


    <style type="text/stylus">
        server_status
            width 100%

        .ui.relaxed.three.column.stackable.grid
            margin 0 auto

        .ui.grid
            margin 0 auto

        #alert_box
            background-color #30B32D // Should change based on server-load
            color white
            text-align center

        #alert_box .ui.tiny.header
            color white

        #alert_box h1
            font-size 5em

        #server_status
            text-align center
            min-width 240px

        #server_status .ui.segment
            min-height 160px

        canvas
            text-align center
            max-width 170px

        @media only screen and (max-width 991px) and (min-width 768px)
            .ui.relaxed.three.column.stackable.grid
                flex-wrap nowrap

        #external_monitors.column .button
            margin-bottom 10px

        #external_monitors
            margin-top -0.5em

        div.ui.cards
            flex-wrap nowrap
            text-align justify

        div.ui.card
            width inherit !important
    </style>
</server_status>
