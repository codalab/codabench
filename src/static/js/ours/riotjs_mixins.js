var ProgressBarMixin = {
    show_progress_bar: function () {
        // The transition delays are for timing the animations, so they're one after the other
        this.refs.form.style.transitionDelay = '0s'
        this.refs.form.style.maxHeight = 0
        this.refs.form.style.overflow = 'hidden'

        this.refs.progress.style.transitionDelay = '.1s'
        this.refs.progress.style.height = '24px'
    },
    hide_progress_bar: function () {
        // The transition delays are for timing the animations, so they're one after the other
        this.refs.progress.style.transitionDelay = '0s'
        this.refs.progress.style.height = 0

        this.refs.form.style.transitionDelay = '.1s'
        this.refs.form.style.maxHeight = '1000px'

        // Need to keep track of self for setTimeout
        var self = this

        setTimeout(function () {
            // Do this after transition has been totally completed
            self.refs.form.style.overflow = 'visible'

            // Reset progress for the next displaying
            $(self.refs.progress).progress('reset')
        }, 1000)
    },
    file_upload_progress_handler: function (upload_progress) {
        if (this.upload_progress === undefined || upload_progress === undefined) {
            // the upload is just starting, show and reset everything
            this.show_progress_bar()
            upload_progress = 0
        }

        this.upload_progress = upload_progress;
        $(this.refs.progress).progress({percent: this.upload_progress})
        this.update()
    }
}