<queue-form>
    <div class="header">
        Queue Form
    </div>
    <div class="content">
        <form class="ui form" ref="form">
            <div class="ui active tab" data-tab="details">
                <div class="required field">
                    <label>Name</label>
                    <input name="name" placeholder="Name" ref="name" value="{ _.get(queue, 'name', '') }"
                           onkeyup="{ form_updated }">
                </div>
                <div class="required field">
                    <div class="ui checkbox">
                        <label>Is Public?</label>
                        <input type="checkbox" ref="public">
                    </div>
                </div>
                <div class="field">
                    <collaborators-component></collaborators-component>
                </div>
            </div>
        </form>
    </div>
    <div class="actions">
        <div class="ui primary button" onclick="{ handle_queue }">Submit</div>
        <div class="ui basic red cancel button" onclick="{ cancel }">Cancel</div>
    </div>
    <script>
        var self = this

        self.queue = {}
        self.collabs = []

        self.one('mount', function() {
            $(".ui.checkbox", self.root).checkbox()
            if (self.opts.queue_id !== null && self.opts.queue_id !== undefined && self.opts.queue_id !== '') {
                self.set_queue(self.opts.queue_id)
            }
        })

        self.set_queue = function(queue_id) {
            CODALAB.api.get_queue(queue_id)
                .done((data) => {
                    self.queue = data
                    self.update()
                    self.collabs = _.values(_.mapValues(self.queue.organizers , function(organizer) { return organizer.id }))
                    if (self.queue.is_public) {
                        self.refs.public.checked = true
                    }
                    CODALAB.events.trigger('collaborators_load', {
                        'organizers': self.queue.organizers,
                        'creator': self.queue.creator
                    })
                })
                .fail((response) => {
                    toastr.error('Error retrieving Queue')
                })
        }

        self.cancel = function() {
            window.location = '/queues/'
        }

        self.handle_queue = function() {
            var data = {
                name: self.refs.name.value,
                is_public: self.refs.public.checked,
                organizers: self.collabs,
            }
            var endpoint
            if (self.opts.queue_id !== null && self.opts.queue_id !== undefined && self.opts.queue_id !== '') {
                endpoint = CODALAB.api.update_queue(self.opts.queue_id, data)
            } else {
                endpoint = CODALAB.api.create_queue(data)
            }
            endpoint
                .done(function (response) {
                    window.location = '/queues/'
                })
                .fail(function (response) {
                    toastr.error("Could not update/create queue!")
                })
        }

        // Todo: Is this the best way to go about this?
        CODALAB.events.on('collaborators_changed', function (collabs) {
            var tempList = _.values(_.mapValues(collabs , function(collab) { return collab.id }))
            self.collabs = tempList
        })
    </script>
    <style>
        .actions {
            margin-top: 15px !important;
        }
    </style>
</queue-form>