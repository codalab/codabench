<sorting-chevrons>
    <span class="right floated">
        <i class="chevron down icon" show="{ opts.index + 1 < opts.data.length }"
            onclick="{ move_down.bind(this, opts.index) }"></i>
    </span>

    <span class="right floated">
        <i class="chevron up icon" show="{ opts.index > 0 }" onclick="{ move_up.bind(this, opts.index) }"></i>
    </span>

    <script>
        var self = this

        self.move_up = function(index) {
            self.move(index, -1)
        }

        self.move_down = function(index) {
            self.move(index, 1)
        }
        self.move = function(index, offset){
            var data_to_move = self.opts.data[index]

            // Remove the item
            self.opts.data.splice(index, 1)

            // Add 1 item offset up OR down
            self.opts.data.splice(index + offset, 0, data_to_move)

            self.parent.update()

            // Let form_updateds and such know we changed
            if(self.opts.onupdate) {
                self.opts.onupdate()
            }
        }
    </script>
</sorting-chevrons>
