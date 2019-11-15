/* ----------------------------------------------------------------------------
 Progress bar mixin

 This shows a progress bar intended to be used with out client API functions like
 `create_dataset`. To use this class, you should add the mixin to your RiotJS
 component, have your form submit event call `prepare_upload(your_form_submit_function)`,
 */

var ProgressBarMixin = {
    show_progress_bar: function () {
        // The transition delays are for timing the animations, so they're one after the other
        if (!!this.refs.form) {
            this.refs.form.style.transitionDelay = '0s'
            this.refs.form.style.maxHeight = 0
            this.refs.form.style.overflow = 'hidden'
        }
        if (!!this.refs.progress) {
            this.refs.progress.style.transitionDelay = '.1s'
            this.refs.progress.style.height = '24px'
        }
    },
    hide_progress_bar: function () {
        // The transition delays are for timing the animations, so they're one after the other
        if (!!this.refs.progress) {
            this.refs.progress.style.transitionDelay = '0s'
            this.refs.progress.style.height = 0
        }
        if (!!this.refs.form) {
            this.refs.form.style.transitionDelay = '.1s'
            this.refs.form.style.maxHeight = '1000px'
        }
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
            upload_progress = 0
        }

        this.upload_progress = upload_progress;
        $(this.refs.progress).progress({percent: this.upload_progress})
        this.update()
    },
    prepare_upload: function(upload_callback) {
        // Need to keep track of self inside this wrapped function
        var self = this

        return function(event) {
            // This function shows the progress bar then a short time later begins the actual upload
            if (event) {
                event.preventDefault()
            }

            // the upload is just starting, show and reset everything
            self.file_upload_progress_handler(undefined)
            self.show_progress_bar()

            setTimeout(upload_callback, 500)
        }
    }
}